"""Truncate tracebacks to a maximum number of frames, keeping top and/or bottom."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from stacktrace_filter.parser import Traceback, Frame


@dataclass
class TruncateConfig:
    max_frames: int = 10
    keep_top: int = 3
    keep_bottom: int = 7
    omission_label: str = "... ({{n}} frames omitted) ..."


@dataclass
class TruncatedTraceback:
    original: Traceback
    frames: List[Frame]
    omitted: int

    @property
    def was_truncated(self) -> bool:
        return self.omitted > 0


def truncate(tb: Traceback, config: Optional[TruncateConfig] = None) -> TruncatedTraceback:
    """Return a TruncatedTraceback, collapsing middle frames if needed."""
    if config is None:
        config = TruncateConfig()

    frames = tb.frames
    total = len(frames)

    if total <= config.max_frames:
        return TruncatedTraceback(original=tb, frames=list(frames), omitted=0)

    keep_top = min(config.keep_top, config.max_frames)
    keep_bottom = min(config.keep_bottom, config.max_frames - keep_top)

    top = frames[:keep_top]
    bottom = frames[total - keep_bottom:] if keep_bottom > 0 else []
    omitted = total - keep_top - keep_bottom

    return TruncatedTraceback(
        original=tb,
        frames=list(top) + list(bottom),
        omitted=omitted,
    )


def format_truncated(tt: TruncatedTraceback, config: Optional[TruncateConfig] = None) -> str:
    """Render a TruncatedTraceback to a human-readable string."""
    if config is None:
        config = TruncateConfig()

    lines: List[str] = ["Traceback (most recent call last):"]
    keep_top = config.keep_top

    for i, frame in enumerate(tt.frames):
        lines.append(f'  File "{frame.filename}", line {frame.lineno}, in {frame.name}')
        if frame.line:
            lines.append(f"    {frame.line}")
        if tt.was_truncated and i == keep_top - 1:
            label = config.omission_label.replace("{{n}}", str(tt.omitted))
            lines.append(f"  {label}")

    lines.append(tt.original.exception_line)
    return "\n".join(lines)
