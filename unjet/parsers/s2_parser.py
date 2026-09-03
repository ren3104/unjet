import struct
from pathlib import Path
from typing import NamedTuple
import json

from ..helpers import base38_decode


class S2Header(NamedTuple):
    block_count: int


class ParserS2:
    TYPE_CODE = "S2"

    HEADER_SIZE = 42

    COUNT_FORMAT = "<I"
    BLOCK_FORMAT = "<Q2i"
    BLOCK_SIZE = struct.calcsize(BLOCK_FORMAT)

    @classmethod
    def parse_header(cls, data: bytes) -> S2Header:
        if len(data) < cls.HEADER_SIZE:
            raise ValueError(f"data too small: {len(data)} bytes")

        block_count = struct.unpack_from(cls.COUNT_FORMAT, data, cls.HEADER_SIZE)[0]
        return S2Header(block_count)

    @classmethod
    def parse_resource(cls, data: bytes, outp: Path, version: int) -> Path:
        if version not in (0, 1):
            raise ValueError(f"unsupported data version: {version}")

        view = memoryview(data)
        header = cls.parse_header(view)

        offset = cls.HEADER_SIZE + struct.calcsize(cls.COUNT_FORMAT)
        blocks = {}
        for _ in range(header.block_count):
            i2_id, x, y = struct.unpack_from(cls.BLOCK_FORMAT, view, offset)
            offset += cls.BLOCK_SIZE
            blocks[base38_decode(i2_id)] = (x, y)

        target_path = outp.with_name(f"{outp.stem}.json")
        target_path.write_text(json.dumps(blocks))

        return target_path
