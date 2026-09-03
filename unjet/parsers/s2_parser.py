import struct
from pathlib import Path
import json

from ..helpers import base38_encode


def parse_s2_file(data: bytes, outp: Path) -> Path:
    if len(data) < 42:
        raise ValueError(f"Data too small: {len(data)} bytes")
    
    # header = struct.unpack("<2sI9f", data[:42]) # skip
    
    block_count = struct.unpack("<I", data[42:46])[0]

    offset = 46
    blocks = {}
    for _ in range(block_count):
        i2_id, x, y = struct.unpack("<Q2i", data[offset:offset+16])
        i2_id = base38_encode(i2_id)
        offset += 16
        blocks[i2_id] = (x, y)

    target_path = outp.with_name(f"{outp.stem}.json")
    target_path.write_text(json.dumps(blocks))
    
    return target_path
