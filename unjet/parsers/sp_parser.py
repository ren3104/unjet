import struct
from pathlib import Path
from typing import NamedTuple
import json


class SpHeader(NamedTuple):
    count: int


class ParserSP:
    TYPE_CODE = "SP"

    HEADER_FORMAT = "<2sH"
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    OLD_RECORD_FORMAT = "<hhH"
    OLD_RECORD_SIZE = struct.calcsize(OLD_RECORD_FORMAT)
    NEW_RECORD_FORMAT = "<hhI"
    NEW_RECORD_SIZE = struct.calcsize(NEW_RECORD_FORMAT)

    OLD_UNKNOWN_COUNT = 2  # v1 uses count + 2

    @classmethod
    def parse_header(cls, data: bytes) -> SpHeader:
        if len(data) < cls.HEADER_SIZE:
            raise ValueError(f"data too small: {len(data)} bytes")

        _, count = struct.unpack_from(cls.HEADER_FORMAT, data)
        return SpHeader(count)

    @classmethod
    def calc_data_size(cls, data: bytes) -> int:
        # Only used for v0 archives, so the old (6-byte record) layout applies.
        header = cls.parse_header(data)
        return (
            cls.HEADER_SIZE
            + header.count * cls.OLD_RECORD_SIZE
            + cls.OLD_UNKNOWN_COUNT * 4
        )

    @classmethod
    def parse_resource(cls, data: bytes, outp: Path, version: int) -> Path:
        if version not in (0, 1):
            raise ValueError(f"unsupported data version: {version}")

        old_version = version == 0

        view = memoryview(data)
        header = cls.parse_header(view)

        if old_version:
            record_format, record_size = cls.OLD_RECORD_FORMAT, cls.OLD_RECORD_SIZE
        else:
            record_format, record_size = cls.NEW_RECORD_FORMAT, cls.NEW_RECORD_SIZE

        offset = cls.HEADER_SIZE
        records = {"unknown": []}
        for _ in range(header.count):
            x, y, im_file = struct.unpack_from(record_format, view, offset)
            offset += record_size
            records[im_file] = (x, y)

        # trailing unknown array
        unknown_count = cls.OLD_UNKNOWN_COUNT if old_version else header.count + 2
        for _ in range(unknown_count):
            value = struct.unpack_from("<I", view, offset)[0]
            offset += 4
            records["unknown"].append(value)

        target_path = outp.with_name(f"{outp.stem}.json")
        target_path.write_text(json.dumps(records))

        return target_path
