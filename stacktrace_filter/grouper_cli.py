"""CLI entry-point for grouping multiple tracebacks from a file."""
from __future__ import annotations
import argparse
import sys
from .io_utils import read_source
from .parser import parse
from .grouper import group_tracebacks, format_groups


def build_grouper_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-group",
        description="Group repeated tracebacks by exception type and message.",
    )
    p.add_argument(
        "file",
        nargs="?",
        default="-",
        help="File containing tracebacks (default: stdin)",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI colour output",
    )
    p.add_argument(
        "--min-count",
        type=int,
        default=1,
        metavar="N",
        help="Only show groups with at least N occurrences (default: 1)",
    )
    return p


def main(argv=None) -> int:
    parser = build_grouper_parser()
    args = parser.parse_args(argv)

    try:
        text = read_source(args.file)
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 1

    # Split on blank lines between tracebacks and parse each block
    blocks = text.strip().split("\n\n")
    tracebacks = []
    for block in blocks:
        block = block.strip()
        if block:
            tb = parse(block + "\n")
            if tb is not None:
                tracebacks.append(tb)

    groups = group_tracebacks(tracebacks)
    if args.min_count > 1:
        groups = [g for g in groups if g.count >= args.min_count]

    print(format_groups(groups, color=not args.no_color), end="")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
