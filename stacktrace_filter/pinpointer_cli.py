"""CLI entry-point for the pinpointer feature."""
from __future__ import annotations

import argparse
import sys

from .io_utils import read_source
from .parser import parse
from .pinpointer import pinpoint, format_pinpoint


def build_pinpointer_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-pinpoint",
        description="Identify the most likely root-cause frame in a Python traceback.",
    )
    p.add_argument(
        "file",
        nargs="?",
        default="-",
        help="Path to a file containing a traceback (default: stdin).",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI colour output.",
    )
    p.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Emit result as JSON instead of plain text.",
    )
    return p


def main(argv: list[str] | None = None) -> None:  # pragma: no cover
    parser = build_pinpointer_parser()
    args = parser.parse_args(argv)

    try:
        source = read_source(args.file)
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    tb = parse(source)
    result = pinpoint(tb)

    if args.json:
        import json

        frame = result.frame
        payload = {
            "reason": result.reason,
            "frame": {
                "filename": frame.filename if frame else None,
                "lineno": frame.lineno if frame else None,
                "function": frame.function if frame else None,
                "text": frame.text if frame else None,
            },
            "index": result.index,
        }
        print(json.dumps(payload, indent=2))
    else:
        print(format_pinpoint(result, color=not args.no_color))
