# mp3lsbsteg/metrics/psnr.py
from __future__ import annotations
import io
import math
from typing import Literal, Tuple, List

import numpy as np
from pydub import AudioSegment  # requires ffmpeg installed on the system


def _audiosegment_to_float32(
    blob: bytes,
    *,
    samplerate: int,
    mono: bool,
) -> np.ndarray:
    """
    Decode arbitrary audio (e.g., MP3) using pydub/ffmpeg and return
    float32 PCM in [-1, 1] with shape (num_samples, channels).

    - Resamples to `samplerate`
    - If mono=True, mixes down to 1 channel
    """
    if not blob:
        raise ValueError("Empty audio blob")

    seg = AudioSegment.from_file(io.BytesIO(blob))  # ffmpeg-backed
    seg = seg.set_frame_rate(int(samplerate))
    seg = seg.set_channels(1 if mono else seg.channels)

    # pydub gives interleaved int PCM via get_array_of_samples()
    samples = np.array(seg.get_array_of_samples(), dtype=np.float32)

    # Scale to [-1, 1] based on sample width
    # e.g., 16-bit -> max |value| is 2^(15) = 32768
    max_abs = float(1 << (8 * seg.sample_width - 1))
    if max_abs <= 0:
        raise ValueError(f"Unsupported sample width: {seg.sample_width}")
    samples = samples / max_abs

    ch = seg.channels
    if ch > 1:
        # de-interleave: (..., ch)
        samples = samples.reshape(-1, ch)
    else:
        samples = samples.reshape(-1, 1)

    return samples.astype(np.float32, copy=False)


def _align_pair(
    x: np.ndarray,
    y: np.ndarray,
    *,
    mode: Literal["min", "first", "pad"] = "min",
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Ensure both arrays share the same length in samples.
    - 'min'   : crop both to the shorter length
    - 'first' : crop y to x length
    - 'pad'   : zero-pad the shorter to match the longer (not recommended for PSNR)
    """
    if x.ndim != 2 or y.ndim != 2:
        raise ValueError("Inputs must be shaped (num_samples, channels)")

    nx, ny = x.shape[0], y.shape[0]
    if mode == "min":
        n = min(nx, ny)
        return x[:n], y[:n]
    elif mode == "first":
        n = nx
        return x[:n], y[:n]
    elif mode == "pad":
        n = max(nx, ny)
        def pad(a: np.ndarray, n: int) -> np.ndarray:
            if a.shape[0] >= n:
                return a[:n]
            pad_len = n - a.shape[0]
            return np.vstack([a, np.zeros((pad_len, a.shape[1]), dtype=a.dtype)])
        return pad(x, n), pad(y, n)
    else:
        raise ValueError("mode must be 'min', 'first', or 'pad'")


def _psnr_from_arrays_float32(
    ref: np.ndarray,
    test: np.ndarray,
    *,
    per_channel: bool = False,
    eps: float = 1e-20,
) -> float | List[float]:
    """
    Compute PSNR (dB) for float32 arrays in [-1, 1], shape (N, C).
    If per_channel=True, returns a list of PSNR per channel.
    Otherwise returns a single averaged PSNR (mean of per-channel PSNRs).
    """
    if ref.shape != test.shape:
        raise ValueError(f"Shape mismatch: {ref.shape} vs {test.shape}")
    if ref.size == 0:
        raise ValueError("Empty audio after alignment")

    # MSE per channel
    mse_ch = ((ref - test) ** 2).mean(axis=0)
    # For normalized audio, MAX = 1.0
    with np.errstate(divide="ignore"):
        psnr_ch = 10.0 * np.log10(1.0 / np.maximum(mse_ch, eps))

    if per_channel:
        return [float(v) for v in psnr_ch]
    return float(psnr_ch.mean())


def audio_psnr(
    before_bytes: bytes,
    after_bytes: bytes,
    *,
    samplerate: int = 48000,
    mono: bool = True,
    align: Literal["min", "first", "pad"] = "min",
) -> float:
    """
    Decode both audio blobs with pydub/ffmpeg and compute PSNR (dB).
      - `samplerate`: resample both to this rate
      - `mono`: mix to mono before comparison (recommended for a single score)
      - `align`: handle small length mismatches (default 'min' crop)

    Returns a single PSNR value (dB). If signals are identical after decode,
    returns +inf.
    """
    x = _audiosegment_to_float32(before_bytes, samplerate=samplerate, mono=mono)
    y = _audiosegment_to_float32(after_bytes, samplerate=samplerate, mono=mono)
    x, y = _align_pair(x, y, mode=align)
    return _psnr_from_arrays_float32(x, y, per_channel=False)


def audio_psnr_per_channel(
    before_bytes: bytes,
    after_bytes: bytes,
    *,
    samplerate: int = 48000,
    align: Literal["min", "first", "pad"] = "min",
) -> List[float]:
    """
    Compute PSNR per channel (no mono mixdown).
    Returns a list of PSNR values (dB), one per channel.
    """
    x = _audiosegment_to_float32(before_bytes, samplerate=samplerate, mono=False)
    y = _audiosegment_to_float32(after_bytes, samplerate=samplerate, mono=False)
    x, y = _align_pair(x, y, mode=align)

    # Ensure equal channel count for fair comparison (basic strategy):
    cx, cy = x.shape[1], y.shape[1]
    if cx != cy:
        # Mix down both to min channel count (usually 1)
        c = min(cx, cy)
        x = x[:, :c]
        y = y[:, :c]

    out = _psnr_from_arrays_float32(x, y, per_channel=True)
    return out  # type: ignore[return-value]
