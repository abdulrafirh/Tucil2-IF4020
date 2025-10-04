# mp3lsbsteg/cli/validate_signbits.py
import sys
from mp3lsbsteg.validate.signbits_check import validate_signbits

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m mp3lsbsteg.cli.validate_signbits <file.mp3> [--frames N] [--quiet]")
        return
    path = sys.argv[1]
    n = None
    verbose = True
    if "--frames" in sys.argv:
        try:
            n = int(sys.argv[sys.argv.index("--frames")+1])
        except Exception:
            pass
    if "--quiet" in sys.argv:
        verbose = False

    errs = validate_signbits(path, frames=n, verbose=verbose)
    if errs == 0:
        print("[PASS] sign-bit validation OK.")
    else:
        print(f"[FAIL] errors={errs}")

if __name__ == "__main__":
    main()
