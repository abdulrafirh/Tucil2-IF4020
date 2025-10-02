# mp3lsbsteg/stego/payload.py
import os

MAGIC = b"MP3S"
HEADER_SIZE = 4 + 4 + 8  # magic + len + ext

def wrap_payload(data: bytes, src_path: str | None = None) -> bytes:
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("payload must be bytes")
    length = len(data).to_bytes(4, "big", signed=False)

    ext_bytes = b""
    if src_path:
        ext = os.path.splitext(src_path)[1].lstrip(".").lower()
        if ext:
            ext_bytes = ext.encode("ascii", errors="ignore")[:8]
    ext_bytes = ext_bytes.ljust(8, b"\x00")

    return MAGIC + length + ext_bytes + data

def try_parse_header(buf: bytes):
    if len(buf) < HEADER_SIZE:
        return (None, None, None)
    magic_ok = buf[:4] == MAGIC
    payload_len = int.from_bytes(buf[4:8], "big", signed=False)
    ext_raw = buf[8:16].rstrip(b"\x00")
    try:
        ext = ext_raw.decode("ascii")
    except UnicodeDecodeError:
        ext = ""
    total_needed = HEADER_SIZE + payload_len
    return (magic_ok, total_needed, ext)

def vigenere_xor(data: bytes, key: str | None) -> bytes:
    """
    Repeating-key XOR over arbitrary bytes. If key is None/empty, returns data unchanged.
    """
    if not key:
        return data
    k = key.encode("utf-8")
    out = bytearray(len(data))
    m = len(k)
    for i, b in enumerate(data):
        out[i] = b ^ k[i % m]
    return bytes(out)
