# mp3lsbsteg/io/bitwriter.py
class BitWriter:
    """In-place bit writer over a mutable bytearray."""
    __slots__ = ("buf", "n_bits")
    def __init__(self, b: bytearray):
        self.buf = b
        self.n_bits = len(b) * 8

    def flip_bit(self, bitpos: int):
        if not (0 <= bitpos < self.n_bits):
            raise ValueError("flip out of range")
        byte_i = bitpos >> 3
        bit_i  = 7 - (bitpos & 7)
        self.buf[byte_i] ^= (1 << bit_i)

    def set_bit(self, bitpos: int, value: int):
        if not (0 <= bitpos < self.n_bits):
            raise ValueError("set out of range")
        byte_i = bitpos >> 3
        bit_i  = 7 - (bitpos & 7)
        mask = (1 << bit_i)
        if value:
            self.buf[byte_i] |= mask
        else:
            self.buf[byte_i] &= ~mask

    def set_bit_value(self, bit_index: int, value: int) -> None:
        """
        Set the bit at absolute bit index to 0 or 1 explicitly.
        - bit_index 0 means the MSB of buf[0].
        """
        byte_index = bit_index >> 3                # bit_index // 8
        bit_in_byte = 7 - (bit_index & 7)         # MSB-first: 7..0
        mask = 1 << bit_in_byte
        if value & 1:
            self.buf[byte_index] |= mask          # force to 1
        else:
            self.buf[byte_index] &= ~mask         # force to 0
