"""CLI for highlighting individual traceback lines with syntax colouring."""
from __future__ import annotations

import argparse
import sys

from stacktrace_filter.highlighter import highlight_line, highlight_exception_line
from stacktrace_filter.io_utils import read_source


def build_highlighter_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-highlight",
        description="Apply syntax highlighting to traceback lines read from stdin or a file.",
    )
    p.add_argument(
        "file",
        nargs="?",
        default=None,
        help="Path to a traceback file (default: stdin).",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI colour output.",
    )
    p.add_argument(
        "--exception-only",
        action="store_true",
        default=False,
        help="Only highlight the final exception line, pass others through unchanged.",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_highlighter_parser()
    args = parser.parse_args(argv)

    if args.file:
        try:
            text = read_source(args.file)
        except FileNotFoundError:
            print(f"error: file not found: {args.file}", file=sys.stderr)
            sys.exit(1)
    else:
        text = sys.stdin.read()

    color = not args.no_color
    lines = text.splitlines()

    for line in lines:
        stripped = line.rstrip("\n")
        if args.exception_only:
            # Only apply exception highlighting on lines that look like an exception.
            if ": " in stripped and not stripped.startswith(" ") and not stripped.startswith("Traceback"):
                print(highlight_exception_line(stripped, color=color))
            else:
                print(stripped)
        else:
            if stripped.startswith("  File "):
                print(highlight_line(stripped, color=color))
            elif ": " in stripped and not stripped.startswith(" ") and not stripped.startswith("Traceback"):
                print(highlight_exception_line(stripped, color=color))
            else:
                print(stripped)
