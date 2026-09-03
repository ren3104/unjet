import filetype

from pathlib import Path
import re
import codecs

from .constants import B38_ALPHABET


def base38_decode(v: int) -> str:
    if v == 0:
        return "0"
    out = []
    while v:
        v, r = divmod(v, 38)
        out.append(B38_ALPHABET[r])
    return "".join(reversed(out)) 


def base38_encode(name: str) -> int:
    if len(name) > 12:
        raise ValueError("maximum 12 characters allowed")
    v = 0
    for ch in name:
        o = ord(ch)
        if   0x30 <= o <= 0x39:
            d = o - 0x30  # 0-9
        elif 0x61 <= o <= 0x7a:
            d = o - 0x57  # a-z -> 10..35
        elif 0x41 <= o <= 0x5a:
            d = o - 0x37  # A-Z -> 10..35
        elif ch in ".[":
            d = 36
        elif ch == "_":
            d = 37
        else:
            raise ValueError(f"{ch!r} is not in the base38 alphabet")
        v = v * 38 + d
    return v


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
