"""Format a list of AnnotatedFrames into a readable report section."""
from __future__ import annotations

from typing import List

from .annotator import AnnotatedFrame, render_annotated_frame

_HEADER = 'Annotated Traceback (most recent call last):'
_SEP = '-' * 60


def format_annotated_traceback(
    frames: List[AnnotatedFrame],
    exception_line: str = '',
    color: bool = False,
    show_sep: bool = True,
) -> str:
    """Render all annotated frames plus optional exception line."""
    parts = [_HEADER]
    for af in frames:
        if show_sep:
            parts.append(_SEP)
        parts.append(render_annotated_frame(af, color=color))
    if show_sep:
        parts.append(_SEP)
    if exception_line:
        if color:
            exception_line = f'\033[31m{exception_line}\033[0m'
        parts.append(exception_line)
    return '\n'.join(parts)


def format_locals_table(locals_snapshot: dict, indent: int = 6) -> str:
    """Render a locals dict as an aligned two-column table."""
    if not locals_snapshot:
        return ''
    pad = ' ' * indent
    max_key = max(len(k) for k in locals_snapshot)
    rows = [f'{pad}{k:<{max_key}} = {v}' for k, v in locals_snapshot.items()]
    return '\n'.join(rows)
