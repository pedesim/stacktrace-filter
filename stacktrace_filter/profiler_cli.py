"""CLI entry point for the profiler module."""
from __future__ import annotations
import argparse
import sys
from stacktrace_filter.io_utils import read_source
from stacktrace_filter.parser import parse
from stacktrace_filter.profiler import profile, format_profile


def build_profiler_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stf-profile",
        description="Profile frame frequency across multiple tracebacks.",
    )
    p.add_argument(
        "files",
        nargs="*",
        metavar="FILE",
        help="Input files (default: stdin).",
    )
    p.add_argument(
        "--top",
        type=int,
        default=10,
        metavar="N",
        help="Number of top entries to show (default: 10).",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Output raw counts as JSON.",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_profiler_parser()
    args = parser.parse_args(argv)

    sources = []
    if args.files:
        for path in args.files:
            try:
                sources.append(read_source(path))
            except FileNotFoundError:
                parser.error(f"File not found: {path}")
    else:
        sources.append(sys.stdin.read())

    tracebacks = []
    for src in sources:
        tracebacks.extend(parse(src))

    report = profile(tracebacks, top_n=args.top)

    if args.json:
        import json
        out = {
            "total_tracebacks": report.total_tracebacks,
            "total_frames": report.total_frames,
            "top_frames": [
                {"filename": fp.filename, "function": fp.function,
                 "count": fp.count, "pct": fp.pct}
                for fp in report.top_frames
            ],
            "top_files": [list(t) for t in report.top_files],
            "top_functions": [list(t) for t in report.top_functions],
        }
        print(json.dumps(out, indent=2))
    else:
        print(format_profile(report))
