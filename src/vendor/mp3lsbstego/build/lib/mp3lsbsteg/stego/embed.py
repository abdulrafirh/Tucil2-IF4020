# mp3lsbsteg/stego/embed.py
from __future__ import annotations
from typing import Iterable, List, Tuple, Optional, Dict
import bisect
import hashlib

from mp3lsbsteg.io.bitreader import BitReader
from mp3lsbsteg.io.bitwriter import BitWriter
from mp3lsbsteg.mpeg.stream import iter_frames_with_windows, _parse_header_basic
from mp3lsbsteg.mpeg.sideinfo import parse_sideinfo, sideinfo_bytes
from mp3lsbsteg.mpeg.header import parse_header
from mp3lsbsteg.mpeg.part3 import (
    extract_signbits_for_window,
    extract_signbits_count1_fixed,
)
from mp3lsbsteg.mpeg import tables as T
from mp3lsbsteg.stego.payload import wrap_payload, try_parse_header, HEADER_SIZE, vigenere_xor

# -------------------- tiny utils --------------------

def _bytes_to_bits(data: bytes) -> Iterable[int]:
    for b in data:
        for k in (7, 6, 5, 4, 3, 2, 1, 0):
            yield (b >> k) & 1

def _bits_to_bytes(bits: Iterable[int]) -> bytes:
    out = bytearray()
    acc = 0
    n = 0
    for bit in bits:
        acc = (acc << 1) | (bit & 1)
        n += 1
        if n == 8:
            out.append(acc)
            acc = 0
            n = 0
    if n:
        out.append(acc << (8 - n))
    return bytes(out)

def _pos_score(key: Optional[str], frame_index: int, fpos: int) -> int:
    """
    Deterministic per-position score for ordering with a key.
    Lower score = earlier pick. Independent of list order and platform.
    """
    if not key:
        # when no key, keep natural order by returning fpos
        return fpos
    h = hashlib.sha256()
    h.update(b"mp3lsbsteg/pos-rank/v1")
    h.update(key.encode("utf-8"))
    h.update(frame_index.to_bytes(8, "big", signed=False))
    h.update(fpos.to_bytes(8, "big", signed=False))
    return int.from_bytes(h.digest()[:8], "big", signed=False)

def _part2_bits(version_id: int, gr: int, ch: int, si) -> int:
    """MPEG-1 part2 (scalefactor) bits. Extend if you add MPEG-2/2.5 later."""
    mpeg1 = (version_id == 3)
    gch = si.granules[gr][ch]
    if not mpeg1:
        return 0
    slen1, slen2 = T.slen[int(gch.scalefac_compress)]
    if gch.window_switching_flag and gch.block_type == 2:
        if gch.mixed_block_flag:
            return 8 * slen1 + 3 * 3 * slen1 + 3 * 6 * slen2
        else:
            return 3 * 6 * slen1 + 3 * 6 * slen2
    if gr == 0:
        return 11 * slen1 + 10 * slen2
    scfsi_ch = list(si.scfsi[ch])
    total = 0
    total += 0 if scfsi_ch[0] else (6 * slen1)
    total += 0 if scfsi_ch[1] else (5 * slen1)
    total += 0 if scfsi_ch[2] else (5 * slen2)
    total += 0 if scfsi_ch[3] else (5 * slen2)
    return total

# ---------------- reservoir <-> file mapping ----------------

class _Seg:
    __slots__ = ("res_start", "res_end", "file_start_bit")
    def __init__(self, res_start: int, res_end: int, file_start_bit: int):
        self.res_start = res_start
        self.res_end = res_end
        self.file_start_bit = file_start_bit

def _build_reservoir_map(blob: bytes) -> Tuple[List[_Seg], List[int]]:
    segs: List[_Seg] = []
    res_cursor = 0
    for fw in iter_frames_with_windows(blob):
        hb = _parse_header_basic(blob[fw.offset:fw.offset + 4])
        header_bits = 32
        crc_bits = 16 if hb["has_crc"] else 0
        si_bits = sideinfo_bytes(hb["version_id"], hb["channels"]) * 8
        avail = fw.available_main_bits
        if avail <= 0:
            continue
        file_main_start_bit = (fw.offset * 8) + header_bits + crc_bits + si_bits
        segs.append(_Seg(res_cursor, res_cursor + avail, file_main_start_bit))
        res_cursor += avail
    breakpoints = [s.res_start for s in segs]
    return segs, breakpoints

