"""Prune frames from tracebacks based on configurable depth and pattern rules."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
import re

from stacktrace_filter.parser import Frame, Traceback


@dataclass
class PruneConfig:
    max_frames: Optional[int] = None
    drop_filenames: List[str] = field(default_factory=list)
    drop_functions: List[str] = field(default_factory=list)
    keep_last: int = 1  # always keep this many frames at the bottom

    def __post_init__(self):
        self._fn_patterns = [re.compile(p) for p in self.drop_filenames]
        self._func_patterns = [re.compile(p) for p in self.drop_functions]


@dataclass
class PruneResult:
    traceback: Traceback
    original_count: int
    pruned_count: int

    @property
    def delta(self) -> int:
        return self.original_count - self.pruned_count


def _should_drop(frame: Frame, config: PruneConfig) -> bool:
    for pat in config._fn_patterns:
        if pat.search(frame.filename):
            return True
    for pat in config._func_patterns:
        if pat.search(frame.function):
            return True
    return False


def prune(tb: Traceback, config: PruneConfig) -> PruneResult:
    original = list(tb.frames)
    original_count = len(original)

    # apply pattern-based drops, but preserve the last `keep_last` frames
    protected = set(range(max(0, original_count - config.keep_last), original_count))
    kept = [
        f for i, f in enumerate(original)
        if i in protected or not _should_drop(f, config)
    ]

    # apply max_frames cap (keep tail)
    if config.max_frames is not None and len(kept) > config.max_frames:
        overflow = len(kept) - config.max_frames
        kept = kept[overflow:]

    pruned_tb = Traceback(frames=kept, exception=tb.exception)
    return PruneResult(
        traceback=pruned_tb,
        original_count=original_count,
        pruned_count=len(kept),
    )


def format_prune_result(result: PruneResult, color: bool = False) -> str:
    lines = []
    if result.delta:
        msg = f"[pruner] removed {result.delta} frame(s) ({result.pruned_count} remaining)"
        lines.append(f"\033[33m{msg}\033[0m" if color else msg)
    for frame in result.traceback.frames:
        lines.append(f"  File \"{frame.filename}\", line {frame.lineno}, in {frame.function}")
    if result.traceback.exception:
        lines.append(result.traceback.exception)
    return "\n".join(lines)
