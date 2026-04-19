"""CLI for replaying archived tracebacks."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from stacktrace_filter.archiver import ArchiveEntry
from stacktrace_filter.replayer import ReplayConfig, replay


def build_replayer_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-replay",
        description="Replay tracebacks from an archive file.",
    )
    p.add_argument("archive", help="Path to JSONL archive file")
    p.add_argument(
        "--delay",
        type=float,
        default=0.0,
        metavar="SECONDS",
        help="Pause between entries (default: 0)",
    )
    p.add_argument(
        "--max",
        type=int,
        default=None,
        dest="max_entries",
        metavar="N",
        help="Maximum number of entries to replay",
    )
    p.add_argument(
        "--reverse",
        action="store_true",
        default=False,
        help="Replay in reverse chronological order",
    )
    p.add_argument(
        "--label",
        default=None,
        help="Only replay entries with this label",
    )
    p.add_argument(
        "--count-only",
        action="store_true",
        default=False,
        help="Print entry count only, do not print tracebacks",
    )
    return p


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_replayer_parser()
    args = parser.parse_args(argv)

    config = ReplayConfig(
        delay=args.delay,
        max_entries=args.max_entries,
        reverse=args.reverse,
        filter_label=args.label,
    )

    printed: list = []

    def _print_entry(entry: ArchiveEntry) -> None:
        if not args.count_only:
            sys.stdout.write(f"[{entry.label}] {entry.traceback.exception}\n")
            for frame in entry.traceback.frames:
                sys.stdout.write(f"  {frame.filename}:{frame.lineno} in {frame.function}\n")
            sys.stdout.write("\n")
        printed.append(entry)

    try:
        result = replay(args.archive, config=config, callback=_print_entry)
    except FileNotFoundError:
        sys.stderr.write(f"error: archive file not found: {args.archive}\n")
        sys.exit(1)
    except OSError as exc:
        sys.stderr.write(f"error: could not read archive: {exc}\n")
        sys.exit(1)

    sys.stdout.write(f"Replayed {result.total} entries (skipped {result.skipped}).\n")
