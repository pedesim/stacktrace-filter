"""CLI entry point for the splitter feature."""
from __future__ import annotations
import argparse
import json
import sys
from stacktrace_filter.parser import parse
from stacktrace_filter.splitter import SplitRule, split, format_split_result
from stacktrace_filter.io_utils import read_source


def build_splitter_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-splitter",
        description="Split tracebacks into named partitions.",
    )
    p.add_argument("input", nargs="?", default="-", help="Input file (default: stdin)")
    p.add_argument(
        "--rules",
        required=True,
        metavar="FILE",
        help="JSON file with split rules [{name, exc_type}]",
    )
    p.add_argument("--json", action="store_true", help="Output counts as JSON")
    return p


def _load_rules(path: str) -> list:
    with open(path) as fh:
        return json.load(fh)


def main(argv=None) -> None:
    parser = build_splitter_parser()
    args = parser.parse_args(argv)

    if not __import__("pathlib").Path(args.rules).exists():
        print(f"error: rules file not found: {args.rules}", file=sys.stderr)
        sys.exit(1)

    raw_rules = _load_rules(args.rules)
    rules = [
        SplitRule(
            name=r["name"],
            predicate=lambda tb, et=r.get("exc_type", ""): et in (tb.exception or ""),
        )
        for r in raw_rules
    ]

    text = read_source(args.input)
    tb = parse(text)
    result = split([tb], rules)

    if args.json:
        out = {name: len(tbs) for name, tbs in result.partitions.items()}
        out["unmatched"] = len(result.unmatched)
        print(json.dumps(out))
    else:
        print(format_split_result(result))
