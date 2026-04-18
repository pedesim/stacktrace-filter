"""CLI entry-point for the watchdog (tail) feature."""
from __future__ import annotations

import argparse
import sys
from .watchdog import watch
from .config import FilterConfig


def build_watchdog_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stf-watch",
        description="Tail a log file and pretty-print tracebacks as they appear.",
    )
    p.add_argument("file", help="Log file to watch")
    p.add_argument(
        "--poll-interval",
        type=float,
        default=0.5,
        metavar="SECONDS",
        help="Polling interval in seconds (default: 0.5)",
    )
    p.add_argument("--no-color", action="store_true", help="Disable ANSI colors")
    p.add_argument(
        "--hide-stdlib",
        action="store_true",
        default=False,
        help="Hide stdlib frames",
    )
    p.add_argument(
        "--hide-site-packages",
        action="store_true",
        default=False,
        help="Hide site-package frames",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_watchdog_parser()
    args = parser.parse_args(argv)

    cfg = FilterConfig(
        hide_stdlib=args.hide_stdlib,
        hide_site_packages=args.hide_site_packages,
    )

    try:
        watch(
            path=args.file,
            config=cfg,
            poll_interval=args.poll_interval,
            color=not args.no_color,
        )
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
