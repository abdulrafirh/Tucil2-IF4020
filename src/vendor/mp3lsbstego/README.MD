# mp3lsbsteg

MP3 LSB steganography toolkit with **deterministic embedding**, **auto-length extraction (magic + size + ext)**, **capacity estimation**, and **PSNR metrics** (via `pydub`/FFmpeg).

---

## Features

- 🔒 Deterministic bit-position selection (seeded by `key`)
- 🧠 Perceptual masking via global-gain percentile (`mask_percentile`)
- 🎚️ Cap carriers per frame (`bits_per_frame`, e.g. 1–4)
- 📦 Auto header: magic + total size + file extension (≤ 8 chars)
- 📏 Capacity estimation
- 📈 PSNR & per-channel PSNR (decoded with `pydub`, requires FFmpeg)

---

## Installation

> Requires **Python ≥ 3.9** and **FFmpeg** available on PATH (for `pydub`).

Install FFmpeg:
- **Ubuntu/Debian**: `sudo apt-get update && sudo apt-get install -y ffmpeg`
- **macOS** (Homebrew): `brew install ffmpeg`
- **Windows** (Chocolatey): `choco install ffmpeg`

Install the package (from repo root, where `pyproject.toml` lives):

```bash
# dev/editable install + test tooling
pip install -e .[dev]

# or regular install
pip install .
```

---

## Quickstart (API)

```python
from mp3lsbsteg import api

# Load MP3 bytes (e.g., from disk or HTTP)
with open("clean.mp3", "rb") as f:
    mp3_bytes = f.read()

payload = b"secret data here"
stego_mp3 = api.embed_bytes(
    mp3_bytes,
    payload,
    payload_filename="p.bin",     # extension ≤ 8 chars is enforced
    bits_per_frame=4,             # 1..4 recommended
    fraction=1.0,                 # fraction of eligible sign-bits to use
    key="my-key",                 # seeds deterministic selection (and Vigenère if enabled)
    vigenere=False,               # optional repeating-key XOR layer
    mask_percentile=0.60,         # 0..1; None to disable masking
    max_frames=None,              # limit frames (optional)
)

# Extract (params MUST match the embed side)
data, ext = api.extract_auto_bytes(
    stego_mp3,
    bits_per_frame=4,
    fraction=1.0,
    key="my-key",
    mask_percentile=0.60,
    max_frames=None,
    vigenere=False,
)
assert data == payload

# Quality metric (dB). Uses pydub/FFmpeg decode; mono=True gives single PSNR.
psnr_db = api.psnr(mp3_bytes, stego_mp3, samplerate=48000, mono=True, align="min")
print("PSNR:", psnr_db, "dB")
```

**Also available:**
```python
api.psnr_per_channel(before_bytes, after_bytes, samplerate=48000, align="min")  # -> list[float]
```

---

## CLI Usage (no entry points needed)

Use the module runner:

```bash
# Embed a file
python -m mp3lsbsteg.cli.embed_file clean.mp3 stego.mp3 payload.bin \
  --bits-per-frame 4 --key "my-key" --mask-pctl 0.60

# Extract automatically (size+ext from header)
python -m mp3lsbsteg.cli.extract_auto stego.mp3 out \
  --bits-per-frame 4 --key "my-key" --mask-pctl 0.60
```

> If you prefer global commands (e.g., `mp3lsbsteg-embed`), add console scripts to `pyproject.toml`:
>
> ```toml
> [project.scripts]
> mp3lsbsteg-embed = "mp3lsbsteg.cli.embed_file:main"
> mp3lsbsteg-extract = "mp3lsbsteg.cli.extract_auto:main"
> ```

---

## Parameters (important)

- **`bits_per_frame`**: cap of carriers per MPEG frame (1–4 typical). Must match on extract.
- **`fraction`**: use only this fraction of eligible sign bits (0 < f ≤ 1). Must match on extract.
- **`mask_percentile`**: perceptual masking using global-gain; higher = stricter masking. Set to `None` to disable. Must match on extract.
- **`key`**: seeds the deterministic selection (and Vigenère if `vigenere=True`). Must match on extract.
- **`max_frames`**: optional frame limit. Must match on extract.
- **`payload_filename`**: used to store extension in the header; extension must be ≤ **8** characters.

If any of the above differ between embed/extract, the extractor will not find the header (by design).

---

## Capacity Estimation

```python
# Rough available capacity in bits (given your selection settings)
bits = api.estimate_capacity(
    mp3_bytes,
    bits_per_frame=4,
    fraction=1.0,
    mask_percentile=0.60,
    max_frames=None,
)
print("Capacity (bytes):", bits // 8)
```

> This is an estimate based on decoded frame windows and your selection settings.

---

## PSNR Formula

Signals are decoded to float32 in **[-1, 1]**, optionally resampled and mixed to mono.

\[
\text{MSE} = \frac{1}{N}\sum_{i=1}^{N}(x_i - y_i)^2, \quad
\text{PSNR} = 10\log_{10}\left(\frac{1.0}{\text{MSE}}\right)
\]

- `api.psnr(...)` → single PSNR (dB)
- `api.psnr_per_channel(...)` → list of PSNR (dB) per channel

---

## Tests

A minimal end-to-end test is included.

**Place a small MP3 at**: `tests/example.mp3`

Run with `pytest` (recommended):

```bash
pytest -q
```

Or run the script directly:

```bash
python tests/test_e2e_embed_psnr.py
```

> The pytest version writes artifacts to a temporary directory; the script version writes `example_stego_4bpf.mp3` then deletes it at the end.

---

## Project Layout

```
mp3lsbsteg/
  mp3lsbsteg/
    api.py                  # public API: embed/extract/capacity/psnr
    metrics/psnr.py         # PSNR helpers (pydub/FFmpeg)
    stego/                  # embedding/extraction internals
    mpeg/                   # MPEG parsing helpers
    io/                     # bit readers/writers
    cli/                    # python -m ... commands
  tests/
    test_e2e_embed_psnr.py
    example.mp3             # (you add this)
  pyproject.toml
  README.md
```

---

## Tips & Troubleshooting

- **No audio output / PSNR fails** → ensure **FFmpeg** is installed and on PATH.
- **“Magic header not found”** → your extractor params must match the embed params (`bits_per_frame`, `fraction`, `mask_percentile`, `key`, `max_frames`, `vigenere`).
- **Import errors in tests** → install the package first: `pip install -e .[dev]`.

---

## License

MIT