def _res_to_file_bit(R: int, segs: List[_Seg], breaks: List[int]) -> Optional[int]:
    i = bisect.bisect_right(breaks, R) - 1
    if i < 0 or i >= len(segs):
        return None
    s = segs[i]
    if not (s.res_start <= R < s.res_end):
        return None
    return s.file_start_bit + (R - s.res_start)

# -------- sign-bit positions for a frame (reservoir coords) --------

def _frame_sign_positions_reservoir(blob: bytes, fw) -> List[int]:
    """All sign bits (reservoir coordinates), aggregated across granules/channels."""
    hb = _parse_header_basic(blob[fw.offset:fw.offset + 4])
    if hb["has_crc"]:
        return []
    si = parse_sideinfo(blob, fw.offset, hb["version_id"], hb["channels"], hb["has_crc"])
    fs_hz = parse_header(blob[fw.offset:fw.offset + 4])["samplerate"]

    out: List[int] = []
    ngr = 2 if hb["version_id"] == 3 else 1
    for g in range(ngr):
        for ch in range(hb["channels"]):
            win_start, win_end = fw.windows[g][ch]
            if win_end <= win_start:
                continue
            p2 = _part2_bits(hb["version_id"], g, ch, si)
            p3_start = win_start + p2
            p3_len = max(0, win_end - p3_start)
            if p3_len <= 0:
                continue
            gch = si.granules[g][ch]
            s = extract_signbits_for_window(
                blob=blob,
                start_bit=p3_start,
                length_bits=p3_len,
                fs_hz=fs_hz,
                table_select=[
                    int(gch.table_select[0]),
                    int(gch.table_select[1]),
                    int(gch.table_select[2]),
                ],
                region0_count=int(gch.region0_count),
                region1_count=int(gch.region1_count),
                big_value=int(gch.big_values),
                count1table_select=int(gch.count1table_select),
            )
            out.extend(s)
    return out

def _frame_sign_positions_reservoir_c1fixed(blob: bytes, fw) -> List[int]:
    """Only count1-fixed sign bits (reservoir coordinates); safest for audibility & stability."""
    hb = _parse_header_basic(blob[fw.offset:fw.offset + 4])
    if hb["has_crc"]:
        return []
    si = parse_sideinfo(blob, fw.offset, hb["version_id"], hb["channels"], hb["has_crc"])
    fs_hz = parse_header(blob[fw.offset:fw.offset + 4])["samplerate"]

    out: List[int] = []
    ngr = 2 if hb["version_id"] == 3 else 1
    for g in range(ngr):
        for ch in range(hb["channels"]):
            win_start, win_end = fw.windows[g][ch]
            if win_end <= win_start:
                continue
            p2 = _part2_bits(hb["version_id"], g, ch, si)
            p3_start = win_start + p2
            p3_len = max(0, win_end - p3_start)
            if p3_len <= 0:
                continue
            gch = si.granules[g][ch]
            c1 = extract_signbits_count1_fixed(
                blob=blob,
                start_bit=p3_start,
                length_bits=p3_len,
                fs_hz=fs_hz,
                count1table_select=int(gch.count1table_select),
            )
            out.extend(c1)
    return out

# -------- masking helpers --------

def _frame_avg_global_gain(blob: bytes, fw) -> float:
    """Average global_gain across granules and channels for this frame."""
    hb = _parse_header_basic(blob[fw.offset:fw.offset + 4])
    si = parse_sideinfo(blob, fw.offset, hb["version_id"], hb["channels"], hb["has_crc"])
    vals = []
    ngr = 2 if hb["version_id"] == 3 else 1
    for g in range(ngr):
        for ch in range(hb["channels"]):
            vals.append(int(si.granules[g][ch].global_gain))
    return float(sum(vals)) / max(1, len(vals))

def _compute_min_gain_threshold(blob: bytes, percentile: Optional[float]) -> Optional[float]:
    """
    Return the global_gain threshold at the given percentile (0..1), or None to disable masking.
    """
    if percentile is None:
        return None
    vals = []
    for fw in iter_frames_with_windows(blob):
        vals.append(_frame_avg_global_gain(blob, fw))
    if not vals:
        return None
    vals.sort()
    p = 0.0 if percentile < 0 else (1.0 if percentile > 1 else percentile)
    idx = int(p * (len(vals) - 1))
    return float(vals[idx])

