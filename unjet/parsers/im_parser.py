import struct
from pathlib import Path
from PIL import Image


def parse_im_file(data: bytes, outp: Path) -> Path | None:
    if len(data) < 7:
        raise ValueError(f"Data too small: {len(data)} bytes")

    _, flag, width, height = struct.unpack_from("<2sB2H", data)

    if width == 0 or height == 0:
        return

    offset = 7
    pixel_count = width * height

    if flag == 6: # 8-bit grayscale
        expected_size = offset + pixel_count
        if len(data) < expected_size:
            raise ValueError("Unexpected end of grayscale data")
        
        img = Image.frombytes("L", (width, height), data[offset:expected_size])

    elif flag == 0: # RGB565 -> RGB888
        expected_size = offset + (pixel_count * 2)
        if len(data) < expected_size:
            raise ValueError("Unexpected end of RGB565 data")

        img = Image.frombytes(
            "RGB", 
            (width, height), 
            data[offset:expected_size], 
            "raw", 
            "BGR;16"
        )

    elif flag == 2: # RGB565 + Alpha -> RGBA8888
        rgb_data_size = pixel_count * 2
        alpha_offset = offset + rgb_data_size
        expected_size = alpha_offset + pixel_count

        if len(data) < expected_size:
            raise ValueError("Unexpected end of RGBA data")

        img = Image.frombytes(
            "RGB", 
            (width, height), 
            data[offset:alpha_offset], 
            "raw", 
            "BGR;16"
        )
        
        alpha_channel = Image.frombytes(
            "L", 
            (width, height), 
            data[alpha_offset:expected_size]
        )
        
        img.putalpha(alpha_channel)

    else:
        raise RuntimeError(f"Unsupported image mode ({flag})")

    target_path = outp.with_name(f"{outp.stem}.png")
    img.save(target_path)

    return target_path
