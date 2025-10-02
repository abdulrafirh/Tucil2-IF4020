# mp3stego_min/mpeg/header.py
import struct

BITRATES = {
    (3, 1): [None, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, None],
    (3, 2): [None, 32, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 384, None],
    (3, 3): [None, 32, 64, 96, 128, 160, 192, 224, 256, 288, 320, 352, 384, 416, 448, None],
    (2, 1): [None, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, None],
    (2, 2): [None, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, None],
    (2, 3): [None, 32, 48, 56, 64, 80, 96, 112, 128, 144, 160, 176, 192, 224, 256, None],
    (0, 1): [None, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, None],
    (0, 2): [None, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, None],
    (0, 3): [None, 32, 48, 56, 64, 80, 96, 112, 128, 144, 160, 176, 192, 224, 256, None],
}
SAMPLERATES = {3: [44100, 48000, 32000, None],
               2: [22050, 24000, 16000, None],
               0: [11025, 12000, 8000,  None]}

def parse_header(b: bytes):
    if len(b) < 4: return None
    b1, b2, b3, b4 = struct.unpack(">BBBB", b)
    if b1 != 0xFF or (b2 & 0xE0) != 0xE0:
        return None
    version_id = (b2 >> 3) & 0x03
    layer_id   = (b2 >> 1) & 0x03
    prot_bit   =  b2 & 0x01
    br_idx     = (b3 >> 4) & 0x0F
    sr_idx     = (b3 >> 2) & 0x03
    pad_bit    = (b3 >> 1) & 0x01
    ch_mode    = (b4 >> 6) & 0x03

    if version_id == 1 or layer_id == 0:
        return None

    bitrate_kbps = BITRATES.get((version_id, layer_id), [None]*16)[br_idx]
    sr = SAMPLERATES.get(version_id, [None]*4)[sr_idx]
    if bitrate_kbps is None or sr is None:
        return None

    if layer_id == 3:  # Layer I
        length = int((12 * bitrate_kbps * 1000 / sr + pad_bit) * 4)
    else:
        factor = 144 if version_id == 3 else 72
        length = int(factor * bitrate_kbps * 1000 / sr + pad_bit)

    return {
        "frame_length": length,
        "samplerate": sr,
        "bitrate": bitrate_kbps * 1000,
        "channels": 1 if ch_mode == 3 else 2,
    }

def parse_header_basic(b: bytes):
    import struct
    if len(b) < 4: return None
    b1,b2,b3,b4 = struct.unpack(">BBBB", b)
    if b1 != 0xFF or (b2 & 0xE0) != 0xE0: return None
    version_id = (b2 >> 3) & 0x03      # 00=2.5,10=2,11=1
    layer_id   = (b2 >> 1) & 0x03
    prot_bit   =  b2       & 0x01
    ch_mode    = (b4 >> 6) & 0x03      # 3 = mono
    return {"version_id": version_id, "layer_id": layer_id, "has_crc": (prot_bit==0), "channels": 1 if ch_mode==3 else 2}

def sideinfo_bytes(version_id: int, channels: int) -> int:
    # MPEG-1: 32 (stereo), 17 (mono);  MPEG-2/2.5: 17 (stereo), 9 (mono)
    if version_id == 3:  # MPEG-1
        return 17 if channels == 1 else 32
    else:                # MPEG-2 or 2.5
        return 9 if channels == 1 else 17