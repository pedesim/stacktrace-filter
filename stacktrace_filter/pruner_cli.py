"""CLI entry point for the pruner module."""
from __future__ import annotations
import argparse
import sys

from stacktrace_filter.io_utils import read_source
from stacktrace_filter.parser import parse
from stacktrace_filter.pruner import PruneConfig, prune, format_prune_result


def build_pruner_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-pruner",
        description="Prune noisy frames from a Python traceback.",
    )
    p.add_argument("file", nargs="?", help="Input file (default: stdin)")
    p.add_argument("--max-frames", type=int, default=None, metavar="N",
                   help="Maximum number of frames to keep (tail).")
    p.add_argument("--drop-filename", action="append", default=[],
                   metavar="PATTERN", dest="drop_filenames",
                   help="Regex pattern; drop frames whose filename matches.")
    p.add_argument("--drop-function", action="append", default=[],
                   metavar="PATTERN", dest="drop_functions",
                   help="Regex pattern; drop frames whose function matches.")
    p.add_argument("--keep-last", type=int, default=1, metavar="N",
                   help="Always preserve the last N frames (default: 1).")
    p.add_argument("--no-color", action="store_true", help="Disable ANSI color.")
    return p


def main(argv=None) -> None:
    parser = build_pruner_parser()
    args = parser.parse_args(argv)

    try:
        text = read_source(args.file)
    except FileNotFoundError as exc:
        parser.error(str(exc))
        return

    tb = parse(text)
    config = PruneConfig(
        max_frames=args.max_frames,
        drop_filenames=args.drop_filenames,
        drop_functions=args.drop_functions,
        keep_last=args.keep_last,
    )
    result = prune(tb, config)
    print(format_prune_result(result, color=not args.no_color))


if __name__ == "__main__":
    main()
