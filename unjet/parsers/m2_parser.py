import struct
from pathlib import Path
from typing import NamedTuple

from .vn_parser import ParserVN
from ..helpers import guess_file_ext


class M2Header(NamedTuple):
    file_type: int
    file_size: int


class ParserM2:
    TYPE_CODE = "M2"

    HEADER_FORMAT = "<2siI"
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    TYPE_EXTERNAL = -1  # ExternalData
    TYPE_SCRIPT = 0  # ExternalData (Scripts)

    @classmethod
    def parse_header(cls, data: bytes) -> M2Header:
        if len(data) < cls.HEADER_SIZE:
            raise ValueError(f"data too small: {len(data)} bytes")

        _, file_type, file_size = struct.unpack_from(cls.HEADER_FORMAT, data)
        return M2Header(file_type, file_size)

    @classmethod
    def calc_data_size(cls, data: bytes) -> int:
        header = cls.parse_header(data)
        return cls.HEADER_SIZE + header.file_size

    @classmethod
    def parse_resource(cls, data: bytes, outp: Path, version: int) -> Path | None:
        if version not in (0, 1):
            raise ValueError(f"unsupported data version: {version}")

        header = cls.parse_header(data)
        payload = data[cls.HEADER_SIZE:]  # cut header

        if header.file_type == cls.TYPE_EXTERNAL:
            ext = guess_file_ext(payload)
        elif header.file_type == cls.TYPE_SCRIPT:
            return ParserVN.parse_resource(payload, outp, version)
        else:  # ?
            ext = "bin"
            # raise RuntimeError(f"unsupported M2 file type: {header.file_type}")

        target_path = outp.with_name(f"{outp.stem}.{ext}")
        target_path.write_bytes(payload)

        return target_path
