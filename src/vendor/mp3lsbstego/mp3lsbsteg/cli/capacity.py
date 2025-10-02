# mp3lsbsteg/cli/capacity.py
import sys
from mp3lsbsteg.stego.embed import estimate_capacity

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m mp3lsbsteg.cli.capacity <file.mp3> [--frames N] [--fraction F] [--bits-per-frame N]")
        return
    path = sys.argv[1]
    max_frames = None
    fraction = 1.0
    bpf = None

    if "--frames" in sys.argv:
        i = sys.argv.index("--frames")
        if i+1 < len(sys.argv): max_frames = int(sys.argv[i+1])
    if "--fraction" in sys.argv:
        i = sys.argv.index("--fraction")
        if i+1 < len(sys.argv): fraction = float(sys.argv[i+1])
    if "--bits-per-frame" in sys.argv:
        i = sys.argv.index("--bits-per-frame")
        if i+1 < len(sys.argv): bpf = int(sys.argv[i+1])

    cap = estimate_capacity(path, max_frames=max_frames, fraction=fraction, bits_per_frame=bpf)
    print(f"[capacity] {cap} bits ({cap//8} bytes)  fraction={fraction}  bits_per_frame={bpf}")
    if max_frames is not None:
        print(f"[note] limited to first {max_frames} frames")

if __name__ == "__main__":
    main()
