"""CLI entry point for severity classification of tracebacks."""
from __future__ import annotations
import argparse
import sys
from stacktrace_filter.io_utils import read_source
from stacktrace_filter.parser import parse
from stacktrace_filter.severity import classify, format_severity


def build_severity_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-severity",
        description="Classify the severity of a Python traceback.",
    )
    p.add_argument("file", nargs="?", help="input file (default: stdin)")
    p.add_argument(
        "--no-color", action="store_true", default=False, help="disable colored output"
    )
    p.add_argument(
        "--critical-keyword",
        action="append",
        dest="critical_keywords",
        metavar="KW",
        default=[],
        help="treat tracebacks containing KW as CRITICAL (repeatable)",
    )
    p.add_argument(
        "--min-score",
        type=int,
        default=0,
        help="only show tracebacks with severity score >= MIN_SCORE",
    )
    return p


def main(argv=None) -> None:
    parser = build_severity_parser()
    args = parser.parse_args(argv)

    try:
        text = read_source(args.file)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    tb = parse(text)
    result = classify(tb, critical_keywords=args.critical_keywords)

    if result.score < args.min_score:
        return

    color = not args.no_color
    print(format_severity(result, color=color))


if __name__ == "__main__":  # pragma: no cover
    main()
