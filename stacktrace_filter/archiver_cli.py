"""CLI for appending / listing traceback archives."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from stacktrace_filter.archiver import ArchiveEntry, append_entry, load_archive
from stacktrace_filter.parser import parse


def build_archiver_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-archive",
        description="Append tracebacks to an NDJSON archive or list entries.",
    )
    p.add_argument("archive", help="Path to the NDJSON archive file")
    sub = p.add_subparsers(dest="command")

    ap = sub.add_parser("append", help="Append a traceback to the archive")
    ap.add_argument("input", nargs="?", help="Input file (default: stdin)")
    ap.add_argument("--label", default="", help="Label for this entry")

    lp = sub.add_parser("list", help="List entries in the archive")
    lp.add_argument("--count", action="store_true", help="Print entry count only")
    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_archiver_parser()
    args = parser.parse_args(argv)

    archive_path = Path(args.archive)

    if args.command == "append":
        if args.input:
            inp = Path(args.input)
            if not inp.exists():
                print(f"error: file not found: {inp}", file=sys.stderr)
                sys.exit(1)
            text = inp.read_text(encoding="utf-8")
        else:
            text = sys.stdin.read()

        tb = parse(text)
        entry = ArchiveEntry(traceback=tb, label=args.label)
        append_entry(archive_path, entry)
        print(f"Appended 1 entry to {archive_path}")

    elif args.command == "list":
        if not archive_path.exists():
            print(f"error: archive not found: {archive_path}", file=sys.stderr)
            sys.exit(1)
        entries = list(load_archive(archive_path))
        if args.count:
            print(len(entries))
        else:
            for i, e in enumerate(entries):
                ts = e.timestamp
                label = f" [{e.label}]" if e.label else ""
                exc = e.traceback.exception or "(no exception)"
                print(f"{i:4d}  ts={ts:.3f}{label}  {exc}")
    else:
        parser.print_help()
        sys.exit(1)
