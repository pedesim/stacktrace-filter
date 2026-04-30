"""CLI entry point for the suppressor module."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from stacktrace_filter.parser import parse
from stacktrace_filter.suppressor import SuppressRule, SuppressorConfig, suppress, format_suppress_result


def build_suppressor_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-suppressor",
        description="Suppress matching tracebacks from a stream.",
    )
    p.add_argument("input", nargs="?", default="-", help="Input file (default: stdin)")
    p.add_argument(
        "--rules",
        required=True,
        metavar="FILE",
        help="JSON file containing suppression rules",
    )
    p.add_argument(
        "--summary",
        action="store_true",
        help="Print suppression summary instead of kept tracebacks",
    )
    return p


def _load_rules(path: str) -> List[SuppressRule]:
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    rules = []
    for item in raw:
        rules.append(
            SuppressRule(
                exc_type=item.get("exc_type"),
                exc_message=item.get("exc_message"),
                filename=item.get("filename"),
                reason=item.get("reason", "suppressed"),
            )
        )
    return rules


def main(argv=None) -> None:
    parser = build_suppressor_parser()
    args = parser.parse_args(argv)

    try:
        rules = _load_rules(args.rules)
    except FileNotFoundError:
        parser.error(f"Rules file not found: {args.rules}")

    if args.input == "-":
        text = sys.stdin.read()
    else:
        try:
            with open(args.input, encoding="utf-8") as fh:
                text = fh.read()
        except FileNotFoundError:
            parser.error(f"Input file not found: {args.input}")

    tb = parse(text)
    config = SuppressorConfig(rules=rules)
    result = suppress(tb.tracebacks if hasattr(tb, "tracebacks") else [tb], config)

    if args.summary:
        print(format_suppress_result(result))
    else:
        for kept_tb in result.kept:
            print(kept_tb.raw.strip())
            print()
