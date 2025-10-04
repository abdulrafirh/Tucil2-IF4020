# mp3lsbsteg/api.py
from __future__ import annotations
from typing import Optional, Tuple, List

from mp3lsbsteg.stego.payload import (
    wrap_payload,
    try_parse_header,
    HEADER_SIZE,
    vigenere_xor,
)
from mp3lsbsteg.io.bitreader import BitReader
from mp3lsbsteg.io.bitwriter import BitWriter
from mp3lsbsteg.mpeg.stream import iter_frames_with_windows
from mp3lsbsteg.metrics.psnr import audio_psnr as _audio_psnr, audio_psnr_per_channel as _audio_psnr_per_channel

from mp3lsbsteg.stego.embed import (
    _build_reservoir_map,
    _compute_min_gain_threshold,
    _select_positions_for_frame,
    _bytes_to_bits,
    _bits_to_bytes,
)

class Mp3StegoError(Exception):
    """Generic API error for MP3 LSB stego operations."""

# --------------------------
# Helpers
# --------------------------

def _validate_fraction(f: float) -> None:
    if not (0.0 < f <= 1.0):
        raise Mp3StegoError(f"fraction must be in (0, 1], got {f}")

def _normalize_mask_percentile(p: Optional[float]) -> Optional[float]:
    if p is None:
        return None

    return None if p < 0 else p

def _ext_from_filename(path_or_name: Optional[str]) -> Optional[str]:
    if not path_or_name:
        return ""
    name = path_or_name.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    if "." not in name:
        return ""
    ext = name.rsplit(".", 1)[-1]
    return ext

def _validate_extension(ext: Optional[str]) -> str:
    ext = (ext or "").strip().lower()
    if len(ext) > 8:
        raise Mp3StegoError(f"extension '{ext}' exceeds 8 bytes (limit)")

    for ch in ext:
        if not (ch.isalnum() or ch in ("_", "-")):
            raise Mp3StegoError(f"extension contains unsupported char: {ch!r}")
    return ext

def _count_capacity_bits(
    mp3_bytes: bytes,
    *,
    bits_per_frame: Optional[int],
    fraction: float,
    key: Optional[str],
    mask_percentile: Optional[float],
    max_frames: Optional[int],
) -> int:
    _validate_fraction(fraction)
    mp3_blob = mp3_bytes  # alias for clarity

    segs, breaks = _build_reservoir_map(mp3_blob)
    min_gain = _compute_min_gain_threshold(mp3_blob, mask_percentile)

    used_positions: set[int] = set()
    capacity_bits = 0

    for fi, fw in enumerate(iter_frames_with_windows(mp3_blob)):
        if max_frames is not None and fi >= max_frames:
            break

        positions_file = _select_positions_for_frame(
            blob=mp3_blob, fw=fw, segs=segs, breaks=breaks,
            fraction=fraction, bits_per_frame=bits_per_frame,
            key=key, frame_index=fi, min_gain=min_gain,
            prefer_safe_c1fixed=True,
            force_deterministic=True,
        )
        if not positions_file:
            continue

        positions_file = [p for p in positions_file if p not in used_positions]
        if not positions_file:
            continue

        capacity_bits += len(positions_file)
        used_positions.update(positions_file)

    return capacity_bits

# --------------------------
# Public API
# --------------------------

def estimate_capacity(
    mp3_bytes: bytes,
    *,
    bits_per_frame: Optional[int] = None,
    fraction: float = 1.0,
    key: Optional[str] = None,
    mask_percentile: Optional[float] = 0.60,
    max_frames: Optional[int] = None,
) -> int:
    mask_p = _normalize_mask_percentile(mask_percentile)
    return _count_capacity_bits(
        mp3_bytes,
        bits_per_frame=bits_per_frame,
        fraction=fraction,
        key=key,
        mask_percentile=mask_p,
        max_frames=max_frames,
    )

def embed_bytes(
    mp3_bytes: bytes,
    payload: bytes,
    *,
    payload_filename: Optional[str] = None,
    bits_per_frame: Optional[int] = None,
    fraction: float = 1.0,
    key: Optional[str] = None,
    vigenere: bool = False,
    mask_percentile: Optional[float] = 0.60,
    max_frames: Optional[int] = None,
) -> bytes:
    _validate_fraction(fraction)
    mask_p = _normalize_mask_percentile(mask_percentile)

    ext = _validate_extension(_ext_from_filename(payload_filename))
    wrapped = wrap_payload(payload, src_path=payload_filename)

    if vigenere:
        cipher_tail = vigenere_xor(wrapped[HEADER_SIZE:], key)
        wrapped = wrapped[:HEADER_SIZE] + cipher_tail

    total_bits_needed = len(wrapped) * 8

    cap_bits = _count_capacity_bits(
        mp3_bytes,
        bits_per_frame=bits_per_frame,
        fraction=fraction,
        key=key,
        mask_percentile=mask_p,
        max_frames=max_frames,
    )
    if total_bits_needed > cap_bits:
        raise Mp3StegoError(
            f"Insufficient capacity: need {total_bits_needed} bits "
            f"(~{len(wrapped)} bytes), available {cap_bits} bits "
            f"(~{cap_bits//8} bytes)."
        )

    buf = bytearray(mp3_bytes)
    blob = bytes(buf)

    segs, breaks = _build_reservoir_map(blob)
    bw = BitWriter(buf)
    min_gain = _compute_min_gain_threshold(blob, mask_p)

    bits_iter = iter(_bytes_to_bits(wrapped))
    written = 0
    used_positions: set[int] = set()

    for fi, fw in enumerate(iter_frames_with_windows(blob)):
        if max_frames is not None and fi >= max_frames:
            break
        if written >= total_bits_needed:
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

        positions_file = [p for p in positions_file if p not in used_positions]
        if not positions_file:
            continue

        for fpos in positions_file:
            if written >= total_bits_needed:
                break
            bit = next(bits_iter) & 1
            bw.set_bit_value(fpos, bit)
            used_positions.add(fpos)
            written += 1

    if written < total_bits_needed:
        raise Mp3StegoError(
            f"Unexpected early stop: wrote {written}/{total_bits_needed} bits."
        )

    return bytes(buf)

