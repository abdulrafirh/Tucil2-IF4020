#!/usr/bin/env bash
set -euo pipefail

python --version
pip --version

pip install --no-cache-dir --upgrade pip setuptools wheel

if [ -d "/vendor/mp3lsbstego" ]; then
  echo "[entrypoint] Installing vendor mp3lsbsteg (non-editable) from /vendor/mp3lsbstego"
  pip install --no-cache-dir /vendor/mp3lsbstego
fi

exec flask run --host=0.0.0.0 --port=8080
