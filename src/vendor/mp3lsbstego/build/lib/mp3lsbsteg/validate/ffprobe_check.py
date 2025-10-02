# mp3lsbsteg/validate/ffprobe_check.py
import subprocess, json, shutil
from mp3lsbsteg.mpeg.stream import iter_frames

def run_ffprobe(path):
    if not shutil.which("ffprobe"):
        raise RuntimeError("ffprobe not found. Install ffmpeg.")
    out = subprocess.check_output([
        "ffprobe","-v","error","-show_frames",
        "-select_streams","a","-print_format","json",path
    ])
    j = json.loads(out.decode("utf-8","replace"))
    return [f for f in j.get("frames",[]) if f.get("media_type")=="audio"]

def cross_check(path: str):
    with open(path,"rb") as fh: data = fh.read()
    ours = iter_frames(data)
    ffs  = run_ffprobe(path)
    m = min(len(ours), len(ffs))
    mism = 0
    for i in range(m):
        off_o, size_o = ours[i]
        off_f, size_f = int(ffs[i]["pkt_pos"]), int(ffs[i]["pkt_size"])
        if off_o != off_f or size_o != size_f:
            mism += 1
            if mism < 10:
                print(f"[mismatch] idx={i}: ours(off={off_o},size={size_o}) ffprobe(off={off_f},size={size_f})")
    if mism == 0:
        print("[ok] all offsets/sizes match ffprobe.")
    else:
        print(f"[warn] {mism}/{m} mismatches.")
    return mism
