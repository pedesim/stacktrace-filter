"""CLI entry point for the batcher module."""
from __future__ import annotations
import argparse
import sys
from stacktrace_filter.io_utils import read_source
from stacktrace_filter.parser import parse
from stacktrace_filter.batcher import batch_tracebacks, format_batch_result


def build_batcher_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-batch",
        description="Split a file of tracebacks into fixed-size batches.",
    )
    p.add_argument("input", nargs="?", default="-", help="Input file (default: stdin)")
    p.add_argument(
        "--batch-size", "-n", type=int, default=10,
        metavar="N", help="Max tracebacks per batch (default: 10)",
    )
    p.add_argument(
        "--summary", action="store_true",
        help="Print batch summary instead of per-batch output",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_batcher_parser()
    args = parser.parse_args(argv)

    try:
        text = read_source(args.input)
    except FileNotFoundError:
        print(f"error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    tb = parse(text)
    result = batch_tracebacks([tb] if tb.frames else [], args.batch_size)

    if args.summary:
        print(format_batch_result(result))
    else:
        for batch in result.batches:
            print(f"--- Batch {batch.index} ({batch.size} entries) ---")


if __name__ == "__main__":
    main()
