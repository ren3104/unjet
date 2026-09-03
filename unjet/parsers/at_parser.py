import struct
from pathlib import Path
from typing import NamedTuple
import json

from PIL import Image

from ..helpers import base38_decode


class AtHeader(NamedTuple):
    block_count: int


class ParserAT:
    TYPE_CODE = "AT"

    COUNT_OFFSET = 43  # "<2sI9f" (42) + 1 magic byte
    HEADER_SIZE = 47  # COUNT_OFFSET + 4-byte count

    BLOCK_FORMAT = "<QfH"
    BLOCK_SIZE = struct.calcsize(BLOCK_FORMAT)

    @classmethod
    def parse_header(cls, data: bytes) -> AtHeader:
        if len(data) < cls.HEADER_SIZE:
            raise ValueError(f"data too small: {len(data)} bytes")

        block_count = struct.unpack_from("<I", data, cls.COUNT_OFFSET)[0]
        return AtHeader(block_count)

    @classmethod
    def parse_resource(
        cls, data: bytes, outp: Path, version: int
    ) -> Path | tuple[Path, Path]:
        if version not in (0, 1):
            raise ValueError(f"unsupported data version: {version}")

        view = memoryview(data)
        header = cls.parse_header(view)

        offset = cls.HEADER_SIZE
        blocks = {}
        for _ in range(header.block_count):
            block_id, frame_duration, name_len = struct.unpack_from(
                cls.BLOCK_FORMAT, view, offset)
            offset += cls.BLOCK_SIZE
            name = struct.unpack_from(f"<{name_len}s", view, offset)[0].decode("ascii")
            offset += name_len

            blocks[base38_decode(block_id)] = [
                int(frame_duration * 1000),
                name_len,
                name,
            ]

        json_path = outp.with_name(f"{outp.stem}.json")
        json_path.write_text(json.dumps(blocks))

        if len(blocks) <= 1:
            return json_path

        img_cache: dict[str, Image.Image] = {}

        def get_img(i2_id: str) -> Image.Image:
            if i2_id not in img_cache:
                img_cache[i2_id] = Image.open(outp.parent / f"{i2_id}.png")
            return img_cache[i2_id]

        all_frames_data: list[tuple[list, int]] = []
        for s2_id, block in blocks.items():
            s2_data: dict = json.loads((outp.parent / f"{s2_id}.json").read_bytes())
            layers = [
                (get_img(i2_id), coords[0], coords[1])
                for i2_id, coords in s2_data.items()
            ]
            all_frames_data.append((layers, block[1]))  # (layers, duration_ms)

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
