from dataclasses import dataclass
import struct


@dataclass
class SegmentHeader:
    full_size: int
    segment_size: int
    rel_pos_end: int
    file_id: int
    unknown: int
    segment_no: int
    magic: bytes

    @classmethod
    def from_bytes(cls, raw: bytes) -> "SegmentHeader":
        return cls(*struct.unpack("<5IH2s", raw))


@dataclass
class Segment:
    pos: int
    data_start: int
    data_end: int
    header: SegmentHeader
