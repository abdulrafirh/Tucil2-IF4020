# mp3lsbsteg/cli/embed_file.py
import os
import argparse
from mp3lsbsteg.stego.embed import embed_file

def main():
    ap = argparse.ArgumentParser(
        description="Embed a payload file into an MP3 (sign-bit stego)."
    )
    ap.add_argument("in_mp3", help="Input MP3 path")
    ap.add_argument("out_mp3", help="Output MP3 path (stego)")
    ap.add_argument("payload_path", help="Payload file to embed")

    ap.add_argument("--frames", type=int, default=None,
                    help="Max number of frames to process (default: all)")
    ap.add_argument("--key", default=None,
                    help="Key used for deterministic position selection (and Vigenère if enabled)")
    ap.add_argument("--fraction", type=float, default=1.0,
                    help="Use only this fraction of candidate sign bits (0<frac<=1)")
    ap.add_argument("--bits-per-frame", type=int, default=None,
                    help="Cap carriers per frame (e.g., 1..4)")
    ap.add_argument("--mask-pctl", type=float, default=0.60,
                    help="Global-gain percentile [0..1]; use -1 to disable masking (default: 0.60)")
    ap.add_argument("--vigenere", action="store_true",
                    help="Apply repeating-key XOR to payload bytes before embedding")

    args = ap.parse_args()

    # load payload
    with open(args.payload_path, "rb") as fh:
        payload = fh.read()

    # resolve masking config
    mask_percentile = None if args.mask_pctl is not None and args.mask_pctl < 0 else args.mask_pctl

    # do the embed
    nbits = embed_file(
        path_in=args.in_mp3,
        path_out=args.out_mp3,
        payload=payload,
        payload_src=args.payload_path,       # used to capture extension in header
        max_frames=args.frames,
        key=args.key,
        fraction=args.fraction,
        bits_per_frame=args.bits_per_frame,
        mask_percentile=mask_percentile,
        vigenere=args.vigenere,              # NEW: optional Vigenère layer
    )

    print(f"[ok] embedded {nbits} bits ({nbits//8} bytes) into {os.path.basename(args.out_mp3)}")

if __name__ == "__main__":
    main()
