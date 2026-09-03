import struct
from pathlib import Path
from typing import NamedTuple
import json

from PIL import Image


class AnHeader(NamedTuple):
    block_count: int


class ParserAN:
    TYPE_CODE = "AN"

    HEADER_FORMAT = "<2sH"
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    OLD_BLOCK_FORMAT = "<3H"
    OLD_BLOCK_SIZE = struct.calcsize(OLD_BLOCK_FORMAT)
    NEW_BLOCK_FORMAT = "<IQ"
    NEW_BLOCK_SIZE = struct.calcsize(NEW_BLOCK_FORMAT)

    @classmethod
    def parse_header(cls, data: bytes) -> AnHeader:
        if len(data) < cls.HEADER_SIZE:
            raise ValueError(f"data too small: {len(data)} bytes")

        _, block_count = struct.unpack_from(cls.HEADER_FORMAT, data)
        return AnHeader(block_count)

    @classmethod
    def calc_data_size(cls, data: bytes) -> int:
        # Only used for v0 archives, so the old (6-byte block) layout applies.
        header = cls.parse_header(data)
        return cls.HEADER_SIZE + header.block_count * cls.OLD_BLOCK_SIZE

    @classmethod
    def parse_resource(
        cls, data: bytes, outp: Path, version: int
    ) -> Path | tuple[Path, Path]:
        if version not in (0, 1):
            raise ValueError(f"unsupported data version: {version}")

        old_version = version == 0

        view = memoryview(data)
        header = cls.parse_header(view)

        offset = cls.HEADER_SIZE
        blocks = {}
        for _ in range(header.block_count):
            if old_version:
                duration, _, sp_id = struct.unpack_from(
                    cls.OLD_BLOCK_FORMAT, view, offset)
                offset += cls.OLD_BLOCK_SIZE
            else:
                duration, sp_id = struct.unpack_from(
                    cls.NEW_BLOCK_FORMAT, view, offset)
                offset += cls.NEW_BLOCK_SIZE
            blocks[sp_id] = duration

        json_path = outp.with_name(f"{outp.stem}.json")
        json_path.write_text(json.dumps(blocks))

        if len(blocks) <= 1:
            return json_path

        img_cache: dict[str, Image.Image] = {}

        def get_img(im_id: str) -> Image.Image:
            if im_id not in img_cache:
                img_cache[im_id] = Image.open(outp.parent / f"{im_id}.png")
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
