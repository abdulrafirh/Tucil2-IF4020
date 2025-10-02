# mp3lsbsteg/cli/check_frames.py
import sys
from mp3lsbsteg.mpeg.stream import iter_frames
from mp3lsbsteg.validate.ffprobe_check import cross_check

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m mp3lsbsteg.cli.check_frames <file.mp3> [--ffprobe]")
        return
    path = sys.argv[1]
    with open(path, "rb") as f:
        data = f.read()
    frames = iter_frames(data)
    print(f"[parser] frames={len(frames)}")
    if frames:
        print(f"[parser] first 5: {frames[:5]}")
    if "--ffprobe" in sys.argv:
        cross_check(path)

if __name__ == "__main__":
    main()
