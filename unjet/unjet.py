from pathlib import Path

from .constants import JET_FILE_EXTENSIONS, CURSOR_FILE
from .helpers import natural_keys
from .extractor import extract_jet_file


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
        extract_jet_file(inp, out, False)
    elif inp.is_dir():
        for file in iter_jet_files(inp):
            extract_jet_file(file, out, True)
