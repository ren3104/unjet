from pathlib import Path
import struct

from .vn_parser import parse_vn_file
from ..helpers import guess_file_ext


def parse_m2_file(data: bytes, outp: Path) -> Path | None:
    if len(data) < 10:
        raise ValueError(f"Data too small: {len(data)} bytes")

    file_type = struct.unpack("<i", data[2:6])[0]
    data = data[10:] # cut header

    if file_type == -1: # ExternalData
        ext = guess_file_ext(data)
    elif file_type == 0: # ExternalData (Scripts)
        return parse_vn_file(data, outp)
    else: # ?
        ext = "bin"
        # raise RuntimeError(f"Unsupported M2 file type: {file_type}")
    
    target_path = outp.with_name(f"M2_{outp.stem}.{ext}")
    target_path.write_bytes(data)

    return target_path
