import filetype

from pathlib import Path
import re
import codecs


_NUM_RE = re.compile(r"(\d+)")


def natural_keys(value: str | Path) -> list[str | int]:
    """Sorts in human order"""
    if not isinstance(value, str):
        value = str(value)
    
    return [
        int(c) if c.isdigit() else c
        for c in _NUM_RE.split(value)
    ]


def check_encoding(
    data: bytes,
    sample_size: int | None = 512,
    encoding="utf-8"
) -> str | None:
    try:
        if sample_size is None:
            return data.decode(encoding)
        
        decoder = codecs.getincrementaldecoder(encoding)("strict")
        return decoder.decode(data[:sample_size], final=False)
    except UnicodeDecodeError:
        return None


def guess_file_ext(data: bytes) -> str:
    kind = filetype.guess(data)
    if kind is not None:
        return kind.extension
    
    text = check_encoding(data)
    if text is not None:
        # spine atlas
        text_lines = text.lstrip().split("\n", maxsplit=5)[:5]
        if (
            len(text_lines) == 5 and
            text_lines[1].startswith("size") and
            text_lines[2].startswith("format") and
            text_lines[3].startswith("filter") and
            text_lines[4].startswith("repeat")
        ):
            return "atlas"

        return "txt"
    else:
        # spine skel
        if (
            data[0] == 0x1C and
            all(
                ((0x30 <= data[i] <= 0x39) or data[i] == 0x2E)
                for i in range(29, 32)
            )
        ):
            return "skel"
    
    return "bin"
