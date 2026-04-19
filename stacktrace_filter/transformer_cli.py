"""CLI entry-point for the transformer pipeline."""
from __future__ import annotations
import argparse
import sys
from stacktrace_filter.io_utils import read_source
from stacktrace_filter.parser import parse
from stacktrace_filter.transformer import (
    TransformPipeline, drop_frames, limit_frames, transform,
)
from stacktrace_filter.parser import is_stdlib, is_site_package
from stacktrace_filter.formatter import format_traceback


def build_transformer_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-transform",
        description="Apply transforms to a Python traceback.",
    )
    p.add_argument("file", nargs="?", help="Input file (default: stdin)")
    p.add_argument("--drop-stdlib", action="store_true",
                   help="Remove stdlib frames")
    p.add_argument("--drop-site-packages", action="store_true",
                   help="Remove third-party frames")
    p.add_argument("--max-frames", type=int, default=0,
                   help="Keep only the last N frames (0 = unlimited)")
    p.add_argument("--keep", choices=["first", "last"], default="last",
                   help="Which end to keep when --max-frames is set")
    p.add_argument("--no-color", action="store_true",
                   help="Disable ANSI colour output")
    return p


def main(argv=None) -> None:
    parser = build_transformer_parser()
    args = parser.parse_args(argv)

    try:
        source = read_source(args.file)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    tb = parse(source)
    pipeline = TransformPipeline()

    if args.drop_stdlib:
        pipeline.add(drop_frames(lambda f: is_stdlib(f.filename)))
    if args.drop_site_packages:
        pipeline.add(drop_frames(lambda f: is_site_package(f.filename)))
    if args.max_frames > 0:
        pipeline.add(limit_frames(args.max_frames, keep=args.keep))

    result = transform(tb, pipeline)
    color = not args.no_color
    print(format_traceback(result.transformed, color=color))
