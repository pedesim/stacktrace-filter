"""CLI for throttle-filtering a stream of tracebacks."""
from __future__ import annotations
import argparse
import sys

from stacktrace_filter.io_utils import read_source
from stacktrace_filter.chain import parse_chained
from stacktrace_filter.throttler import Throttler, ThrottlerConfig
from stacktrace_filter.exporter import export


def build_throttler_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stf-throttle",
        description="Drop repeated tracebacks that exceed a rate limit.",
    )
    p.add_argument("file", nargs="?", help="Input file (default: stdin)")
    p.add_argument(
        "--max", type=int, default=10, metavar="N",
        help="Max occurrences per window (default: 10)",
    )
    p.add_argument(
        "--window", type=float, default=60.0, metavar="SECS",
        help="Window size in seconds (default: 60)",
    )
    p.add_argument(
        "--format", choices=["plain", "json"], default="plain",
        help="Output format (default: plain)",
    )
    p.add_argument("--no-color", action="store_true", help="Disable color output")
    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_throttler_parser()
    args = parser.parse_args(argv)

    try:
        text = read_source(args.file)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    tracebacks = [ct.tracebacks[-1] for ct in parse_chained(text) if ct.tracebacks]
    config = ThrottlerConfig(max_per_window=args.max, window_seconds=args.window)
    throttler = Throttler(config)
    kept = throttler.filter(tracebacks)

    for tb in kept:
        print(export(tb, fmt=args.format, color=not args.no_color))


if __name__ == "__main__":
    main()
