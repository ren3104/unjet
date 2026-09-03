import struct
from pathlib import Path
from typing import NamedTuple

from PIL import Image


class ImHeader(NamedTuple):
    flag: int
    width: int
    height: int


class ParserIM:
    TYPE_CODE = "IM"

    HEADER_FORMAT = "<2sB2H"
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    # Pixel encodings.
    FLAG_RGB565 = 0  # RGB565 -> RGB888
    FLAG_RGB565_ALPHA = 2  # RGB565 + A -> RGBA8888
    FLAG_GRAYSCALE = 6  # 8-bit gray -> L

    _BYTES_PER_PIXEL = {
        FLAG_RGB565: 2,
        FLAG_RGB565_ALPHA: 3,
        FLAG_GRAYSCALE: 1,
    }

    @classmethod
    def parse_header(cls, data: bytes) -> ImHeader:
        if len(data) < cls.HEADER_SIZE:
            raise ValueError(f"data too small: {len(data)} bytes")

        _, flag, width, height = struct.unpack_from(cls.HEADER_FORMAT, data)
        return ImHeader(flag, width, height)

    @classmethod
    def calc_data_size(cls, data: bytes) -> int:
        header = cls.parse_header(data)

        try:
            bytes_per_pixel = cls._BYTES_PER_PIXEL[header.flag]
        except KeyError:
            raise ValueError(f"unsupported image flag: {header.flag}")

        return cls.HEADER_SIZE + header.width * header.height * bytes_per_pixel

    @classmethod
    def parse_resource(cls, data: bytes, outp: Path, version: int) -> Path | None:
        if version not in (0, 1):
            raise ValueError(f"unsupported data version: {version}")

        view = memoryview(data)
        header = cls.parse_header(view)

        if header.width == 0 or header.height == 0:
            return None

        size = (header.width, header.height)
        pixel_count = header.width * header.height
        start = cls.HEADER_SIZE

        if header.flag == cls.FLAG_GRAYSCALE:
            end = start + pixel_count
            if len(view) < end:
                raise ValueError("unexpected end of grayscale data")

            img = Image.frombytes("L", size, view[start:end])
        elif header.flag == cls.FLAG_RGB565:
            end = start + pixel_count * 2
            if len(view) < end:
                raise ValueError("unexpected end of RGB565 data")

            img = Image.frombytes("RGB", size, view[start:end], "raw", "BGR;16")
        elif header.flag == cls.FLAG_RGB565_ALPHA:
            alpha_start = start + pixel_count * 2
            end = alpha_start + pixel_count
            if len(view) < end:
                raise ValueError("unexpected end of RGBA data")

            img = Image.frombytes(
                "RGB", size, view[start:alpha_start], "raw", "BGR;16")
            img.putalpha(Image.frombytes("L", size, view[alpha_start:end]))
        else:
            raise ValueError(f"unsupported image mode ({header.flag})")

        target_path = outp.with_name(f"{outp.stem}.png")
        img.save(target_path)

        return target_path
