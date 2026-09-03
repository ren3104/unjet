from pathlib import Path
import subprocess

from ..constants import SPINE_CONVERTER
from ..helpers import guess_file_ext


class ParserRW:
    TYPE_CODE = "RW"

    HEADER_SIZE = 6

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

        # Convert spine .skel to .json
        # https://github.com/wang606/SpineSkeletonDataConverter
        if ext == "skel" and SPINE_CONVERTER.exists():
            json_path = target_path.with_suffix(".json")
            subprocess.run(
                [str(SPINE_CONVERTER), str(target_path), str(json_path)],
                stdout=subprocess.DEVNULL,
                check=True,
            )

        return target_path
