from dataclasses import dataclass
import struct

from .constants import JET_V1_HEADER_FORMAT
from .helpers import base38_encode


@dataclass
class JetHeader:
    total_size: int
    part_size: int
    relative_data_end: int
    resource_id: str
    part_index: int
    type_code: bytes

    @classmethod
    def from_bytes(cls, raw: bytes) -> "JetHeader":
        total_sz, part_sz, data_end, rid, part_idx, tcode = struct.unpack(
            JET_V1_HEADER_FORMAT, raw)
        rid = base38_encode(rid)
        return cls(total_sz, part_sz, data_end, rid, part_idx, tcode)


@dataclass
class JetInfo:
    pos: int
    data_start: int
    data_end: int
    header: JetHeader
