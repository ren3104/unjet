from pathlib import Path


def parse_vn_file(data: bytes, outp: Path) -> Path:
    target_path = outp.with_name(f"VN_{outp.stem}.bin")

    target_path.write_bytes(data)

    return target_path
