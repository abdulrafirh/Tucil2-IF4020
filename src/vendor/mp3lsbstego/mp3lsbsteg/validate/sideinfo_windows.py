# mp3lsbsteg/validate/sideinfo_windows.py
from typing import Tuple
from mp3lsbsteg.mpeg.stream import iter_frames_with_windows, _parse_header_basic
from mp3lsbsteg.mpeg.sideinfo import parse_sideinfo, sideinfo_bytes
from mp3lsbsteg.io.bitreader import BitReader

def hexdump(b: bytes, maxlen=32):
    s = b[:maxlen].hex()
    return " ".join(s[i:i+2] for i in range(0, len(s), 2))

def validate_windows(path: str, verbose: bool = True) -> int:
    with open(path, "rb") as fh:
        blob = fh.read()

    errs = 0
    for idx, fw in enumerate(iter_frames_with_windows(blob)):
        hb = _parse_header_basic(blob[fw.offset:fw.offset+4])
        si = parse_sideinfo(blob, fw.offset, hb["version_id"], hb["channels"], hb["has_crc"])

        # Where we think side-info starts (bytes)
        si_byte_off = fw.offset + 4 + (2 if hb["has_crc"] else 0)
        si_len_bytes = sideinfo_bytes(hb["version_id"], hb["channels"])

        if verbose and idx < 2:
            print(f"[frame {idx}] off={fw.offset} size={fw.size} avail_main_bits={fw.available_main_bits}")
            print(f"  version_id={hb['version_id']} channels={hb['channels']} has_crc={hb['has_crc']}")
            print(f"  sideinfo @ byte {si_byte_off} (len {si_len_bytes} bytes)  main_data_begin={si.main_data_begin}")
            print(f"  sideinfo hex: {hexdump(blob[si_byte_off:si_byte_off+si_len_bytes], 48)}")

        # re-read just the first few side-info fields directly to verify cursor
        if verbose and idx < 2:
            br = BitReader(blob, si_byte_off * 8)
            mpeg1 = (hb["version_id"] == 3)
            mdb = br.read_bits(9 if mpeg1 else 8)
            # private bits
            if mpeg1 and hb["channels"] == 2:
                _ = br.read_bits(3)
            elif mpeg1 and hb["channels"] == 1:
                _ = br.read_bits(5)
            elif not mpeg1 and hb["channels"] == 2:
                _ = br.read_bits(2)
            else:
                _ = br.read_bits(1)
            if mpeg1:
                scfsi0 = [br.read_bits(1) for _ in range(4)]
                scfsi1 = [br.read_bits(1) for _ in range(4)] if hb["channels"] == 2 else []
            # peek first granule/channel part2_3_length
            p231 = br.read_bits(12)
            print(f"  [debug] re-read main_data_begin={mdb} first part2_3_length(bits)={p231}")

        # formal window checks
        ngr = 2 if hb["version_id"] == 3 else 1
        for g in range(ngr):
            for ch in range(hb["channels"]):
                start, end = fw.windows[g][ch]
                L = si.granules[g][ch].part2_3_length
                if end - start != L:
                    errs += 1
                    if verbose:
                        print(f"[len-mismatch] frame={idx} g={g} ch={ch} window={end-start} vs part2_3_length={L}")

        flat = [fw.windows[g][ch] for g in range(ngr) for ch in range(hb["channels"])]
        for i in range(1, len(flat)):
            if flat[i][0] < flat[i-1][1]:
                errs += 1
                if verbose:
                    print(f"[overlap] frame={idx} seg{i-1}={flat[i-1]} seg{i}={flat[i]}")

        if verbose and idx < 2:
            for g in range(ngr):
                for ch in range(hb["channels"]):
                    s,e = fw.windows[g][ch]
                    print(f"  g{g} ch{ch}: [{s},{e}) bits ({e-s} bits)")

    if errs == 0 and verbose:
        print("[ok] all per-granule/ch windows match part2_3_length and order.")
    return errs

def dump_lengths(path: str, frames_to_show: int = 3):
    """Print raw per-(granule,channel) part2_3_length for the first few frames."""
    from mp3lsbsteg.mpeg.stream import iter_frames_with_windows, _parse_header_basic
    from mp3lsbsteg.mpeg.sideinfo import parse_sideinfo

    with open(path, "rb") as fh:
        blob = fh.read()

    print("[debug] first frames part2_3_length (bits):")
    shown = 0
    for idx, fw in enumerate(iter_frames_with_windows(blob)):
        hb = _parse_header_basic(blob[fw.offset:fw.offset+4])
        si = parse_sideinfo(blob, fw.offset, hb["version_id"], hb["channels"], hb["has_crc"])
        ngr = 2 if hb["version_id"] == 3 else 1
        row = []
        for g in range(ngr):
            for ch in range(hb["channels"]):
                row.append(si.granules[g][ch].part2_3_length)
        print(f"  frame {idx} @ {fw.offset}, mdb={si.main_data_begin}, lengths={row}")
        shown += 1
        if shown >= frames_to_show:
            break
