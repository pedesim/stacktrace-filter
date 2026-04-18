"""CLI integration for redacting sensitive locals before formatting."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from stacktrace_filter.redactor import RedactorConfig, redact_annotated_frames
from stacktrace_filter.parser import parse
from stacktrace_filter.annotator import annotate_frames
from stacktrace_filter.locals_parser import extract_frame_locals
from stacktrace_filter.annotation_formatter import format_annotated_traceback
from stacktrace_filter.io_utils import read_source


def build_redactor_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-redact",
        description="Filter and redact sensitive locals from a Python traceback.",
    )
    p.add_argument("file", nargs="?", help="Traceback file (default: stdin)")
    p.add_argument(
        "--pattern",
        dest="patterns",
        action="append",
        metavar="REGEX",
        help="Additional regex pattern to redact (may be repeated)",
    )
    p.add_argument(
        "--placeholder",
        default="<redacted>",
        help="Replacement text for redacted values (default: <redacted>)",
    )
    p.add_argument(
        "--case-sensitive",
        action="store_true",
        default=False,
        help="Match patterns case-sensitively",
    )
    p.add_argument("--no-color", action="store_true", default=False)
    return p


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_redactor_parser()
    args = parser.parse_args(argv)

    try:
        source = read_source(args.file)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    tb = parse(source)
    frame_locals = extract_frame_locals(source)
    annotated = annotate_frames(tb.frames, frame_locals)

    extra = args.patterns or []
    from stacktrace_filter.redactor import DEFAULT_PATTERNS
    cfg = RedactorConfig(
        patterns=list(DEFAULT_PATTERNS) + extra,
        placeholder=args.placeholder,
        case_sensitive=args.case_sensitive,
    )
    annotated = redact_annotated_frames(annotated, cfg)

    color = not args.no_color
    output = format_annotated_traceback(tb, annotated, color=color)
    print(output)


if __name__ == "__main__":  # pragma: no cover
    main()
