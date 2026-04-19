"""Remove noise frames from tracebacks based on configurable patterns."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_filter.parser import Frame, Traceback


@dataclass
class DenoiserConfig:
    """Configuration for the denoiser."""
    filename_patterns: List[str] = field(default_factory=list)
    function_patterns: List[str] = field(default_factory=list)
    min_frames: int = 1  # never reduce below this many frames

    def __post_init__(self) -> None:
        self._fn_re = [re.compile(p) for p in self.filename_patterns]
        self._func_re = [re.compile(p) for p in self.function_patterns]


@dataclass
class DenoiseResult:
    traceback: Traceback
    removed_count: int
    removed_frames: List[Frame]


def _is_noise(frame: Frame, cfg: DenoiserConfig) -> bool:
    for pat in cfg._fn_re:
        if pat.search(frame.filename):
            return True
    for pat in cfg._func_re:
        if pat.search(frame.function):
            return True
    return False


def denoise(tb: Traceback, cfg: Optional[DenoiserConfig] = None) -> DenoiseResult:
    """Remove noise frames from *tb* according to *cfg*.

    Frames are only removed when the resulting frame list would still contain
    at least ``cfg.min_frames`` entries.
    """
    if cfg is None:
        cfg = DenoiserConfig()

    kept: List[Frame] = []
    removed: List[Frame] = []

    for frame in tb.frames:
        if _is_noise(frame, cfg):
            removed.append(frame)
        else:
            kept.append(frame)

    # Respect min_frames: if we removed too many, put back from the end
    while len(kept) < cfg.min_frames and removed:
        kept.append(removed.pop())

    clean_tb = Traceback(frames=kept, exception=tb.exception)
    return DenoiseResult(traceback=clean_tb, removed_count=len(removed), removed_frames=removed)


def format_denoise_result(result: DenoiseResult) -> str:
    lines = []
    if result.removed_count:
        lines.append(f"[denoiser] removed {result.removed_count} noise frame(s)")
        for f in result.removed_frames:
            lines.append(f"  - {f.filename}:{f.lineno} in {f.function}")
    else:
        lines.append("[denoiser] no noise frames found")
    return "\n".join(lines)
