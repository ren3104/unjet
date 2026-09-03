import struct
from pathlib import Path
from typing import NamedTuple

from PIL import Image


class I2Header(NamedTuple):
    width: int
    height: int
    table_a_len: int
    table_b_len: int
    rmpot_count: int


class ParserI2:
    TYPE_CODE = "I2"

    HEADER_FORMAT = "<2sI9f7I"
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    RMPOT_FORMAT = "<5s6I"
    RMPOT_SIZE = struct.calcsize(RMPOT_FORMAT)

    @classmethod
    def parse_header(cls, data: bytes) -> I2Header:
        if len(data) < cls.HEADER_SIZE:
            raise ValueError(f"data too small: {len(data)} bytes")

        # skip magic (2s) and a leading uint (?); the rest is 9 floats + 7 uints
        fields = struct.unpack_from(cls.HEADER_FORMAT, data)[2:]
        return I2Header(
            width=fields[9],
            height=fields[10],
            table_a_len=fields[13],
            table_b_len=fields[14],
            rmpot_count=fields[15],
        )

    @classmethod
    def parse_resource(cls, data: bytes, outp: Path, version: int) -> Path:
        if version not in (0, 1):
            raise ValueError(f"unsupported data version: {version}")

        view = memoryview(data)
        header = cls.parse_header(view)

        offset = cls.HEADER_SIZE
        offset += header.table_a_len * 4  # table_a (skipped)
        offset += header.table_b_len * 4  # table_b (skipped)

        rmpot = []
        for _ in range(header.rmpot_count):
            w_alloc, h_alloc, w, h, x, y = struct.unpack_from(
                cls.RMPOT_FORMAT, view, offset)[1:]
            rmpot.append((w_alloc, h_alloc, w, h, x, y))
            offset += cls.RMPOT_SIZE

        canvas = Image.new("RGBA", (header.width, header.height))
        for w_alloc, h_alloc, w, h, x, y in rmpot:
            size = w_alloc * h_alloc * 4
            block = Image.frombuffer(
                "RGBA", (w_alloc, h_alloc), view[offset:offset + size])
            canvas.paste(block.crop((0, 0, w, h)), (x, y))
            offset += size

        target_path = outp.with_name(f"{outp.stem}.png")
        canvas.save(target_path)

        return target_path
