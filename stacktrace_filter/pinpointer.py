"""Pinpointer: identify the most likely root-cause frame in a traceback."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .parser import Frame, Traceback
from .parser import is_stdlib, is_site_package


@dataclass
class PinpointResult:
    traceback: Traceback
    frame: Optional[Frame]
    index: Optional[int]          # position in traceback.frames
    reason: str


def _is_user_frame(frame: Frame) -> bool:
    return not is_stdlib(frame) and not is_site_package(frame)


def _score_frame(frame: Frame, exc_message: str) -> int:
    """Higher score → more likely to be the root-cause frame."""
    score = 0
    if _is_user_frame(frame):
        score += 10
    # Prefer frames whose filename appears in the exception message
    if frame.filename and frame.filename in exc_message:
        score += 5
    # Prefer frames whose function name appears in the exception message
    if frame.function and frame.function in exc_message:
        score += 3
    # Prefer frames closer to the bottom of the stack (innermost)
    return score


def pinpoint(tb: Traceback) -> PinpointResult:
    """Return the single frame most likely responsible for *tb*.

    Strategy:
    1. Score every frame; pick the highest-scoring one.
    2. Tie-break: prefer the innermost (last) frame.
    3. If no frames exist, return a result with frame=None.
    """
    if not tb.frames:
        return PinpointResult(
            traceback=tb,
            frame=None,
            index=None,
            reason="no frames",
        )

    exc_msg = tb.exception or ""
    scores: List[int] = [_score_frame(f, exc_msg) for f in tb.frames]

    best_score = max(scores)
    # Walk from the end so tie-breaks favour innermost frames
    best_idx = max(
        (i for i, s in enumerate(scores) if s == best_score),
        key=lambda i: i,
    )

    frame = tb.frames[best_idx]
    if _is_user_frame(frame):
        reason = "highest-scoring user frame"
    else:
        reason = "highest-scoring frame (no user frames found)"

    return PinpointResult(
        traceback=tb,
        frame=frame,
        index=best_idx,
        reason=reason,
    )


def format_pinpoint(result: PinpointResult, *, color: bool = True) -> str:
    """Render a human-readable summary of the pinpoint result."""
    if result.frame is None:
        return "[pinpointer] No frames to analyse."

    f = result.frame
    loc = f"{f.filename}:{f.lineno}" if f.filename else "<unknown>"
    fn = f.function or "<unknown>"
    lines = [
        f"[pinpointer] Most likely root-cause frame ({result.reason}):",
        f"  File {loc}, in {fn}",
    ]
    if f.text:
        lines.append(f"    {f.text.strip()}")
    return "\n".join(lines)