def extract_auto_bytes(
    mp3_bytes: bytes,
    *,
    bits_per_frame: Optional[int] = None,
    fraction: float = 1.0,
    key: Optional[str] = None,
    vigenere: bool = False,
    mask_percentile: Optional[float] = 0.60,
    max_frames: Optional[int] = None,
) -> Tuple[bytes, Optional[str]]:
    _validate_fraction(fraction)
    mask_p = _normalize_mask_percentile(mask_percentile)

    blob = mp3_bytes
    br = BitReader(blob)
    segs, breaks = _build_reservoir_map(blob)
    min_gain = _compute_min_gain_threshold(blob, mask_p)

    out_bits: List[int] = []
    have_total_bytes: Optional[int] = None
    header_checked = False
    out_ext: Optional[str] = ""

    def _bits_to_current_bytes(bits: List[int]) -> bytes:
        return _bits_to_bytes(bits)

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

        positions_file = [p for p in positions_file if p not in used_positions]
        if not positions_file:
            continue

        for fpos in positions_file:
            if have_total_bytes is not None:
                needed_bits = have_total_bytes * 8
                if len(out_bits) >= needed_bits:
                    data = _bits_to_current_bytes(out_bits[:needed_bits])
                    cipher = data[HEADER_SIZE:have_total_bytes]
                    plain = vigenere_xor(cipher, key) if vigenere else cipher
                    return plain, out_ext

            save = br.tell()
            br.seek(fpos)
            out_bits.append(br.read_bits(1))
            br.seek(save)
            used_positions.add(fpos)

            if not header_checked and len(out_bits) >= HEADER_SIZE * 8:
                cur_bytes = _bits_to_current_bytes(out_bits[:HEADER_SIZE * 8])
                ok, total_needed, ext = try_parse_header(cur_bytes[:HEADER_SIZE])
                header_checked = True
                if ok is not True:
                    raise Mp3StegoError("Magic header not found; no MP3S payload present")
                have_total_bytes = total_needed
                out_ext = ext or ""

    if have_total_bytes is not None:
        needed_bits = have_total_bytes * 8
        data = _bits_to_current_bytes(out_bits[:needed_bits])
        if len(data) >= have_total_bytes:
            cipher = data[HEADER_SIZE:have_total_bytes]
            plain = vigenere_xor(cipher, key) if vigenere else cipher
            return plain, out_ext

    raise Mp3StegoError("Incomplete MP3S payload: not enough embedded bits found")


# ---------------------------
# Metrics: PSNR (via pydub)
# ---------------------------

def psnr(
    before_mp3: bytes,
    after_mp3: bytes,
    *,
    samplerate: int = 48_000,
    mono: bool = True,
    align: str = "min",
) -> float:
    """Compute PSNR (dB) between two decoded audio streams.

    This is a thin wrapper around :func:`mp3lsbsteg.metrics.psnr.audio_psnr`,
    re-exposed here for convenience by web apps.

    Parameters
    ----------
    before_mp3 : bytes
        Original (pre-stego) MP3 bytes.
    after_mp3 : bytes
        Modified (post-stego) MP3 bytes.
    samplerate : int, default 48000
        Resample both to this rate before comparison.
    mono : bool, default True
        If True, mix to mono first, returning a single PSNR value.
    align : {'min','first','pad'}, default 'min'
        Handle small length mismatches.

    Returns
    -------
    float
        PSNR in dB (``math.inf`` if identical post-decode).
    """
    return _audio_psnr(before_mp3, after_mp3, samplerate=samplerate, mono=mono, align=align)  # type: ignore[arg-type]


def psnr_per_channel(
    before_mp3: bytes,
    after_mp3: bytes,
    *,
    samplerate: int = 48_000,
    align: str = "min",
) -> list[float]:
    """Compute PSNR (dB) per-channel and return a list of dB values.

    Wrapper for :func:`mp3lsbsteg.metrics.psnr.audio_psnr_per_channel`.
    Channels will be aligned and truncated to a common count as needed.

    Returns
    -------
    list[float]
        One PSNR (dB) per channel.
    """
    return list(_audio_psnr_per_channel(before_mp3, after_mp3, samplerate=samplerate, align=align))  # type: ignore[arg-type]
