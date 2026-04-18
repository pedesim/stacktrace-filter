"""Format parsed tracebacks with optional collapsing and ANSI highlighting."""
from __future__ import annotations

from typing import List

from .parser import Frame, Traceback

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"


def _colorize(text: str, *codes: str) -> str:
    return "".join(codes) + text + RESET


def format_frame(frame: Frame, *, color: bool = True, dim: bool = False) -> str:
    prefix = "  "
    path_str = f'File "{frame.path}", line {frame.lineno}, in {frame.func}'
    if color:
        if dim:
            path_str = _colorize(path_str, DIM)
        else:
            path_str = _colorize(f'File "{frame.path}"', CYAN) + \
                       f', line ' + _colorize(str(frame.lineno), YELLOW) + \
                       f', in ' + _colorize(frame.func, BOLD)
    lines = [prefix + path_str]
    if frame.code:
        code_str = f"    {frame.code}"
        if color and not dim:
            code_str = _colorize(code_str, BOLD)
        lines.append(code_str)
    return "\n".join(lines)


def format_traceback(
    tb: Traceback,
    *,
    collapse_stdlib: bool = True,
    collapse_site_packages: bool = False,
    color: bool = True,
) -> str:
    output: List[str] = ["Traceback (most recent call last):"]
    collapsed = 0

    def flush_collapsed() -> None:
        nonlocal collapsed
        if collapsed:
            msg = f"  ... ({collapsed} frame{'s' if collapsed > 1 else ''} collapsed)"
            output.append(_colorize(msg, DIM) if color else msg)
            collapsed = 0

    for frame in tb.frames:
        should_collapse = (collapse_stdlib and frame.is_stdlib and not frame.is_site_package) or \
                          (collapse_site_packages and frame.is_site_package)
        if should_collapse:
            collapsed += 1
        else:
            flush_collapsed()
            output.append(format_frame(frame, color=color, dim=False))

    flush_collapsed()

    if tb.exception:
        exc_line = tb.exception
        if tb.message:
            exc_line += f": {tb.message}"
        output.append(_colorize(exc_line, BOLD, RED) if color else exc_line)

    return "\n".join(output)
