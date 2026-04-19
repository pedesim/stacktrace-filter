"""CLI entry point for traceback comparison."""
from __future__ import annotations
import argparse
import sys
from stacktrace_filter.io_utils import read_source
from stacktrace_filter.parser import parse
from stacktrace_filter.comparator import compare, format_comparison


def build_comparator_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-compare",
        description="Compare two Python tracebacks and score their similarity.",
    )
    p.add_argument("left", help="First traceback file (or '-' for stdin)")
    p.add_argument("right", help="Second traceback file")
    p.add_argument("--no-color", action="store_true", help="Disable ANSI color output")
    p.add_argument(
        "--score-only",
        action="store_true",
        help="Print only the numeric overall score",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_comparator_parser()
    args = parser.parse_args(argv)

    try:
        left_text = read_source(args.left)
    except FileNotFoundError:
        print(f"error: file not found: {args.left}", file=sys.stderr)
        sys.exit(1)

    try:
        right_text = read_source(args.right)
    except FileNotFoundError:
        print(f"error: file not found: {args.right}", file=sys.stderr)
        sys.exit(1)

    left_tb = parse(left_text)
    right_tb = parse(right_text)
    result = compare(left_tb, right_tb)

    if args.score_only:
        print(result.overall_score)
    else:
        print(format_comparison(result, color=not args.no_color))
