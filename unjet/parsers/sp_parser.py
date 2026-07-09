import struct
from pathlib import Path
import json


def parse_sp_file(data: bytes, outp: Path, old_version: bool = False) -> Path:
    if len(data) < 4:
        raise ValueError(f"Data too small: {len(data)} bytes")
    
    _, count = struct.unpack_from("<2sH", data)
    
    offset = 4
    records = {"unknown": []}

    for _ in range(count):
        if old_version:
            x, y, im_file = struct.unpack("<hhH", data[offset:offset+6])
            offset += 6
        else:
            x, y, im_file = struct.unpack("<hhI", data[offset:offset+8])
            offset += 8
        records[im_file] = (x, y)
    
    # unknown array
    if old_version:
        unknown_count = 2
    else:
        unknown_count = count + 2
    for _ in range(unknown_count):
        value = struct.unpack("<I", data[offset:offset+4])[0]
        offset += 4
        records["unknown"].append(value)
    
    target_path = outp.with_name(f"SP_{outp.stem}.json")
    target_path.write_text(json.dumps(records))
    
    return target_path
