# mp3lsbsteg/cli/extract_auto.py
import os
import sys
import argparse

from mp3lsbsteg.stego.embed import extract_file_auto

def main():
    ap = argparse.ArgumentParser(
        description="Extract stego payload from MP3 using auto length (magic+size+extension)."
    )
    ap.add_argument("in_mp3", help="Input MP3 with embedded payload")
    ap.add_argument("out_path", help="Output path (extension added if header provides one and none given)")
    ap.add_argument("--bits-per-frame", type=int, default=None, help="Max bits to read per frame (must match embed)")
    ap.add_argument("--fraction", type=float, default=1.0, help="Use only this fraction of candidates (must match embed)")
    ap.add_argument("--key", default=None, help="Key used during embedding (must match embed)")
    ap.add_argument("--mask-pctl", type=float, default=0.60,
                    help="Global-gain percentile [0..1]; use -1 to disable (must match embed)")
    ap.add_argument("--frames", type=int, default=None, help="Optional limit on number of frames to scan")
    ap.add_argument("--vigenere", action="store_true",
                    help="Apply repeating-key XOR to payload bytes before embedding")
    args = ap.parse_args()

    if not os.path.exists(args.in_mp3):
        print(f"[ERR] input not found: {args.in_mp3}", file=sys.stderr)
        sys.exit(2)

    mask_percentile = None if args.mask_pctl < 0 else args.mask_pctl

    try:
        data, ext = extract_file_auto(
            path_in=args.in_mp3,
            max_frames=args.frames,
            key=args.key,
            fraction=args.fraction,
            bits_per_frame=args.bits_per_frame,
            mask_percentile=mask_percentile,
            vigenere=args.vigenere,
        )
    except Exception as e:
        print(f"[ERR] extraction failed: {e}", file=sys.stderr)
        sys.exit(1)

    # If no extension in the provided out_path and header gives one, append it
    out_path = args.out_path
    has_ext = bool(os.path.splitext(out_path)[1])
    if ext and not has_ext:
        out_path = f"{out_path}.{ext}"

    # Ensure parent directory exists
    parent = os.path.dirname(os.path.abspath(out_path))
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)

    with open(out_path, "wb") as f:
        f.write(data)

    print(f"[ok] extracted {len(data)} bytes to {out_path}")

if __name__ == "__main__":
    main()
