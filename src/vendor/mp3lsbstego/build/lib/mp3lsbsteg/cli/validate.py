# mp3lsbsteg/cli/validate.py
import sys
from mp3lsbsteg.validate.sideinfo_windows import validate_windows, dump_lengths

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m mp3lsbsteg.cli.validate <file.mp3>")
        return
    path = sys.argv[1]

    # 1) dump the first few frames' side-info lengths (raw)
    dump_lengths(path, frames_to_show=3)

    # 2) run the structural window validator
    errs = validate_windows(path, verbose=True)
    if errs == 0:
        print("[PASS] side-info windows look correct.")
    else:
        print(f"[FAIL] errors={errs}")

if __name__ == "__main__":
    main()
