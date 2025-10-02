# mp3lsbsteg/validate/signbits_check.py
from typing import List, Tuple
from mp3lsbsteg.mpeg.stream import iter_frames_with_windows, _parse_header_basic
from mp3lsbsteg.mpeg.sideinfo import parse_sideinfo
from mp3lsbsteg.mpeg.header import parse_header
from mp3lsbsteg.mpeg.part3 import extract_signbits_for_window
from mp3lsbsteg.mpeg import tables as T

def _part2_bits_mpeg1_long(scalefac_compress: int, scfsi_ch: List[int], gr: int) -> int:
    slen1, slen2 = T.slen[scalefac_compress]
    if gr == 0:
        return 11 * slen1 + 10 * slen2
    total = 0
    total += 0 if scfsi_ch[0] else (6 * slen1)  # sfb 0..5
    total += 0 if scfsi_ch[1] else (5 * slen1)  # sfb 6..10
    total += 0 if scfsi_ch[2] else (5 * slen2)  # sfb 11..15
    total += 0 if scfsi_ch[3] else (5 * slen2)  # sfb 16..20
    return total

def _part2_bits_mpeg1_short(scalefac_compress: int, mixed_block_flag: bool) -> int:
    slen1, slen2 = T.slen[scalefac_compress]
    if mixed_block_flag:
        return 8 * slen1 + 3 * 3 * slen1 + 3 * 6 * slen2
    else:
        return 3 * 6 * slen1 + 3 * 6 * slen2

def _part2_bits(version_id: int, gr: int, ch: int, si) -> int:
    # MPEG-1 only for now (matches your test file)
    if version_id != 3:
        return 0
    gch = si.granules[gr][ch]
    if gch.window_switching_flag and gch.block_type == 2:
        return _part2_bits_mpeg1_short(int(gch.scalefac_compress), bool(gch.mixed_block_flag))
    else:
        return _part2_bits_mpeg1_long(int(gch.scalefac_compress), list(si.scfsi[ch]), gr)

def validate_signbits(path: str, frames: int | None = None, max_errors: int = 20, verbose: bool = True) -> int:
    """
    Validate sign-bit extraction:
      - offsets inside part3 windows
      - monotonic order within each (g,ch)
    Returns number of errors found.
    """
    errs = 0
    with open(path, "rb") as fh:
        blob = fh.read()

    for fi, fw in enumerate(iter_frames_with_windows(blob)):
        if frames is not None and fi >= frames:
            break

        hb = _parse_header_basic(blob[fw.offset:fw.offset+4])
        si = parse_sideinfo(blob, fw.offset, hb["version_id"], hb["channels"], hb["has_crc"])
        hdr_more = parse_header(blob[fw.offset:fw.offset+4])
        fs_hz = hdr_more["samplerate"]
        ngr = 2 if hb["version_id"] == 3 else 1

        if verbose:
            print(f"[frame {fi}] off={fw.offset} size={fw.size}")

        total_signs = 0
        for g in range(ngr):
            for ch in range(hb["channels"]):
                win_start, win_end = fw.windows[g][ch]
                if win_end <= win_start:
                    if verbose:
                        print(f"  g{g} ch{ch}: empty window")
                    continue

                # part3 window = [win_start + part2_bits, win_end)
                p2 = _part2_bits(hb["version_id"], g, ch, si)
                p3_start = win_start + p2
                p3_end   = win_end
                if p3_start >= p3_end:
                    if verbose:
                        print(f"  g{g} ch{ch}: no part3 (p2={p2}, win=[{win_start},{win_end}))")
                    continue

                gch = si.granules[g][ch]
                signs = extract_signbits_for_window(
                    blob=blob,
                    start_bit=p3_start,
                    length_bits=(p3_end - p3_start),
                    fs_hz=fs_hz,
                    table_select=[int(gch.table_select[0]), int(gch.table_select[1]), int(gch.table_select[2])],
                    region0_count=int(gch.region0_count),
                    region1_count=int(gch.region1_count),
                    big_value=int(gch.big_values),
                    count1table_select=int(gch.count1table_select),
                )

                # Bounds check
                for pos in signs:
                    if not (p3_start <= pos < p3_end):
                        errs += 1
                        if errs <= max_errors:
                            print(f"[ERR] frame {fi} g{g} ch{ch}: sign pos {pos} out of [{p3_start},{p3_end})")
                # Monotonic check
                if any(signs[i] < signs[i-1] for i in range(1, len(signs))):
                    errs += 1
                    if errs <= max_errors:
                        print(f"[ERR] frame {fi} g{g} ch{ch}: sign positions not monotonic")

                if verbose:
                    print(f"  g{g} ch{ch}: part3=[{p3_start},{p3_end}) bits, sign_bits={len(signs)}")

                total_signs += len(signs)

        if verbose:
            print(f"  total sign bits (frame {fi}): {total_signs}")

        if errs > max_errors:
            print(f"[ABORT] too many errors ({errs}).")
            break

    if errs == 0 and verbose:
        print("[ok] sign-bit offsets are within part3 windows and monotonic.")
    return errs
