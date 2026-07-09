from pathlib import Path
import subprocess

from ..constants import SPINE_CONVERTER
from ..helpers import guess_file_ext


def parse_rw_file(data: bytes, outp: Path) -> Path:
    if len(data) < 6:
        raise ValueError(f"Data too small: {len(data)} bytes")
    
    data = data[6:] # skip jet header

    ext = guess_file_ext(data)
    
    target_path = outp.with_name(f"RW_{outp.stem}.{ext}")
    target_path.write_bytes(data)

    # Convert spine .skel to .json
    # https://github.com/wang606/SpineSkeletonDataConverter
    if ext == "skel" and SPINE_CONVERTER.exists():
        json_path = target_path.with_suffix(".json")
        subprocess.run(
            [str(SPINE_CONVERTER), str(target_path), str(json_path)],
            stdout=subprocess.DEVNULL,
            check=True
        )

    return target_path
