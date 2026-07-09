import struct
from pathlib import Path
from PIL import Image


def parse_i2_file(data: bytes, outp: Path) -> Path:
    if len(data) < 70:
        raise ValueError(f"Data too small: {len(data)} bytes")
    
    header = struct.unpack_from("<2sI9f7I", data)[2:] # skip magic and ?
    # header idx from 0 to 8 and 12 is ?
    width, height = header[9],  header[10]
    # format = header[11] # or ?
    table_a_len, table_b_len = header[13], header[14]
    rmpot_count = header[15]
    
    offset = 70

    # table_a = struct.unpack_from(f"<{table_a_len}I", data, offset)
    offset += table_a_len * 4

    # table_b = struct.unpack_from(f"<{table_b_len}I", data, offset)
    offset += table_b_len * 4

    rmpot = []
    for _ in range(rmpot_count):
        w_alloc, h_alloc, w, h, x, y = struct.unpack_from("<5s6I", data, offset)[1:]
        rmpot.append((w_alloc, h_alloc, w, h, x, y))
        offset += 29

    canvas = Image.new("RGBA", (width, height))

    for w_alloc, h_alloc, w, h, x, y in rmpot:
        size = w_alloc * h_alloc * 4
        block = Image.frombuffer("RGBA", (w_alloc, h_alloc), data[offset:offset + size])
        canvas.paste(block.crop((0, 0, w, h)), (x, y))
        offset += size
    
    target_path = outp.with_name(f"I2_{outp.stem}.png")
    canvas.save(target_path)

    return target_path