# -------- unified selector (current-frame only, inner margins, masking, keyed ranking) --------

def _deterministic_positions_in_window(
    start_bit: int,
    end_bit: int,
    key: Optional[str],
    frame_index: int,
    max_take: Optional[int],
) -> List[int]:
    """
    Content-independent carrier positions inside [start_bit, end_bit).
    Uses a per-(frame,key) PRF to pick a starting offset and stride; then walks forward.
    """
    if end_bit <= start_bit:
        return []
    span = end_bit - start_bit

    # PRF = SHA256(frame_index || key)
    h = hashlib.sha256()
    h.update(frame_index.to_bytes(4, "big"))
    if key:
        h.update(key.encode("utf-8"))
    seed = h.digest()

    # derive stride in [17..41] (odd to avoid trivial cycles), and offset in [0..stride-1]
    stride = 17 + (seed[0] % 25)
    if (stride % 2) == 0:
        stride += 1
    offset = seed[1] % stride

    out: List[int] = []
    # walk positions; stop at max_take if provided
    p = start_bit + offset
    while p < end_bit:
        out.append(p)
        if max_take is not None and len(out) >= max_take:
            break
        p += stride
    return out

def _select_positions_for_frame(
    blob: bytes,
    fw,
    segs: List[_Seg],
    breaks: List[int],
    fraction: float,
    bits_per_frame: Optional[int],
    key: Optional[str],
    frame_index: int,
    min_gain: Optional[float] = None,
    prefer_safe_c1fixed: bool = True,
    force_deterministic: bool = True,   # <<< NEW: default to deterministic carriers
) -> List[int]:
    """
    Build carrier positions for this frame, returning FILE bit indices.
    Steps:
      - Compute this frame's main_data [start,end) in FILE bits
      - Apply masking and inner margins
      - If force_deterministic: choose content-independent positions via PRF
        else: fall back to signbit scanner (c1-fixed or full), as before
      - Rank by _pos_score, dedup per file bit, then cap bits_per_frame
    """
    hb = _parse_header_basic(blob[fw.offset:fw.offset + 4])

    # Masking gate (global_gain)
    if min_gain is not None:
        avg_gain = _frame_avg_global_gain(blob, fw)
        if avg_gain < min_gain:
            return []

    # this frame’s main_data range (FILE bits)
    header_bits = 32
    crc_bits = 16 if hb["has_crc"] else 0
    si_bits = sideinfo_bytes(hb["version_id"], hb["channels"]) * 8
    file_main_start_bit = (fw.offset * 8) + header_bits + crc_bits + si_bits
    file_main_end_bit = file_main_start_bit + fw.available_main_bits

    # inner margins
    START_MARGIN = 16
    END_MARGIN = 16
    eff_start = file_main_start_bit + START_MARGIN
    eff_end = max(eff_start, file_main_end_bit - END_MARGIN)
    if eff_end <= eff_start:
        return []

    # Candidate positions
    positions_file: List[int] = []

    if force_deterministic:
        # Content-independent carriers inside the part3 window.
        # Throttle by fraction *before* taking, to keep behaviour similar.
        span = eff_end - eff_start
        # estimate how many we would have taken; this is just for pacing
        approx_total = max(1, span // 20)  # heuristic: ~1 per 20 bits
        want = approx_total
        if fraction < 1.0:
            want = max(1, int(want * fraction + 1e-9))
        if bits_per_frame is not None:
            want = min(want, int(bits_per_frame))
        positions_file = _deterministic_positions_in_window(
            eff_start, eff_end, key, frame_index, max_take=want if want > 0 else None
        )
    else:
        # ORIGINAL path: derive from sign-bit scanner (content-dependent)
        if prefer_safe_c1fixed and bits_per_frame is not None:
            positions_res = _frame_sign_positions_reservoir_c1fixed(blob, fw)
            if not positions_res:
                return []
        else:
            positions_res = _frame_sign_positions_reservoir(blob, fw)
            if not positions_res:
                return []

        # throttle by fraction
        limit = int(len(positions_res) * fraction + 1e-9)
        positions_res = positions_res[:limit]

        # map RES -> FILE and apply inner margins
        for rpos in positions_res:
            fpos = _res_to_file_bit(rpos, segs, breaks)
            if fpos is None:
                continue
            if eff_start <= fpos < eff_end:
                positions_file.append(fpos)

    if not positions_file:
        return []

    # Rank and dedup-by-pos (keep best score per unique file bit)
    score_by_pos: Dict[int, int] = {}
    for fpos in positions_file:
        score = _pos_score(key, frame_index, fpos)
        prev = score_by_pos.get(fpos)
        if prev is None or score < prev:
            score_by_pos[fpos] = score

    ranked = sorted(score_by_pos.items(), key=lambda kv: kv[1])
    positions_file = [p for p, _ in ranked]

    # Cap per frame
    if bits_per_frame is not None and len(positions_file) > bits_per_frame:
        positions_file = positions_file[:int(bits_per_frame)]

    return positions_file

# -------------------- public API --------------------

def estimate_capacity(
    path: str,
    max_frames: Optional[int] = None,
    fraction: float = 1.0,
    bits_per_frame: Optional[int] = None,
    mask_percentile: Optional[float] = 0.60,
) -> int:
    """Capacity (bits) using the same selector (masking defaults to 60th percentile)."""
    assert 0 < fraction <= 1.0
    total = 0
    with open(path, "rb") as fh:
        blob = fh.read()
    segs, breaks = _build_reservoir_map(blob)
    min_gain = _compute_min_gain_threshold(blob, mask_percentile)

    for fi, fw in enumerate(iter_frames_with_windows(blob)):
        if max_frames is not None and fi >= max_frames:
            break
        positions_file = _select_positions_for_frame(
            blob=blob,
            fw=fw,
            segs=segs,
            breaks=breaks,
            fraction=fraction,
            bits_per_frame=bits_per_frame,
            key=None,  # capacity independent of key
            frame_index=fi,
            min_gain=min_gain,
            prefer_safe_c1fixed=True,
            force_deterministic=True,
        )
        total += len(positions_file)
    return total

def embed_file(
    path_in: str,
    path_out: str,
    payload: bytes,
    payload_src: str | None = None,
    max_frames: Optional[int] = None,
    key: Optional[str] = None,
    fraction: float = 1.0,
    bits_per_frame: Optional[int] = None,
    mask_percentile: Optional[float] = 0.60,
    vigenere: bool = False,
) -> int:
    """
    Embed payload with header (magic+len+ext). If vigenere=True, XOR ONLY the
    payload bytes (after the header) using the given key.
    Global de-dup across frames ensures no file bit is used twice.
    Returns the total number of bits written (header+payload).
    """
    from mp3lsbsteg.stego.payload import wrap_payload, vigenere_xor, HEADER_SIZE

    assert 0 < fraction <= 1.0

    # 1) Build header+payload in clear
    wrapped = wrap_payload(payload, src_path=payload_src)  # [0:HEADER_SIZE]=header, [HEADER_SIZE:]=payload

    # 2) Optional Vigenère over payload bytes only (header stays plaintext)
    if vigenere:
        cipher_tail = vigenere_xor(wrapped[HEADER_SIZE:], key)
        wrapped = wrapped[:HEADER_SIZE] + cipher_tail

    # 3) Turn into a bitstream (MSB-first; must match _bits_to_bytes/_bytes_to_bits)
    bits_iter = iter(_bytes_to_bits(wrapped))
    written = 0

    with open(path_in, "rb") as fh:
        buf = bytearray(fh.read())
    blob = bytes(buf)

    segs, breaks = _build_reservoir_map(blob)
    bw = BitWriter(buf)

    min_gain = _compute_min_gain_threshold(blob, mask_percentile)

    # Global de-dup registry of absolute file-bit positions already used
    used_positions: set[int] = set()

    # 4) Iterate frames, select positions, globally de-dup, and write bits
    for fi, fw in enumerate(iter_frames_with_windows(blob)):
        if max_frames is not None and fi >= max_frames:
            break

        positions_file = _select_positions_for_frame(
            blob=blob, fw=fw, segs=segs, breaks=breaks,
            fraction=fraction, bits_per_frame=bits_per_frame,
            key=key, frame_index=fi, min_gain=min_gain,
            prefer_safe_c1fixed=True,
            force_deterministic=True,
        )
        if not positions_file:
            continue

        # Global de-dup: skip any file-bit already used by a previous frame
        positions_file = [p for p in positions_file if p not in used_positions]
        if not positions_file:
            continue

        for fpos in positions_file:
            try:
                bit = next(bits_iter)
            except StopIteration:
                with open(path_out, "wb") as out:
                    out.write(buf)
                return written

            # Explicit write: force target bit to payload bit (0/1), MSB-first
            bw.set_bit_value(fpos, bit & 1)
            used_positions.add(fpos)
            written += 1

    # 5) Flush to disk
    with open(path_out, "wb") as out:
        out.write(buf)
    return written

def extract_file_auto(
    path_in: str,
    max_frames: Optional[int] = None,
    key: Optional[str] = None,
    fraction: float = 1.0,
    bits_per_frame: Optional[int] = None,
    mask_percentile: Optional[float] = 0.60,
    vigenere: bool = False,
) -> Tuple[bytes, Optional[str]]:
    """
    Auto-length extractor (with extension & optional Vigenère decryption).
    - Reads bits in the same deterministic order as embed.
    - As soon as HEADER_SIZE bytes are available, validate header and compute total length.
    - Stops exactly once header+payload bits are collected.
    Returns: (payload_without_header, extension or "")
    """
    assert 0 < fraction <= 1.0
    out_bits: List[int] = []
    have_total_bytes: Optional[int] = None   # total = HEADER_SIZE + payload_len
    header_checked = False
    out_ext: Optional[str] = ""

    with open(path_in, "rb") as fh:
        blob = fh.read()
    br = BitReader(blob)
    segs, breaks = _build_reservoir_map(blob)
    min_gain = _compute_min_gain_threshold(blob, mask_percentile)

    def _bits_to_current_bytes(bits: List[int]) -> bytes:
        return _bits_to_bytes(bits)

    # Global de-dup registry (mirror embed): never read the same file bit twice
    used_positions: set[int] = set()

    for fi, fw in enumerate(iter_frames_with_windows(blob)):
        if max_frames is not None and fi >= max_frames:
            break

        positions_file = _select_positions_for_frame(
            blob=blob, fw=fw, segs=segs, breaks=breaks,
            fraction=fraction, bits_per_frame=bits_per_frame,
            key=key, frame_index=fi, min_gain=min_gain,
            prefer_safe_c1fixed=True,
            force_deterministic=True,
        )
        if not positions_file:
            continue

        # Global de-dup
        positions_file = [p for p in positions_file if p not in used_positions]
        if not positions_file:
            continue

        for fpos in positions_file:
            # Early stop if we already have header+payload
            if have_total_bytes is not None:
                needed_bits = have_total_bytes * 8
                if len(out_bits) >= needed_bits:
                    data = _bits_to_current_bytes(out_bits[:needed_bits])
                    cipher = data[HEADER_SIZE:have_total_bytes]
                    plain = vigenere_xor(cipher, key) if vigenere else cipher
                    return plain, out_ext

            # Read one carrier bit (MSB-first)
            save = br.tell()
            br.seek(fpos)
            out_bits.append(br.read_bits(1))
            br.seek(save)

            used_positions.add(fpos)

            # Parse header as soon as we have it
            if not header_checked and len(out_bits) >= HEADER_SIZE * 8:
                cur_bytes = _bits_to_current_bytes(out_bits[:HEADER_SIZE * 8])
                ok, total_needed, ext = try_parse_header(cur_bytes[:HEADER_SIZE])
                header_checked = True
                if ok is not True:
                    raise ValueError("Magic header not found; file does not contain MP3S payload")
                have_total_bytes = total_needed           # HEADER_SIZE + payload_len
                out_ext = ext or ""

    # Finalization: if loop ended but buffer might already have enough
    if have_total_bytes is not None:
        needed_bits = have_total_bytes * 8
        data = _bits_to_current_bytes(out_bits[:needed_bits])
        if len(data) >= have_total_bytes:
            cipher = data[HEADER_SIZE:have_total_bytes]
            plain = vigenere_xor(cipher, key) if vigenere else cipher
            return plain, out_ext

    raise ValueError("Incomplete MP3S payload: not enough embedded bits found")