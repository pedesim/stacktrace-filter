"""CLI entry point for the labeler feature."""
from __future__ import annotations
import argparse
import json
import sys
from stacktrace_filter.labeler import LabelRule, LabelerConfig, label_all, format_labeled
from stacktrace_filter.parser import parse
from stacktrace_filter.io_utils import read_source


def build_labeler_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stf-labeler",
        description="Label tracebacks using configurable rules.",
    )
    p.add_argument("input", nargs="?", default="-", help="Input file (default: stdin)")
    p.add_argument("--rules", metavar="FILE", help="JSON rules file")
    p.add_argument("--default-label", default="unlabeled", metavar="LABEL")
    p.add_argument("--json", dest="as_json", action="store_true", help="Output JSON")
    return p


def _load_rules(path: str) -> list:
    with open(path) as fh:
        data = json.load(fh)
    return [
        LabelRule(
            label=r["label"],
            exc_type=r.get("exc_type"),
            filename_contains=r.get("filename_contains"),
            message_contains=r.get("message_contains"),
        )
        for r in data
    ]


def main(argv=None) -> None:
    parser = build_labeler_parser()
    args = parser.parse_args(argv)

    rules = _load_rules(args.rules) if args.rules else []
    config = LabelerConfig(rules=rules, default_label=args.default_label)

    try:
        source = read_source(args.input)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    tb = parse(source)
    labeled = label_all([tb], config)

    if args.as_json:
        out = [{"labels": lt.labels, "exc_type": lt.traceback.exc_type,
                "exc_message": lt.traceback.exc_message} for lt in labeled]
        print(json.dumps(out, indent=2))
    else:
        for lt in labeled:
            print(format_labeled(lt))
