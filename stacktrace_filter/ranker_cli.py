"""CLI entry-point for the ranker module."""
from __future__ import annotations

import argparse
import sys
from typing import List

from .io_utils import read_source
from .parser import parse
from .ranker import format_rank, rank_tracebacks


def build_ranker_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-rank",
        description="Rank tracebacks in a file by relevance score.",
    )
    p.add_argument(
        "file",
        nargs="?",
        default="-",
        help="Input file (default: stdin).",
    )
    p.add_argument(
        "--ascending",
        action="store_true",
        default=False,
        help="Sort from lowest to highest score.",
    )
    p.add_argument(
        "--top",
        type=int,
        default=0,
        metavar="N",
        help="Only show the top N results (0 = all).",
    )
    p.add_argument(
        "--scores-only",
        action="store_true",
        default=False,
        help="Print only the numeric scores, one per line.",
    )
    return p


def main(argv: List[str] | None = None) -> None:
    parser = build_ranker_parser()
    args = parser.parse_args(argv)

    try:
        text = read_source(args.file)
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    tb = parse(text)
    ranked = rank_tracebacks([tb], ascending=args.ascending)

    if args.top:
        ranked = ranked[: args.top]

    for i, entry in enumerate(ranked):
        if args.scores_only:
            print(entry.score)
        else:
            print(format_rank(entry, index=i))
            print()


if __name__ == "__main__":  # pragma: no cover
    main()
