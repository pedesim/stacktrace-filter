"""Enrich tracebacks with additional context from source files."""
from __future__ import annotations

import linecache
from dataclasses import dataclass, field
from typing import List, Optional

from .parser import Frame, Traceback


@dataclass
class EnrichedFrame:
    frame: Frame
    source_line: Optional[str] = None
    context_before: List[str] = field(default_factory=list)
    context_after: List[str] = field(default_factory=list)

    @property
    def has_source(self) -> bool:
        return self.source_line is not None


@dataclass
class EnrichedTraceback:
    original: Traceback
    frames: List[EnrichedFrame]
    exception_type: str
    exception_message: str


def _get_line(filename: str, lineno: int) -> Optional[str]:
    line = linecache.getline(filename, lineno)
    return line.rstrip("\n") if line else None


def _get_context(filename: str, lineno: int, context: int) -> tuple[List[str], List[str]]:
    before = []
    after = []
    for i in range(max(1, lineno - context), lineno):
        line = _get_line(filename, i)
        if line is not None:
            before.append(line)
    for i in range(lineno + 1, lineno + context + 1):
        line = _get_line(filename, i)
        if line is not None:
            after.append(line)
    return before, after


def enrich_frame(frame: Frame, context: int = 2) -> EnrichedFrame:
    """Enrich a single frame with source context."""
    source_line = _get_line(frame.filename, frame.lineno)
    if context > 0 and source_line is not None:
        before, after = _get_context(frame.filename, frame.lineno, context)
    else:
        before, after = [], []
    return EnrichedFrame(
        frame=frame,
        source_line=source_line,
        context_before=before,
        context_after=after,
    )


def enrich(tb: Traceback, context: int = 2) -> EnrichedTraceback:
    """Enrich all frames in a traceback with source context."""
    enriched_frames = [enrich_frame(f, context=context) for f in tb.frames]
    return EnrichedTraceback(
        original=tb,
        frames=enriched_frames,
        exception_type=tb.exception_type,
        exception_message=tb.exception_message,
    )


def format_enriched_frame(ef: EnrichedFrame, color: bool = False) -> str:
    """Render an enriched frame as a string with optional context lines."""
    lines = []
    indent = "    "
    for line in ef.context_before:
        lines.append(f"{indent}  {line}")
    if ef.source_line is not None:
        marker = ">>" if color else ">>"
        lines.append(f"{indent}{marker} {ef.source_line}")
    for line in ef.context_after:
        lines.append(f"{indent}  {line}")
    return "\n".join(lines)
