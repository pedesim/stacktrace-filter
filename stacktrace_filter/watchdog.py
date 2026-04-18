"""Watch a log file and filter new tracebacks as they appear."""
from __future__ import annotations

import time
import sys
from pathlib import Path
from typing import Callable, Optional

from .parser import parse, Traceback
from .formatter import format_traceback
from .config import FilterConfig


DEFAULT_POLL_INTERVAL = 0.5
_TRACEBACK_HEADER = "Traceback (most recent call last):"


def _collect_block(lines: list[str], start: int) -> tuple[list[str], int]:
    """Collect a traceback block starting at *start*; return (block, next_index)."""
    block: list[str] = []
    i = start
    while i < len(lines):
        line = lines[i]
        block.append(line)
        # A non-indented line after content that doesn't start a new frame signals end
        if len(block) > 2 and not line.startswith(" ") and not line.startswith("\t") and _TRACEBACK_HEADER not in line:
            i += 1
            break
        i += 1
    return block, i


def _extract_tracebacks(text: str) -> list[str]:
    """Return raw traceback strings found in *text*."""
    lines = text.splitlines(keepends=True)
    results: list[str] = []
    i = 0
    while i < len(lines):
        if _TRACEBACK_HEADER in lines[i]:
            block, i = _collect_block(lines, i)
            results.append("".join(block))
        else:
            i += 1
    return results


def watch(
    path: str | Path,
    config: Optional[FilterConfig] = None,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    output: Callable[[str], None] = print,
    color: bool = True,
) -> None:
    """Tail *path* and print formatted tracebacks as they appear. Blocks forever."""
    cfg = config or FilterConfig()
    p = Path(path)
    offset = p.stat().st_size if p.exists() else 0

    while True:
        time.sleep(poll_interval)
        if not p.exists():
            continue
        size = p.stat().st_size
        if size <= offset:
            offset = size  # handle rotation
            continue
        with p.open("r", errors="replace") as fh:
            fh.seek(offset)
            chunk = fh.read()
        offset = p.stat().st_size
        for raw in _extract_tracebacks(chunk):
            try:
                tb = parse(raw)
                output(format_traceback(tb, cfg, color=color))
            except Exception:
                output(raw)
