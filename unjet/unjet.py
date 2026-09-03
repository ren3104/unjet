from pathlib import Path
import struct
import zlib

from .constants import JET_FILE_EXTENSIONS, JET_V1_HEADER_FORMAT, CURSOR_FILE
from .models import JetHeader
from .helpers import natural_keys
from .extractor import extract_jet_file


def guess_version_jet(data: bytes) -> int:
    data_len = len(data)
    if data_len >= 2:
        try:
            zlib.decompressobj().decompress(data, 1)

            return 0
        except zlib.error:
            pass

        try:
            header = JetHeader(*struct.unpack_from(JET_V1_HEADER_FORMAT, data))
            segment_end = struct.calcsize(JET_V1_HEADER_FORMAT) + header.relative_data_end
            if (
                header.part_index == 0
                and header.relative_data_end >= 0
                and header.total_size >= header.part_size
                and segment_end <= header.part_size <= data_len
            ):
                return 1
        except struct.error:
            pass
    
    raise ValueError("unknown jet version")


def iter_jet_files(inp: Path):
    files = []
    for path in inp.iterdir():
        if path.suffix.lower() in JET_FILE_EXTENSIONS:
            files.append(path)
    
    files.sort(key=natural_keys)
    yield from files


def unjet(
    inp: str | Path,
    out: str | Path | None = None
) -> None:
    if not isinstance(inp, Path):
        inp = Path(inp)
    
    if out is None:
        out = inp.with_name(f"{inp.stem}_unjet")
    elif not isinstance(out, Path):
        out = Path(out)
    out.mkdir(parents=True, exist_ok=True)

    cursor_path = out / CURSOR_FILE
    if cursor_path.exists():
        cursor_path.unlink(missing_ok=True)

    if inp.is_file() and inp.suffix.lower() in JET_FILE_EXTENSIONS:
        data = inp.read_bytes()
        version = guess_version_jet(data)
        extract_jet_file(data, out, version)
    elif inp.is_dir():
        version = None
        for file_inp in iter_jet_files(inp):
            data = file_inp.read_bytes()

            if version is None:
                version = guess_version_jet(data)

            if version == 1:
                file_out = out / file_inp.stem
                file_out.mkdir(parents=True, exist_ok=True)
            else:
                file_out = out
            
            extract_jet_file(data, file_out, version)
