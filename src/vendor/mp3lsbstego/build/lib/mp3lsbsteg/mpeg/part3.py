# mp3lsbsteg/mpeg/part3.py
from typing import List, Tuple
from mp3lsbsteg.io.bitreader import BitReader
from mp3lsbsteg.mpeg.huffman import (
    _decode_bigvalues_pair,
    _decode_count1_quad_fixed,
    _decode_count1_quad_huff,
)
from mp3lsbsteg.mpeg import tables as T

def _region_boundaries_samples(fs_hz: int, r0_count: int, r1_count: int) -> Tuple[int, int]:
    if fs_hz == 44100:
        idx = T.band_index_table.long_44
    elif fs_hz == 48000:
        idx = T.band_index_table.long_48
    elif fs_hz == 32000:
        idx = T.band_index_table.long_32
    else:
        idx = T.band_index_table.long_44
    r0 = 2 * idx[r0_count + 1]
    r1 = 2 * idx[r0_count + r1_count + 2]
    return r0, r1

def extract_signbits_for_window(
    blob: bytes,
    start_bit: int,
    length_bits: int,
    fs_hz: int,
    table_select: List[int],        # length 3
    region0_count: int,
    region1_count: int,
    big_value: int,
    count1table_select: int,
) -> List[int]:
    """
    Full extractor: return all sign-bit absolute positions inside [start_bit, start_bit+length_bits).
    Stabilization rules:
      • Reserve the final 3 bits of the part-3 window (effective end = end_bit − 3).
      • Never break when a code’s sign would cross the end; skip out-of-range signs and continue.
    """
    br = BitReader(blob, start_bit)
    end_bit = start_bit + length_bits
    eff_end = max(start_bit, end_bit - 3)  # safety tail

    frame_signs: List[int] = []

    # ===== big_values =====
    r0, r1 = _region_boundaries_samples(fs_hz, region0_count, region1_count)
    sample = 0
    while sample < big_value * 2 and br.tell() < eff_end:
        if sample < r0:
            tbl = table_select[0]
        elif sample < r1:
            tbl = table_select[1]
        else:
            tbl = table_select[2]

        _x, _y, signs = _decode_bigvalues_pair(br, tbl)
        for p in signs:
            if p < eff_end:
                frame_signs.append(p)
        sample += 2

    # ===== count1 =====
    while br.tell() < eff_end and (sample + 4) < 576:
        if count1table_select == 1 and br.tell() + 4 > eff_end:
            break
        if count1table_select == 1:
            _vals, signs = _decode_count1_quad_fixed(br)
        else:
            _vals, signs = _decode_count1_quad_huff(br)
        for p in signs:
            if p < eff_end:
                frame_signs.append(p)
        sample += 4

    return frame_signs


def extract_signbits_count1_fixed(
    blob: bytes,
    start_bit: int,
    length_bits: int,
    fs_hz: int,
    count1table_select: int,
) -> List[int]:
    """
    SAFE extractor: only sign-bit absolute positions from the count1 **fixed** region.
    If the frame/granule uses the Huffman-coded count1 table (select=0), this returns [].

    Stabilization rules:
      • Reserve the final 3 bits of the part-3 window (effective end = end_bit − 3).
      • Skip any out-of-range signs; never rely on the boundary bit.
    """
    if count1table_select != 1:
        return []

    br = BitReader(blob, start_bit)
    end_bit = start_bit + length_bits
    eff_end = max(start_bit, end_bit - 3)

    signs_out: List[int] = []
    sample = 0
    # We don't know how many samples were consumed by big_values here;
    # the caller should start us at the correct count1 window (i.e., p3_start + part2_bits + bigvalues bits).
    # In our pipeline we feed the whole part3 window; but the fixed path ignores bigvalues and will just
    # decode valid fixed quads in the tail.
    while br.tell() < eff_end and (sample + 4) < 576:
        if br.tell() + 4 > eff_end:
            break
        _vals, signs = _decode_count1_quad_fixed(br)
        for p in signs:
            if p < eff_end:
                signs_out.append(p)
        sample += 4

    return signs_out
