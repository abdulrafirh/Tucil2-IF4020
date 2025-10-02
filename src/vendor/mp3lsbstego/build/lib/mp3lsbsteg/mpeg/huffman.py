# mp3lsbsteg/mpeg/huffman.py
from typing import List, Tuple
from mp3lsbsteg.io.bitreader import BitReader
from mp3lsbsteg.mpeg import tables as T

def _get_bits_abs(br: BitReader, n: int) -> Tuple[int, int]:
    """Return (value, bitpos_before) and advance."""
    pos = br.tell()
    val = br.read_bits(n)
    return val, pos

def _peek32(br: BitReader) -> int:
    """Peek 32 bits (pad with zeros if near EOF) without advancing."""
    pos = br.tell()
    need = 32
    out = 0
    # Temporary local reads
    for _ in range(need):
        byte_i = br.pos >> 3
        bit_i = 7 - (br.pos & 7)
        if br.pos >= br._n_bits:
            bit = 0
        else:
            bit = (br._b[byte_i] >> bit_i) & 1
        out = (out << 1) | bit
        br.pos += 1
    br.pos = pos
    return out

def _decode_bigvalues_pair(br: BitReader, table_num: int) -> Tuple[int, int, List[int]]:
    """
    Decode one (x,y) from the 'big values' region using table `table_num`.
    Return (x, y, sign_bit_positions).
    """
    if table_num == 0:
        return 0, 0, []  # table 0 carries no data

    table = T.big_value_table[table_num]
    vmax  = T.big_value_max[table_num]
    linb  = T.big_value_linbit[table_num]
    sign_pos: List[int] = []

    bits32 = _peek32(br)

    # Tables are laid out like in your old Frame.py: entries in row-major
    # i = 2 * vmax * row + 2 * col  ->  (code, length) at i,i+1
    hit = None
    for row in range(vmax):
        base = 2 * vmax * row
        for col in range(vmax):
            i = base + 2 * col
            code = table[i]
            size = table[i + 1]
            if size == 0:  # safety
                continue
            if (code >> (32 - size)) == (bits32 >> (32 - size)):
                # match
                br.read_bits(size)  # consume
                x, y = row, col

                # linbits for max symbol(s)
                if linb and x == (vmax - 1):
                    _, _ = _get_bits_abs(br, linb)  # we don't store linbits; sign bits only
                if x > 0:
                    _, spos = _get_bits_abs(br, 1)
                    sign_pos.append(spos)

                if linb and y == (vmax - 1):
                    _, _ = _get_bits_abs(br, linb)
                if y > 0:
                    _, spos = _get_bits_abs(br, 1)
                    sign_pos.append(spos)

                hit = (x, y)
                break
        if hit is not None:
            break

    if hit is None:
        # If no code matched (corrupt stream or unexpected table), bail gracefully:
        # consume one bit to avoid infinite loop and move on.
        br.read_bits(1)
        return 0, 0, []

    return hit[0], hit[1], sign_pos

def _decode_count1_quad_fixed(br: BitReader) -> Tuple[List[int], List[int]]:
    """
    count1table_select == 1 path: 4-bit immediate pattern => 4 values in {0,1}.
    Returns (values[4], sign_bit_positions).
    """
    nibble, _ = _get_bits_abs(br, 4)
    vals = [
        0 if (nibble & 0x8) else 1,
        0 if (nibble & 0x4) else 1,
        0 if (nibble & 0x2) else 1,
        0 if (nibble & 0x1) else 1,
    ]
    signs: List[int] = []
    for v in vals:
        if v != 0:
            _, spos = _get_bits_abs(br, 1)
            signs.append(spos)
    return vals, signs

def _decode_count1_quad_huff(br: BitReader) -> Tuple[List[int], List[int]]:
    """
    count1table_select == 0 path: use quad_table_1 (h_cod/h_len/value).
    Returns (values[4], sign_bit_positions).
    """
    bits32 = _peek32(br)
    vals = [0, 0, 0, 0]
    signs: List[int] = []
    # 16 entries
    for entry in range(16):
        code = T.quad_table_1.h_cod[entry]
        size = T.quad_table_1.h_len[entry]
        if (code >> (32 - size)) == (bits32 >> (32 - size)):
            br.read_bits(size)
            vals = T.quad_table_1.value[entry].copy()
            for v in vals:
                if v != 0:
                    _, spos = _get_bits_abs(br, 1)
                    signs.append(spos)
            return vals, signs
    # Fallback if nothing matched
    br.read_bits(1)
    return vals, signs
