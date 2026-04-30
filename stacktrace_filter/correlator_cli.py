"""CLI entry-point for the correlator module."""
from __future__ import annotations

import argparse
import sys
from typing import List

from stacktrace_filter.io_utils import read_source
from stacktrace_filter.parser import parse
from stacktrace_filter.correlator import correlate, format_correlation


def build_correlator_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-correlator",
        description="Correlate tracebacks by shared frames.",
    )
    p.add_argument(
        "files",
        nargs="*",
        metavar="FILE",
        help="Input files containing Python tracebacks (default: stdin).",
    )
    p.add_argument(
        "--min-shared",
        type=int,
        default=1,
        metavar="N",
        help="Minimum shared frames to consider two tracebacks correlated (default: 1).",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI color output.",
    )
    p.add_argument(
        "--clusters-only",
        action="store_true",
        default=False,
        help="Print only cluster membership, not edge details.",
    )
    return p


def main(argv: List[str] | None = None) -> None:  # pragma: no cover
    parser = build_correlator_parser()
    args = parser.parse_args(argv)

    sources: List[str] = []
    if args.files:
        for path in args.files:
            try:
                sources.append(read_source(path))
            except FileNotFoundError:
                print(f"error: file not found: {path}", file=sys.stderr)
                sys.exit(1)
    else:
        sources.append(sys.stdin.read())

    tracebacks = []
    for src in sources:
        tb = parse(src)
        if tb is not None:
            tracebacks.append(tb)

    if not tracebacks:
        print("No tracebacks found.", file=sys.stderr)
        sys.exit(0)

    result = correlate(tracebacks, min_shared=args.min_shared)
    output = format_correlation(result, color=not args.no_color)

    if args.clusters_only:
        lines = [l for l in output.splitlines() if "Cluster" in l or "Correlation" in l]
        print("\n".join(lines))
    else:
        print(output)
