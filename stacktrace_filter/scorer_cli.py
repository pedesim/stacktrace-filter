"""CLI entry point for the scorer module."""
from __future__ import annotations
import argparse
import sys
from stacktrace_filter.io_utils import read_source
from stacktrace_filter.parser import parse
from stacktrace_filter.scorer import score_all, format_scored


def build_scorer_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-scorer",
        description="Score and rank tracebacks by relevance.",
    )
    p.add_argument("file", nargs="?", help="Input file (default: stdin)")
    p.add_argument("--no-color", action="store_true", help="Disable color output")
    p.add_argument(
        "--weight-user", type=float, default=0.5, metavar="W",
        help="Weight for user-frame ratio (default: 0.5)",
    )
    p.add_argument(
        "--weight-depth", type=float, default=0.3, metavar="W",
        help="Weight for depth score (default: 0.3)",
    )
    p.add_argument(
        "--weight-exc", type=float, default=0.2, metavar="W",
        help="Weight for exception-type score (default: 0.2)",
    )
    p.add_argument(
        "--top", type=int, default=0, metavar="N",
        help="Show only top N results (0 = all)",
    )
    return p


def main(argv=None) -> None:
    parser = build_scorer_parser()
    args = parser.parse_args(argv)

    if args.file:
        try:
            text = read_source(args.file)
        except FileNotFoundError:
            print(f"error: file not found: {args.file}", file=sys.stderr)
            sys.exit(1)
    else:
        text = sys.stdin.read()

    tb = parse(text)
    tracebacks = [tb] if tb.frames else []

    scored = score_all(
        tracebacks,
        weight_user=args.weight_user,
        weight_depth=args.weight_depth,
        weight_exc=args.weight_exc,
    )

    if args.top:
        scored = scored[: args.top]

    print(format_scored(scored, color=not args.no_color))
