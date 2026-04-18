"""CLI entry point for stacktrace-filter."""

import argparse
import sys

from .parser import parse
from .formatter import format_traceback


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-filter",
        description="Collapse and highlight relevant lines in Python tracebacks.",
    )
    p.add_argument(
        "file",
        nargs="?",
        help="File containing a traceback (default: stdin).",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI color output.",
    )
    p.add_argument(
        "--show-stdlib",
        action="store_true",
        default=False,
        help="Show stdlib frames instead of collapsing them.",
    )
    p.add_argument(
        "--show-site-packages",
        action="store_true",
        default=False,
        help="Show site-package frames instead of collapsing them.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.file:
        try:
            text = open(args.file).read()
        except OSError as exc:
            print(f"stacktrace-filter: {exc}", file=sys.stderr)
            return 1
    else:
        text = sys.stdin.read()

    tb = parse(text)
    if tb is None:
        print(text, end="")
        return 0

    output = format_traceback(
        tb,
        color=not args.no_color,
        show_stdlib=args.show_stdlib,
        show_site_packages=args.show_site_packages,
    )
    print(output)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
