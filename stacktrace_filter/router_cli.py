"""CLI for traceback router."""
from __future__ import annotations
import argparse
import json
import sys
from stacktrace_filter.parser import parse
from stacktrace_filter.router import RouterConfig, RouteRule, route_all, format_routing_report


def build_router_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Route tracebacks to destinations by rule.")
    p.add_argument("rules_file", help="JSON file with routing rules")
    p.add_argument("input", nargs="?", help="Traceback file (default: stdin)")
    p.add_argument("--default", default="default", help="Default destination name")
    p.add_argument("--summary", action="store_true", help="Print routing summary")
    return p


def _load_config(path: str, default: str) -> RouterConfig:
    with open(path) as f:
        data = json.load(f)
    rules = [
        RouteRule(
            destination=r["destination"],
            exc_type=r.get("exc_type"),
            exc_message=r.get("exc_message"),
            filename_contains=r.get("filename_contains"),
        )
        for r in data.get("rules", [])
    ]
    return RouterConfig(rules=rules, default_destination=default)


def main(argv=None) -> None:
    parser = build_router_parser()
    args = parser.parse_args(argv)

    try:
        config = _load_config(args.rules_file, args.default)
    except FileNotFoundError:
        print(f"rules file not found: {args.rules_file}", file=sys.stderr)
        sys.exit(1)

    if args.input:
        try:
            text = open(args.input).read()
        except FileNotFoundError:
            print(f"file not found: {args.input}", file=sys.stderr)
            sys.exit(1)
    else:
        text = sys.stdin.read()

    tb = parse(text)
    grouped = route_all([tb], config)
    if args.summary:
        print(format_routing_report(grouped))
    else:
        for dest, entries in sorted(grouped.items()):
            for rt in entries:
                print(f"{dest}: {rt.traceback.exc_type}")
