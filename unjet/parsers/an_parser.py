import struct
from pathlib import Path
import json
from PIL import Image


def parse_an_file(
    data: bytes,
    outp: Path,
    old_version: bool = False
) -> Path | tuple[Path, Path]:
    if len(data) < 4:
        raise ValueError(f"Data too small: {len(data)} bytes")

    _, block_count = struct.unpack_from("<2sH", data)

    offset = 4
    blocks = {}
    for _ in range(block_count):
        if old_version:
            duration, _, sp_id = struct.unpack("<3H", data[offset:offset+6])
            offset += 6
        else:
            duration, sp_id = struct.unpack("<IQ", data[offset:offset+12])
            offset += 12
        blocks[sp_file] = duration
    
    json_path = outp.with_name(f"{outp.stem}.json")
    json_path.write_text(json.dumps(blocks))

    if len(blocks) <= 1:
        return json_path

    img_cache: dict[str, Image.Image] = {}

    def get_img(im_id: str) -> Image.Image:
        if im_id not in img_cache:
            img = Image.open(outp.parent / f"{im_id}.png")
            img_cache[im_id] = img
        return img_cache[im_id]

    all_frames_data: list[tuple[list, int]] = []
    for sp_id, duration in blocks.items():
        sp_data: dict = json.loads((outp.parent / f"{sp_id}.json").read_bytes())
        layers = [
            (get_img(im_id), coords[0], coords[1])
            for im_id, coords in sp_data.items()
            if im_id != "unknown"
        ]
        all_frames_data.append((layers, duration))

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
