"""Format parsed tracebacks for terminal output."""
from __future__ import annotations

from typing import List, Optional

from .parser import Frame, Traceback
from .config import FilterConfig, should_hide
from .highlighter import highlight_line, highlight_exception_line

_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_BLUE = "\033[34m"
_RED = "\033[31m"
_YELLOW = "\033[33m"


def _colorize(text: str, code: str, color: bool) -> str:
    if not color:
        return text
    return f"{code}{text}{_RESET}"


def flush_collapsed(count: int, label: str, color: bool) -> Optional[str]:
    if count == 0:
        return None
    msg = f"  ... {count} {label} frame(s) collapsed ..."
    return _colorize(msg, _DIM, color)


def format_frame(frame: Frame, color: bool = True) -> List[str]:
    """Return lines representing a single stack frame."""
    lines = []
    location = f'  File "{frame.filename}", line {frame.lineno}, in {frame.name}'
    lines.append(_colorize(location, _BLUE, color))
    if frame.line:
        highlighted = highlight_line(f"    {frame.line}", color=color)
        lines.append(highlighted)
    return lines


def format_traceback(
    tb: Traceback,
    config: Optional[FilterConfig] = None,
    color: bool = True,
) -> str:
    """Format a full Traceback object into a string ready for display."""
    if config is None:
        config = FilterConfig()

    output_lines: List[str] = []
    output_lines.append(_colorize("Traceback (most recent call last):", _BOLD, color))

    collapsed_count = 0
    collapsed_label = config.collapse_label

    for frame in tb.frames:
        if should_hide(frame, config):
            collapsed_count += 1
        else:
            flushed = flush_collapsed(collapsed_count, collapsed_label, color)
            if flushed:
                output_lines.append(flushed)
            collapsed_count = 0
            output_lines.extend(format_frame(frame, color=color))

    flushed = flush_collapsed(collapsed_count, collapsed_label, color)
    if flushed:
        output_lines.append(flushed)

    if tb.exception:
        output_lines.append(highlight_exception_line(tb.exception, color=color))

    return "\n".join(output_lines)
