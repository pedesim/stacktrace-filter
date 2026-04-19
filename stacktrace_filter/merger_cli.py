"""CLI entry point for the merger tool."""
from __future__ import annotations
import argparse
import sys
from stacktrace_filter.io_utils import read_source
from stacktrace_filter.parser import parse
from stacktrace_filter.merger import merge, format_merge_result


def build_merger_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stf-merge",
        description="Merge and deduplicate tracebacks from multiple files.",
    )
    p.add_argument("files", nargs="+", metavar="FILE", help="Input files (use - for stdin)")
    p.add_argument("--no-dedup", action="store_true", help="Disable deduplication")
    p.add_argument(
        "--sort-by",
        choices=["depth", "user_frames", "exc_type"],
        default="depth",
        help="Sort criterion (default: depth)",
    )
    p.add_argument("--ascending", action="store_true", help="Sort ascending")
    p.add_argument("--json", action="store_true", help="Output JSON summary")
    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_merger_parser()
    args = parser.parse_args(argv)

    groups = []
    for path in args.files:
        try:
            source = read_source(path)
        except FileNotFoundError:
            print(f"error: file not found: {path}", file=sys.stderr)
            sys.exit(1)
        groups.append(parse(source))

    result = merge(
        groups,
        dedup=not args.no_dedup,
        sort_by=args.sort_by,
        ascending=args.ascending,
    )

    if args.json:
        import json
        print(json.dumps({"kept": result.kept, "dropped": result.dropped, "total_input": result.total_input}))
    else:
        print(format_merge_result(result))
