#!/usr/bin/env python3
import argparse
import numpy as np
from pydub import AudioSegment

def text_to_bits(text: str):
    data = text.encode("utf-8")
    bits = []
    for b in data:
        for i in range(8):
            bits.append((b >> (7 - i)) & 1)
    return np.array(bits, dtype=np.int16)

def bits_to_text(bits):
    out = bytearray()
    for i in range(0, len(bits), 8):
        chunk = bits[i:i+8]
        if len(chunk) < 8: break
        val = 0
        for bit in chunk:
            val = (val << 1) | (bit & 1)
        out.append(val)
    # show corruption rather than silently dropping bytes
    return out.decode("utf-8", errors="replace")

def ensure_16bit(seg: AudioSegment) -> AudioSegment:
    # keep sr/ch, but force 16-bit so LSB handling is predictable
    return seg.set_sample_width(2)

def embed(in_mp3, out_mp3, message="STEGANO", repeat=9, bitrate="320k"):
    seg = ensure_16bit(AudioSegment.from_file(in_mp3))
    samples = np.array(seg.get_array_of_samples(), dtype=np.int16)

    base_bits = text_to_bits(message)
    # repeat each bit R times for robustness
    if repeat < 1: repeat = 1
    bits = np.repeat(base_bits, repeat).astype(np.int16)

    if bits.size > samples.size:
        raise ValueError(f"Not enough samples to hide {len(base_bits)} bits ×{repeat} (need {bits.size}, have {samples.size})")

    # overwrite LSBs from offset 0
    out = samples.copy()
    out[:bits.size] = (out[:bits.size] & ~1) | bits

    stego = seg._spawn(out.tobytes())
    stego.export(out_mp3, format="mp3", bitrate=bitrate)
    print(f"Embedded '{message}' ({len(base_bits)} bits, repeat x{repeat} → {bits.size} samples) into {out_mp3}")

def extract(stego_mp3, length_chars=7, repeat=9):
    seg = ensure_16bit(AudioSegment.from_file(stego_mp3))
    samples = np.array(seg.get_array_of_samples(), dtype=np.int16)

    total_bits = length_chars * 8
    read_bits = total_bits * max(1, repeat)
    if read_bits > samples.size:
        raise ValueError(f"Not enough samples to read {total_bits} bits ×{repeat} (need {read_bits}, have {samples.size})")

    raw = (samples[:read_bits] & 1).astype(np.int16)

    if repeat <= 1:
        decided = raw[:total_bits]
    else:
        # majority vote per group of R bits
        decided = []
        R = repeat
        for i in range(total_bits):
            chunk = raw[i*R:(i+1)*R]
            decided.append(1 if np.sum(chunk) >= (R+1)//2 else 0)
        decided = np.array(decided, dtype=np.int16)

    msg = bits_to_text(decided.tolist())
    print(f"Recovered: '{msg}'")
    return msg

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["embed", "extract"])
    p.add_argument("--infile", required=True)
    p.add_argument("--outfile")
    p.add_argument("--text", default="STEGANO")
    p.add_argument("--repeat", type=int, default=9, help="bit repetition factor")
    p.add_argument("--bitrate", default="320k")
    args = p.parse_args()

    if args.mode == "embed":
        if not args.outfile:
            raise SystemExit("--outfile required for embed")
        embed(args.infile, args.outfile, args.text, repeat=args.repeat, bitrate=args.bitrate)
    else:
        # extract expects the *intended* plaintext length to reconstruct the right number of bits
        extract(args.infile, length_chars=len(args.text), repeat=args.repeat)
