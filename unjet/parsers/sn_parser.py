from pathlib import Path

from ..helpers import guess_file_ext


def parse_sn_file(data: bytes, outp: Path) -> Path:
    if len(data) < 10:
        raise ValueError(f"Data too small: {len(data)} bytes")
    
    data = data[10:] # skip jet header

    ext = guess_file_ext(data)
    
    target_path = outp.with_name(f"SN_{outp.stem}.{ext}")
    target_path.write_bytes(data)

    return target_path
