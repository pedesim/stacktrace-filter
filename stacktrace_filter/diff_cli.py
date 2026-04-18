"""CLI entry point for diffing two traceback files."""
import argparse
import sys
from .io_utils import read_source
from .parser import parse
from .differ import diff_tracebacks, format_diff


def build_diff_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-diff",
        description="Compare two Python tracebacks and show differing frames.",
    )
    p.add_argument("left", help="First traceback file (or '-' for stdin)")
    p.add_argument("right", help="Second traceback file")
    p.add_argument("--no-color", action="store_true", help="Disable ANSI color output")
    return p


def main(argv=None) -> int:
    parser = build_diff_parser()
    args = parser.parse_args(argv)

    try:
        left_text = read_source(None if args.left == "-" else args.left)
        right_text = read_source(args.right)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    left_tb = parse(left_text)
    right_tb = parse(right_text)

    result = diff_tracebacks(left_tb, right_tb)
    print(format_diff(result, color=not args.no_color))
    return 0


if __name__ == "__main__":
    sys.exit(main())
