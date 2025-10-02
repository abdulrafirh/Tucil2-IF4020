# mp3lsbsteg/io/bitreader.py
from typing import Union

class BitReader:
    """
    MSB-first bit reader with backward-compatible constructor:
      BitReader(buf)                  -> start at bit 0
      BitReader(buf, start_bit)       -> start at bit start_bit
    Absolute bit index 0 refers to the MSB of buf[0].
    """
    def __init__(self, buf: Union[bytes, bytearray], start_bit: int = 0):
        self.buf = buf if isinstance(buf, (bytes, bytearray)) else bytes(buf)
        self._pos = int(start_bit)

    def seek(self, bit_index: int) -> None:
        self._pos = int(bit_index)

    def tell(self) -> int:
        return self._pos

    def read_bits(self, n: int) -> int:
        """
        Read n bits MSB-first and return as an int.
        Bit position i uses bit_in_byte = 7 - (i & 7) to match BitWriter.set_bit_value.
        """
        v = 0
        pos = self._pos
        max_bits = len(self.buf) * 8
        if n < 0:
            raise ValueError("n must be >= 0")
        if pos < 0 or pos + n > max_bits:
            raise EOFError("BitReader: attempt to read beyond buffer")

        for _ in range(n):
            byte_index = pos >> 3             # pos // 8
            bit_in_byte = 7 - (pos & 7)       # MSB-first
            v = (v << 1) | ((self.buf[byte_index] >> bit_in_byte) & 1)
            pos += 1
        self._pos = pos
        return v
