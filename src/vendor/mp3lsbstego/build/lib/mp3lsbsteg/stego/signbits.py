# mp3lsbsteg/stego/signbits.py
from typing import List, Tuple
from mp3lsbsteg.io.bitreader import BitReader
from mp3lsbsteg.mpeg.stream import iter_frames_with_windows, _parse_header_basic
from mp3lsbsteg.mpeg.sideinfo import parse_sideinfo
from mp3lsbsteg.mpeg.part3 import extract_signbits_for_window
from mp3lsbsteg.mpeg import tables as T

def _part2_bits_mpeg1_long(scalefac_compress: int, scfsi_ch: List[int], gr: int) -> int:
    """
    Long blocks (MPEG-1): number of scalefactor bits in PART2.
    slen[scalefac_compress] = (slen1, slen2)
    gr=0: 11*slen1 + 10*slen2
    gr=1: bands reused depending on scfsi flags:
          [0..5]=6*slen1, [6..10]=5*slen1, [11..15]=5*slen2, [16..20]=5*slen2
    """
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
    """
    Short blocks (MPEG-1): PART2 length depends on mixed_block_flag.
    """
    slen1, slen2 = T.slen[scalefac_compress]
    if mixed_block_flag:
        # 8 long (slen1) + (3 windows × sfb 3..5 slen1) + (3 windows × sfb 6..11 slen2)
        return 8 * slen1 + 3 * 3 * slen1 + 3 * 6 * slen2
    else:
        # short-only: (3 windows × sfb 0..5 slen1) + (3 windows × sfb 6..11 slen2)
        return 3 * 6 * slen1 + 3 * 6 * slen2

def _part2_bits(version_id: int, gr: int, ch: int, si) -> int:
    """
    Return PART2 (scalefactors) bitcount for (gr,ch).
    Uses fields from si.granules[gr][ch].
    """
    mpeg1 = (version_id == 3)
    gch = si.granules[gr][ch]

    if not mpeg1:
        # TODO: add MPEG-2/2.5 if needed
        return 0

    if gch.window_switching_flag and gch.block_type == 2:
        return _part2_bits_mpeg1_short(int(gch.scalefac_compress), bool(gch.mixed_block_flag))
    else:
        return _part2_bits_mpeg1_long(int(gch.scalefac_compress), list(si.scfsi[ch]), gr)

def collect_signbits(path: str, frames: int = 3) -> List[List[Tuple[int,int,int]]]:
    """
    Return per-frame list of (g, ch, absolute_bit_position) for all sign bits in the first N frames.
    """
    out: List[List[Tuple[int,int,int]]] = []
    with open(path, "rb") as fh:
        blob = fh.read()

    for fi, fw in enumerate(iter_frames_with_windows(blob)):
        if fi >= frames:
            break

        hb = _parse_header_basic(blob[fw.offset:fw.offset+4])
        si = parse_sideinfo(blob, fw.offset, hb["version_id"], hb["channels"], hb["has_crc"])

        # get samplerate from header parser (we already have offset)
        from mp3lsbsteg.mpeg.header import parse_header
        hdr_more = parse_header(blob[fw.offset:fw.offset+4])
        fs_hz = hdr_more["samplerate"]

        frame_signs: List[Tuple[int,int,int]] = []
        ngr = 2 if hb["version_id"] == 3 else 1
        for g in range(ngr):
            for ch in range(hb["channels"]):
                win_start, win_end = fw.windows[g][ch]
                if win_end <= win_start:
                    continue

                # PART2 (scalefactors) length
                p2_bits = _part2_bits(hb["version_id"], g, ch, si)

                # PART3 (Huffman) window within this (g,ch)
                p3_start = win_start + p2_bits
                p3_len   = max(0, win_end - p3_start)
                if p3_len <= 0:
                    continue

                gch = si.granules[g][ch]
                signs = extract_signbits_for_window(
                    blob=blob,
                    start_bit=p3_start,
                    length_bits=p3_len,
                    fs_hz=fs_hz,
                    table_select=[int(gch.table_select[0]), int(gch.table_select[1]), int(gch.table_select[2])],
                    region0_count=int(gch.region0_count),
                    region1_count=int(gch.region1_count),
                    big_value=int(gch.big_values),
                    count1table_select=int(gch.count1table_select),
                )
                frame_signs.extend((g, ch, pos) for pos in signs)

        out.append(frame_signs)

    return out
