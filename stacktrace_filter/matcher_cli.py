"""CLI for matching tracebacks against named rules."""
from __future__ import annotations
import argparse
import json
import sys

from stacktrace_filter.io_utils import read_source
from stacktrace_filter.parser import parse
from stacktrace_filter.matcher import MatchRule, apply_rules


def build_matcher_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-matcher",
        description="Match tracebacks against pattern rules.",
    )
    p.add_argument("file", nargs="?", help="Input file (default: stdin)")
    p.add_argument("--rules", required=True, help="JSON file defining match rules")
    p.add_argument("--only-matched", action="store_true", help="Only print matched results")
    return p


def _load_rules(path: str) -> list[MatchRule]:
    with open(path) as f:
        data = json.load(f)
    return [
        MatchRule(
            name=r["name"],
            exc_type_pattern=r.get("exc_type_pattern"),
            exc_message_pattern=r.get("exc_message_pattern"),
            filename_pattern=r.get("filename_pattern"),
            min_depth=r.get("min_depth"),
        )
        for r in data
    ]


def main(argv: list[str] | None = None) -> None:
    args = build_matcher_parser().parse_args(argv)
    try:
        rules = _load_rules(args.rules)
    except FileNotFoundError:
        print(f"Rules file not found: {args.rules}", file=sys.stderr)
        sys.exit(1)

    try:
        text = read_source(args.file)
    except FileNotFoundError:
        print(f"File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    tb = parse(text)
    result = apply_rules(tb, rules)

    if args.only_matched and not result.matched:
        return

    if result.matched:
        print(f"Matched rules: {', '.join(result.matched_rules)}")
    else:
        print("No rules matched.")
