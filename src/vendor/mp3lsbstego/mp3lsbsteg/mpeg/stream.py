# mp3lsbsteg/mpeg/stream.py
from dataclasses import dataclass
from typing import List, Tuple
import struct as _st

from .header import parse_header
from .sideinfo import parse_sideinfo, sideinfo_bytes

# ---------- ID3v2 helpers ----------
def _synchsafe_to_int(b: bytes) -> int:
    return ((b[0] & 0x7F) << 21) | ((b[1] & 0x7F) << 14) | ((b[2] & 0x7F) << 7) | (b[3] & 0x7F)

def skip_id3v2(data: bytes) -> int:
    if len(data) < 10 or data[0:3] != b"ID3":
        return 0
    flags = data[5]
    size = _synchsafe_to_int(data[6:10])
    return 10 + size + (10 if (flags & 0x10) else 0)

# ---------- Header peek ----------
def _parse_header_basic(b: bytes):
    if len(b) < 4:
        return None
    b1, b2, b3, b4 = _st.unpack(">BBBB", b)
    if b1 != 0xFF or (b2 & 0xE0) != 0xE0:
        return None
    version_id = (b2 >> 3) & 0x03   # 00=2.5,10=2,11=1
    layer_id   = (b2 >> 1) & 0x03
    has_crc    = ((b2 & 0x01) == 0)
    ch_mode    = (b4 >> 6) & 0x03
    if version_id == 1 or layer_id == 0:
        return None
    channels = 1 if ch_mode == 3 else 2
    return {"version_id": version_id, "channels": channels, "has_crc": has_crc}

# ---------- VBR header detection ----------
def looks_like_vbr_header(data: bytes, frame_off: int, frame_len: int) -> bool:
    hb = _parse_header_basic(data[frame_off:frame_off+4])
    if not hb:
        return False
    off = frame_off + 4 + (2 if hb["has_crc"] else 0) + sideinfo_bytes(hb["version_id"], hb["channels"])
    window = data[off : min(frame_off + frame_len, off + 128)]
    return (b"Xing" in window) or (b"Info" in window) or (b"VBRI" in window)

# ---------- Simple frame iterator (offset, size) ----------
def iter_frames(data: bytes) -> List[Tuple[int, int]]:
    """
    Return a list of (offset, size) tuples for audio frames.
    Skips ID3v2 at the start and drops a VBR header frame if present,
    so results align with ffprobe's audio packet list.
    """
    frames: List[Tuple[int, int]] = []
    i = skip_id3v2(data)
    n = len(data)
    while i + 4 <= n:
        info = parse_header(data[i:i+4])
        if info:
            size = info["frame_length"]
            if size <= 4 or i + size > n:
                i += 1
                continue
            frames.append((i, size))
            i += size
        else:
            i += 1

    # Drop the leading VBR header frame for parity with ffprobe
    if frames and looks_like_vbr_header(data, frames[0][0], frames[0][1]):
        frames = frames[1:]

    return frames

# ---------- Per-granule main_data windows (read-only analysis) ----------
@dataclass
class FrameWindows:
    offset: int
    size: int
    version_id: int
    channels: int
    has_crc: bool
    windows: List[List[Tuple[int, int]]]  # [granule][ch] -> (abs_bit_start, abs_bit_end)
    available_main_bits: int              # main_data bits this frame contributes to reservoir

def iter_frames_with_windows(blob: bytes):
    """
    Yield FrameWindows for each audio frame:
      - frame offset/size
      - version/channels/has_crc
      - per-(granule,channel) absolute bit windows for main_data
      - available_main_bits (contribution to reservoir)
    """
    # Start from same list as iter_frames but we need the raw, un-skipped list first
    frames: List[Tuple[int, int]] = []
    i = skip_id3v2(blob)
    n = len(blob)
    while i + 4 <= n:
        info = parse_header(blob[i:i+4])
        if info:
            size = info["frame_length"]
            if size <= 4 or i + size > n:
                i += 1
                continue
            frames.append((i, size))
            i += size
        else:
            i += 1

    # Skip VBR header for audio mapping
    if frames and looks_like_vbr_header(blob, frames[0][0], frames[0][1]):
        frames = frames[1:]

    reservoir_end = 0  # absolute bit index

    for (off, size) in frames:
        hb = _parse_header_basic(blob[off:off+4])
        if not hb:
            continue
        version_id, channels, has_crc = hb["version_id"], hb["channels"], hb["has_crc"]

        si = parse_sideinfo(blob, off, version_id, channels, has_crc)

        header_bits = 32
        crc_bits = 16 if has_crc else 0
        sideinfo_bits = si.sideinfo_bits
        available_main_bits = size * 8 - header_bits - crc_bits - sideinfo_bits
        if available_main_bits < 0:
            continue

        ngr = 2 if version_id == 3 else 1
        windows: List[List[Tuple[int, int]]] = [[(0, 0) for _ in range(channels)] for _ in range(ngr)]

        read_ptr = reservoir_end - (si.main_data_begin * 8)
        for g in range(ngr):
            for ch in range(channels):
                L = si.granules[g][ch].part2_3_length
                start = read_ptr
                end = start + L
                windows[g][ch] = (start, end)
                read_ptr = end

        reservoir_end += available_main_bits

        yield FrameWindows(
            offset=off,
            size=size,
            version_id=version_id,
            channels=channels,
            has_crc=has_crc,
            windows=windows,
            available_main_bits=available_main_bits,
        )
