# mp3lsbsteg/mpeg/sideinfo.py
from dataclasses import dataclass, field
from typing import List
from mp3lsbsteg.io.bitreader import BitReader

# Side-info byte lengths (bytes)
def sideinfo_bytes(version_id: int, channels: int) -> int:
    # version_id: 3=MPEG1, 2=MPEG2, 0=MPEG2.5 ; channels: 1 mono, 2 stereo
    if version_id == 3:  # MPEG-1
        return 17 if channels == 1 else 32
    else:                # MPEG-2 / 2.5
        return 9 if channels == 1 else 17

@dataclass
class GranuleCH:
    part2_3_length: int
    big_values: int
    global_gain: int
    scalefac_compress: int
    window_switching_flag: int
    block_type: int
    mixed_block_flag: int
    table_select: List[int]
    subblock_gain: List[int]
    region0_count: int
    region1_count: int
    preflag: int
    scalefac_scale: int
    count1table_select: int

@dataclass
class SideInfo:
    main_data_begin: int
    scfsi: List[List[int]]        # [ch][4]
    granules: List[List[GranuleCH]]  # [granule][ch]
    sideinfo_bits: int            # total side-info length in bits (for this frame)

def _read_granule_ch(br: BitReader, mpeg1: bool) -> GranuleCH:
    part2_3_length      = br.read_bits(12)
    big_values          = br.read_bits(9)
    global_gain         = br.read_bits(8)
    scalefac_compress   = br.read_bits(4 if mpeg1 else 9)

    window_switching_flag = br.read_bits(1)
    if window_switching_flag:
        block_type        = br.read_bits(2)
        mixed_block_flag  = br.read_bits(1)
        table_select      = [br.read_bits(5), br.read_bits(5), 0]  # only 2 used
        subblock_gain     = [br.read_bits(3), br.read_bits(3), br.read_bits(3)]
        region0_count     = 0
        region1_count     = 0
    else:
        block_type        = 0
        mixed_block_flag  = 0
        table_select      = [br.read_bits(5), br.read_bits(5), br.read_bits(5)]
        region0_count     = br.read_bits(4)
        region1_count     = br.read_bits(3)
        subblock_gain     = [0, 0, 0]

    preflag           = br.read_bits(1) if mpeg1 else 0
    scalefac_scale    = br.read_bits(1)
    count1table_select = br.read_bits(1)

    return GranuleCH(
        part2_3_length, big_values, global_gain, scalefac_compress,
        window_switching_flag, block_type, mixed_block_flag,
        table_select, subblock_gain, region0_count, region1_count,
        preflag, scalefac_scale, count1table_select
    )

def parse_sideinfo(frame_bytes: bytes, frame_off: int, version_id: int, channels: int, has_crc: bool) -> SideInfo:
    """
    Parse side info from a single frame.
    frame_bytes: full file bytes (so BitReader absolute positions make sense)
    frame_off: byte offset of frame start in file
    """
    mpeg1 = (version_id == 3)
    si_bytes = sideinfo_bytes(version_id, channels)
    # header (4) + optional CRC (2) precede side-info
    start = (frame_off + 4 + (2 if has_crc else 0)) * 8  # absolute bit pos
    br = BitReader(frame_bytes, start)

    main_data_begin = br.read_bits(9 if mpeg1 else 8)
    # private bits (varies with channels/version)
    if mpeg1 and channels == 2:
        _ = br.read_bits(3)
    elif mpeg1 and channels == 1:
        _ = br.read_bits(5)
    elif not mpeg1 and channels == 2:
        _ = br.read_bits(2)
    else:
        _ = br.read_bits(1)

    # scfsi (only MPEG-1)
    scfsi = [[0,0,0,0] for _ in range(channels)]
    if mpeg1:
        for ch in range(channels):
            scfsi[ch] = [br.read_bits(1) for _ in range(4)]

    # granules
    ngr = 2 if mpeg1 else 1
    granules: List[List[GranuleCH]] = []
    for g in range(ngr):
        row: List[GranuleCH] = []
        for ch in range(channels):
            row.append(_read_granule_ch(br, mpeg1))
        granules.append(row)

    sideinfo_bits = si_bytes * 8
    return SideInfo(main_data_begin, scfsi, granules, sideinfo_bits)