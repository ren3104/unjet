from pathlib import Path

from ..helpers import guess_file_ext


class ParserSN:
    TYPE_CODE = "SN"

    HEADER_SIZE = 10

    @classmethod
    def parse_resource(cls, data: bytes, outp: Path, version: int) -> Path:
        if version not in (0, 1):
            raise ValueError(f"unsupported data version: {version}")

        if len(data) < cls.HEADER_SIZE:
            raise ValueError(f"data too small: {len(data)} bytes")

        payload = data[cls.HEADER_SIZE:]
        ext = guess_file_ext(payload)

        target_path = outp.with_name(f"{outp.stem}.{ext}")
        target_path.write_bytes(payload)

        return target_path
