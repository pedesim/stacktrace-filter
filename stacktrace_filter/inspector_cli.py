"""CLI entry-point for the inspector sub-command."""
from __future__ import annotations

import argparse
import sys

from .io_utils import read_source
from .parser import parse
from .inspector import inspect, format_inspection


def build_inspector_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(description="Inspect a single traceback and report key facts.")
    if parent is not None:
        parser = parent.add_parser("inspect", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument(
        "file",
        nargs="?",
        default="-",
        help="Path to traceback file (default: stdin).",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI colour output.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output inspection result as JSON.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_inspector_parser()
    args = parser.parse_args(argv)

    try:
        text = read_source(args.file)
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    tb = parse(text)
    result = inspect(tb)

    if args.json:
        import json
        deepest = None
        if result.deepest_user_frame:
            f = result.deepest_user_frame
            deepest = {"filename": f.filename, "lineno": f.lineno, "function": f.function}
        data = {
            "exc_type": result.exc_type,
            "exc_message": result.exc_message,
            "total_frames": result.total_frames,
            "user_frames": result.user_frames,
            "stdlib_frames": result.stdlib_frames,
            "library_frames": result.library_frames,
            "user_ratio": result.user_ratio,
            "deepest_user_frame": deepest,
            "unique_files": result.unique_files,
            "unique_functions": result.unique_functions,
        }
        print(json.dumps(data, indent=2))
    else:
        print(format_inspection(result, color=not args.no_color))


if __name__ == "__main__":  # pragma: no cover
    main()
