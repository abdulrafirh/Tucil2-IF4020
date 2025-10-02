# app/routes/api_bp.py
from __future__ import annotations
from flask import Blueprint, request, abort, send_file, Response
from werkzeug.utils import secure_filename
import io

from ..services.steg_service import (
    embed_stego,
    extract_payload,
    _parse_bpf,
    _parse_bool,
    estimate_capacity_bytes,
)

api_bp = Blueprint("api", __name__)

@api_bp.get("/health")
def health():
    return {"ok": True, "service": "mp3lsbsteg-backend"}

@api_bp.post("/embed")
def embed():
    """
    Multipart form-data:
      - carrier: MP3 file (required)
      - payload: file to hide (required)
      - bits_per_frame: int [1..4] (optional, default 4)
      - key: string (optional)
      - vigenere: bool (optional, default false)

    Returns: stego MP3 stream (audio/mpeg) with X-PSNR-dB header.
    """
    if "carrier" not in request.files or "payload" not in request.files:
        abort(400, "carrier and payload files are required")

    carrier_file = request.files["carrier"]
    payload_file = request.files["payload"]
    key = request.form.get("key") or None
    bits_per_frame = _parse_bpf(request.form.get("bits_per_frame"), default=4)
    vigenere = _parse_bool(request.form.get("vigenere"), default=False)

    carrier_bytes = carrier_file.read()
    payload_bytes = payload_file.read()

    # Use the original filename for header extension; secure it for safety.
    payload_name = secure_filename(payload_file.filename or "p.bin") or "p.bin"

    stego_bytes, psnr_db = embed_stego(
        carrier_bytes=carrier_bytes,
        payload_bytes=payload_bytes,
        payload_filename=payload_name,
        bits_per_frame=bits_per_frame,
        key=key,
        vigenere=vigenere,
    )

    bio = io.BytesIO(stego_bytes)
    bio.seek(0)
    resp = send_file(
        bio,
        mimetype="audio/mpeg",
        as_attachment=True,
        download_name="stego.mp3",
        max_age=0,
        conditional=False,
        etag=False,
        last_modified=None,
    )
    resp.headers["X-PSNR-dB"] = f"{psnr_db:.2f}"
    resp.headers["X-Bits-Per-Frame"] = str(bits_per_frame)
    return resp

@api_bp.post("/extract")
def extract():
    """
    Multipart form-data:
      - stego: MP3 file with embedded payload (required)
      - bits_per_frame: int [1..4] (optional, default 4; MUST match embed)
      - key: string (optional; MUST match embed)
      - vigenere: bool (optional; MUST match embed)

    Returns: recovered payload stream (application/octet-stream).
    """
    if "stego" not in request.files:
        abort(400, "stego file is required")

    stego_file = request.files["stego"]
    key = request.form.get("key") or None
    bits_per_frame = _parse_bpf(request.form.get("bits_per_frame"), default=4)
    vigenere = _parse_bool(request.form.get("vigenere"), default=False)

    stego_bytes = stego_file.read()

    data, ext = extract_payload(
        stego_bytes=stego_bytes,
        bits_per_frame=bits_per_frame,
        key=key,
        vigenere=vigenere,
    )

    filename = f"recovered.{ext}" if ext else "recovered.bin"
    bio = io.BytesIO(data)
    bio.seek(0)
    resp = send_file(
        bio,
        mimetype="application/octet-stream",
        as_attachment=True,
        download_name=filename,
        max_age=0,
        conditional=False,
        etag=False,
        last_modified=None,
    )
    resp.headers["X-Ext"] = ext or ""
    return resp

@api_bp.post("/capacity")
def capacity():
    """
    Multipart form-data:
      - carrier: MP3 file (required)
      - bits_per_frame: int [1..4] (optional, default 4)
      - payload_size: int (optional) – if provided, response includes `fits`
      - vigenere: bool (optional) – echoed back, does not change capacity

    Returns JSON with capacity metrics.
    """
    if "carrier" not in request.files:
        abort(400, "carrier file is required")

    carrier_file = request.files["carrier"]
    carrier_bytes = carrier_file.read()

    bits_per_frame = _parse_bpf(request.form.get("bits_per_frame"), default=4)
    payload_size = request.form.get("payload_size")
    vigenere = _parse_bool(request.form.get("vigenere"), default=False)  # for UI parity only

    try:
        payload_size_int = int(payload_size) if payload_size is not None else None
    except ValueError:
        abort(400, "payload_size must be an integer")

    metrics = estimate_capacity_bytes(
        carrier_bytes=carrier_bytes,
        bits_per_frame=bits_per_frame,
    )
    resp = {
        "ok": True,
        "bits_per_frame": bits_per_frame,
        "vigenere": bool(vigenere),  # informational; capacity is unaffected
        **metrics,
    }
    if payload_size_int is not None:
        resp["payload_size"] = payload_size_int
        resp["fits"] = payload_size_int + metrics["header_size_bytes"] <= metrics["capacity_bytes"]
    return resp