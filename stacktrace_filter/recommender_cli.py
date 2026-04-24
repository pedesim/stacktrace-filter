"""CLI entry point for the recommender module."""
from __future__ import annotations

import argparse
import sys

from stacktrace_filter.io_utils import read_source
from stacktrace_filter.parser import parse
from stacktrace_filter.recommender import recommend, format_recommendation


def build_recommender_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-recommend",
        description="Suggest fixes for a Python traceback.",
    )
    p.add_argument(
        "file",
        nargs="?",
        default="-",
        help="Path to traceback file (default: stdin).",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI color output.",
    )
    p.add_argument(
        "--advice-only",
        action="store_true",
        default=False,
        help="Print only the advice string, no header or location.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_recommender_parser()
    args = parser.parse_args(argv)

    try:
        source = read_source(args.file)
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 1

    tb = parse(source)
    rec = recommend(tb)

    if args.advice_only:
        print(rec.advice)
    else:
        color = not args.no_color
        print(format_recommendation(rec, color=color))

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
