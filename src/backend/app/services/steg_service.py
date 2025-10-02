# app/services/steg_service.py
from __future__ import annotations
from typing import Optional, Tuple
from mp3lsbsteg import api
from mp3lsbsteg.stego.payload import HEADER_SIZE  
import io
import math

# Hardcoded selection settings (per your request)
FRACTION = 1.0
MASK_PCTL = 0.60
MAX_FRAMES = None  # don't customize

def _parse_bpf(raw: Optional[str], default: int = 4) -> int:
    try:
        bpf = int(raw) if raw is not None else default
    except ValueError:
        raise ValueError("bits_per_frame must be an integer")
    if not (1 <= bpf <= 8):  # library typically uses 1..4, but allow up to 8 if supported
        raise ValueError("bits_per_frame must be between 1 and 8")
    return bpf

def _parse_bool(raw: Optional[str], default: bool = False) -> bool:
    if raw is None:
        return default
    s = str(raw).strip().lower()
    return s in {"1", "true", "t", "yes", "y", "on"}

def embed_stego(
    *,
    carrier_bytes: bytes,
    payload_bytes: bytes,
    payload_filename: Optional[str],
    bits_per_frame: int,
    key: Optional[str],
    vigenere: bool,
) -> Tuple[bytes, float]:
    """Return (stego_mp3_bytes, psnr_db)."""
    stego = api.embed_bytes(
        carrier_bytes,
        payload_bytes,
        payload_filename=payload_filename,
        bits_per_frame=bits_per_frame,
        fraction=FRACTION,
        key=key or None,
        vigenere=vigenere,
        mask_percentile=MASK_PCTL,
        max_frames=MAX_FRAMES,
    )
    # PSNR after decode (mono single score)
    psnr_db = api.psnr(carrier_bytes, stego, samplerate=48000, mono=True, align="min")
    if not math.isfinite(psnr_db):
        psnr_db = float("inf")
    return stego, psnr_db

def extract_payload(
    *,
    stego_bytes: bytes,
    bits_per_frame: int,
    key: Optional[str],
    vigenere: bool,
) -> Tuple[bytes, str]:
    """Return (payload_bytes, ext)."""
    data, ext = api.extract_auto_bytes(
        stego_bytes,
        bits_per_frame=bits_per_frame,
        fraction=FRACTION,
        key=key or None,
        mask_percentile=MASK_PCTL,
        max_frames=MAX_FRAMES,
        vigenere=vigenere,
    )
    return data, ext or ""

def estimate_capacity_bytes(*, carrier_bytes: bytes, bits_per_frame: int) -> dict:
    """
    Returns capacity metrics for the given carrier and settings.
    fraction=1.0, mask_percentile=0.60, max_frames=None are hardcoded.
    """
    cap_bits = api.estimate_capacity(
        carrier_bytes,
        bits_per_frame=bits_per_frame,
        fraction=FRACTION,
        mask_percentile=MASK_PCTL,
        max_frames=MAX_FRAMES,
    )
    cap_bytes = cap_bits // 8
    header_bytes = HEADER_SIZE  # 16
    usable_payload_bytes = max(cap_bytes - header_bytes, 0)
    return {
        "capacity_bits": int(cap_bits),
        "capacity_bytes": int(cap_bytes),
        "header_size_bytes": int(header_bytes),
        "usable_payload_bytes": int(usable_payload_bytes),
    }
