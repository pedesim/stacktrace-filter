"""CLI entry point for timeline feature."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

from stacktrace_filter.parser import parse
from stacktrace_filter.timeline import build_timeline, format_timeline


def build_timeline_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-timeline",
        description="Render tracebacks in chronological order from a JSON manifest.",
    )
    p.add_argument(
        "manifest",
        nargs="?",
        default="-",
        help="JSON file with list of {text, timestamp, label} objects (default: stdin)",
    )
    p.add_argument("--no-color", action="store_true", help="Disable ANSI colors")
    return p


def main(argv=None) -> None:
    parser = build_timeline_parser()
    args = parser.parse_args(argv)

    if args.manifest == "-":
        raw = sys.stdin.read()
    else:
        try:
            with open(args.manifest, encoding="utf-8") as fh:
                raw = fh.read()
        except FileNotFoundError:
            print(f"error: file not found: {args.manifest}", file=sys.stderr)
            sys.exit(1)

    try:
        entries = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON: {exc}", file=sys.stderr)
        sys.exit(1)

    tracebacks, timestamps, labels = [], [], []
    for item in entries:
        tracebacks.append(parse(item["text"]))
        timestamps.append(datetime.fromisoformat(item["timestamp"]))
        labels.append(item.get("label"))

    tl = build_timeline(tracebacks, timestamps, labels)
    print(format_timeline(tl, color=not args.no_color))
