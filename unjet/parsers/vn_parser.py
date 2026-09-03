from pathlib import Path


class ParserVN:
    TYPE_CODE = "VN"

    @classmethod
    def parse_resource(cls, data: bytes, outp: Path, version: int) -> Path:
        if version not in (0, 1):
            raise ValueError(f"unsupported data version: {version}")

        target_path = outp.with_name(f"{outp.stem}.bin")
        target_path.write_bytes(data)

        return target_path
