"""CLI entry point for the censor module."""
from __future__ import annotations
import argparse
import json
import sys
from stacktrace_filter.censor import CensorConfig, CensorRule, censor, format_censor_result
from stacktrace_filter.parser import parse
from stacktrace_filter.io_utils import read_source


def build_censor_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-censor",
        description="Censor sensitive patterns in traceback frames.",
    )
    p.add_argument("rules_file", help="JSON file with censor rules")
    p.add_argument("input", nargs="?", default="-", help="Traceback file (default: stdin)")
    p.add_argument("--no-color", action="store_true", help="Disable colored output")
    p.add_argument("--show-count", action="store_true", help="Print censored field count")
    return p


def _load_rules(path: str) -> CensorConfig:
    with open(path) as fh:
        data = json.load(fh)
    rules = [
        CensorRule(
            field=r["field"],
            pattern=r["pattern"],
            replacement=r.get("replacement", "<censored>"),
        )
        for r in data.get("rules", [])
    ]
    return CensorConfig(rules=rules)


def main(argv: list[str] | None = None) -> None:
    parser = build_censor_parser()
    args = parser.parse_args(argv)

    try:
        config = _load_rules(args.rules_file)
    except FileNotFoundError:
        print(f"error: rules file not found: {args.rules_file}", file=sys.stderr)
        sys.exit(1)

    try:
        source = read_source(args.input)
    except FileNotFoundError:
        print(f"error: input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    tb = parse(source)
    result = censor(tb, config)
    output = format_censor_result(result, color=not args.no_color)
    print(output)
    if args.show_count:
        print(f"Total censored: {result.censored_count}")
