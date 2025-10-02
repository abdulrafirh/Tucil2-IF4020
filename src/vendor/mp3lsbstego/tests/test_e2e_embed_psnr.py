# mp3lsbsteg/tests/test_e2e_embed_psnr.py
from __future__ import annotations
from pathlib import Path
import os
import math

from mp3lsbsteg import api

def test_e2e_embed_psnr(tmp_path: Path) -> None:
    # Locate example.mp3 sitting next to this test file
    test_dir = Path(__file__).resolve().parent
    in_mp3_path = test_dir / "example.mp3"
    assert in_mp3_path.exists(), f"Missing {in_mp3_path}"

    # Params (MUST match on extract)
    BPF = 4
    FRACTION = 1.0
    MASK_PCTL = 0.60
    KEY = "test-key"
    VIG = False

    payload = os.urandom(1024)
    payload_name = "p.bin"

    before = in_mp3_path.read_bytes()

    # Embed
    stego = api.embed_bytes(
        before,
        payload,
        payload_filename=payload_name,
        bits_per_frame=BPF,
        fraction=FRACTION,
        key=KEY,
        vigenere=VIG,
        mask_percentile=MASK_PCTL,
        max_frames=None,
    )

    # Optionally write to tmp for manual inspection (pytest cleans tmp)
    out_path = tmp_path / "example_stego_4bpf.mp3"
    out_path.write_bytes(stego)

    # Extract (match params!)
    recovered, ext = api.extract_auto_bytes(
        stego,
        bits_per_frame=BPF,
        fraction=FRACTION,
        key=KEY,
        mask_percentile=MASK_PCTL,
        max_frames=None,
        vigenere=VIG,
    )

    assert recovered == payload, "Recovered payload mismatch"
    assert ext == "bin", f"Unexpected extension: {ext!r}"

    # PSNR
    psnr_db = api.psnr(before, stego, samplerate=48000, mono=True, align="min")
    assert math.isfinite(psnr_db), "PSNR is not finite"
    # Optional: ensure “good enough” transparency (tune as you like)
    assert psnr_db > 30.0

    # Print only if you run with -s
    print(f"[OK] Embedded 1KB @ {BPF} bpf, extracted OK. PSNR = {psnr_db:.2f} dB")
