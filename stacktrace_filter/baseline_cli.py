"""CLI for baseline capture and regression detection."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .baseline import compare_to_baseline, load_baseline, save_baseline
from .io_utils import read_source
from .parser import parse


def build_baseline_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-baseline",
        description="Capture or compare tracebacks against a baseline.",
    )
    p.add_argument(
        "mode",
        choices=["capture", "compare"],
        help="'capture' saves current tracebacks as baseline; 'compare' checks for regressions.",
    )
    p.add_argument(
        "--baseline",
        default="baseline.json",
        metavar="FILE",
        help="Path to baseline JSON file (default: baseline.json).",
    )
    p.add_argument(
        "input",
        nargs="?",
        metavar="FILE",
        help="Input traceback file (default: stdin).",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable colored output.",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_baseline_parser()
    args = parser.parse_args(argv)

    if args.input:
        p = Path(args.input)
        if not p.exists():
            print(f"error: file not found: {args.input}", file=sys.stderr)
            sys.exit(1)
        text = read_source(p)
    else:
        text = sys.stdin.read()

    tb = parse(text)
    tracebacks = [tb] if tb.frames else []

    baseline_path = Path(args.baseline)

    if args.mode == "capture":
        save_baseline(tracebacks, baseline_path)
        print(f"Baseline saved to {baseline_path} ({len(tracebacks)} traceback(s)).")
        return

    # compare mode
    if not baseline_path.exists():
        print(f"error: baseline file not found: {baseline_path}", file=sys.stderr)
        sys.exit(1)

    baseline = load_baseline(baseline_path)
    report = compare_to_baseline(tracebacks, baseline)

    print(f"New (regressions) : {report.regression_count}")
    print(f"Resolved          : {report.resolved_count}")
    print(f"Persisted         : {len(report.persisted)}")

    if report.new:
        print("\nNew fingerprints:")
        for fp in report.new:
            print(f"  [{fp.short}] {fp.full}")

    if report.resolved:
        print("\nResolved fingerprints:")
        for fp_str in report.resolved:
            entry = baseline[fp_str]
            print(f"  [{entry.short}] {entry.exc_type}: {entry.exc_message[:60]}")
