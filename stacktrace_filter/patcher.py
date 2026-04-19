"""Patch (rewrite) frame paths in a traceback using prefix substitution rules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from stacktrace_filter.parser import Frame, Traceback


@dataclass
class PatchRule:
    """Replace *prefix* in frame filenames with *replacement*."""
    prefix: str
    replacement: str

    def apply(self, path: str) -> str:
        if path.startswith(self.prefix):
            return self.replacement + path[len(self.prefix):]
        return path


@dataclass
class PatchResult:
    traceback: Traceback
    patched_count: int


@dataclass
class PatcherConfig:
    rules: List[PatchRule] = field(default_factory=list)


def _patch_frame(frame: Frame, rules: List[PatchRule]) -> tuple[Frame, bool]:
    original = frame.filename
    patched = original
    for rule in rules:
        patched = rule.apply(patched)
        if patched != original:
            break
    changed = patched != original
    if changed:
        frame = Frame(
            filename=patched,
            lineno=frame.lineno,
            name=frame.name,
            line=frame.line,
        )
    return frame, changed


def patch(tb: Traceback, config: PatcherConfig) -> PatchResult:
    """Return a new Traceback with frame filenames rewritten per *config*."""
    new_frames: List[Frame] = []
    patched_count = 0
    for frame in tb.frames:
        new_frame, changed = _patch_frame(frame, config.rules)
        new_frames.append(new_frame)
        if changed:
            patched_count += 1
    new_tb = Traceback(frames=new_frames, exception=tb.exception)
    return PatchResult(traceback=new_tb, patched_count=patched_count)


def format_patch_result(result: PatchResult) -> str:
    lines = [f"Patched {result.patched_count} frame(s)."]
    for frame in result.traceback.frames:
        lines.append(f"  {frame.filename}:{frame.lineno} in {frame.name}")
    if result.traceback.exception:
        lines.append(result.traceback.exception)
    return "\n".join(lines)
