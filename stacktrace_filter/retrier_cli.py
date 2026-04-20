"""CLI entry-point for the retrier advisor."""
from __future__ import annotations

import argparse
import sys

from stacktrace_filter.io_utils import read_source
from stacktrace_filter.parser import parse
from stacktrace_filter.retrier import RetrierConfig, advise, format_advice


def build_retrier_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stf-retrier",
        description="Advise whether a Python traceback is safe to retry.",
    )
    p.add_argument(
        "file",
        nargs="?",
        default="-",
        help="Traceback file (default: stdin).",
    )
    p.add_argument(
        "--retryable",
        metavar="EXC",
        action="append",
        default=[],
        dest="extra_retryable",
        help="Additional exception type to treat as retryable.",
    )
    p.add_argument(
        "--fatal",
        metavar="EXC",
        action="append",
        default=[],
        dest="extra_fatal",
        help="Additional exception type to treat as fatal.",
    )
    p.add_argument(
        "--delay",
        type=float,
        default=1.0,
        dest="default_delay_s",
        help="Suggested retry delay in seconds (default: 1.0).",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Emit result as JSON.",
    )
    return p


def main(argv: list[str] | None = None) -> None:  # pragma: no cover
    parser = build_retrier_parser()
    args = parser.parse_args(argv)

    try:
        text = read_source(args.file)
    except FileNotFoundError:
        print(f"stf-retrier: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    tb = parse(text)
    cfg = RetrierConfig(
        extra_retryable=args.extra_retryable,
        extra_fatal=args.extra_fatal,
        default_delay_s=args.default_delay_s,
    )
    advice = advise(tb, cfg)

    if args.json:
        import json
        print(json.dumps({
            "exc_type": advice.exc_type,
            "retryable": advice.retryable,
            "fatal": advice.fatal,
            "reason": advice.reason,
            "suggested_delay_s": advice.suggested_delay_s,
            "matched_rule": advice.matched_rule,
        }))
    else:
        print(format_advice(advice))
