import struct
from pathlib import Path
import json
from PIL import Image

from ..helpers import base38_decode


def parse_at_file(data: bytes, outp: Path) -> Path | tuple[Path, Path]:
    if len(data) < 47:
        raise ValueError(f"Data too small: {len(data)} bytes")
    
    # header = struct.unpack("<2sI9f", data[:42]) # skip
    # magic = data[42] # skip
    block_count = struct.unpack("<I", data[43:47])[0]
    offset = 47

    blocks = {}
    for _ in range(block_count):
        block_header = struct.unpack("<QfH", data[offset:offset+14])
        offset += 14
        block_header += (data[offset:offset+block_header[2]],)
        offset += block_header[2]

        blocks[base38_decode(block_header[0])] = [ # S2 file
            int(block_header[1] * 1000), # frame duration
            block_header[2], # name len
            block_header[3].decode("ascii"), # name
        ]
    
    json_path = outp.with_name(f"{outp.stem}.json")
    json_path.write_text(json.dumps(blocks))

    if len(blocks) <= 1:
        return json_path

    img_cache: dict[str, Image.Image] = {}

    def get_img(i2_id: str) -> Image.Image:
        if i2_id not in img_cache:
            img = Image.open(outp.parent / f"{i2_id}.png")
            img_cache[i2_id] = img
        return img_cache[i2_id]

    all_frames_data: list[tuple[list, int]] = []
    for s2_id, block in blocks.items():
        s2_data: dict = json.loads((outp.parent / f"{s2_id}.json").read_bytes())
        layers = [(get_img(i2_id), coords[0], coords[1]) for i2_id, coords in s2_data.items()]
        all_frames_data.append((layers, block[1])) # (layers, duration_ms)

    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")
    for layers, _ in all_frames_data:
        for img, x, y in layers:
            if x < min_x:
                min_x = x
            if y < min_y:
                min_y = y
            r = x + img.width
            max_x = r if r > max_x else max_x
            b = y + img.height
            max_y = b if b > max_y else max_y

    min_x, min_y = int(min_x), int(min_y)
    canvas_w = int(max_x) - min_x
    canvas_h = int(max_y) - min_y
    ox, oy = -min_x, -min_y

    frames: list[Image.Image] = []
    durations: list[int] = []
    for layers, duration in all_frames_data:
        frame = Image.new("RGBA", (canvas_w, canvas_h))
        for img, x, y in layers:
            frame.paste(img, (x + ox, y + oy))
        frames.append(frame)
        durations.append(duration)

    webp_path = outp.with_name(f"{outp.stem}.webp")
    frames[0].save(
        webp_path,
        format="WEBP",
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        quality=90,
        lossless=False,
    )

    return json_path, webp_path
