from __future__ import annotations

import argparse
from pathlib import Path

from .unjet import unjet


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="unjet",
        description="Extract .jet archives",
    )

    parser.add_argument(
        "inp",
        type=Path,
        help="Input .jet/.pak file or directory",
    )

    parser.add_argument(
        "out",
        nargs="?",
        type=Path,
        default=None,
        help="Output directory",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.inp.exists():
        parser.error(f"input not found: {args.inp}")

    try:
        unjet(args.inp, args.out)
    except KeyboardInterrupt:
        print("\nInterrupted")
        return 130
    except Exception as e:
        parser.exit(1, f"Error: {e}\n")

    return 0
