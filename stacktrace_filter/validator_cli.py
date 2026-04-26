"""CLI entry-point for the traceback validator."""
from __future__ import annotations

import argparse
import sys

from stacktrace_filter.io_utils import read_source
from stacktrace_filter.parser import parse
from stacktrace_filter.validator import ValidatorConfig, format_validation, validate


def build_validator_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-validate",
        description="Validate a Python traceback against configurable rules.",
    )
    p.add_argument(
        "file",
        nargs="?",
        default="-",
        help="Traceback file to read (default: stdin)",
    )
    p.add_argument(
        "--max-depth",
        type=int,
        default=None,
        metavar="N",
        help="Fail if the traceback has more than N frames",
    )
    p.add_argument(
        "--require-user-frame",
        action="store_true",
        default=False,
        help="Fail if there are no user-code frames",
    )
    p.add_argument(
        "--forbidden-filename",
        action="append",
        default=[],
        dest="forbidden_filenames",
        metavar="PATTERN",
        help="Fail if any frame filename contains PATTERN (repeatable)",
    )
    p.add_argument(
        "--forbidden-function",
        action="append",
        default=[],
        dest="forbidden_functions",
        metavar="PATTERN",
        help="Fail if any frame function contains PATTERN (repeatable)",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI colour output",
    )
    p.add_argument(
        "--exit-code",
        action="store_true",
        default=False,
        help="Exit with code 1 when validation fails",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_validator_parser()
    args = parser.parse_args(argv)

    try:
        source = read_source(args.file)
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        sys.exit(2)

    tb = parse(source)
    cfg = ValidatorConfig(
        max_depth=args.max_depth,
        require_user_frame=args.require_user_frame,
        forbidden_filenames=args.forbidden_filenames,
        forbidden_functions=args.forbidden_functions,
    )
    result = validate(tb, cfg)
    print(format_validation(result, color=not args.no_color))

    if args.exit_code and not result.is_valid:
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
