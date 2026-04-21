"""catalyst.py – identify the root-cause frame that most likely triggered an exception.

A 'catalyst' is the deepest user frame whose function name or surrounding
context matches a heuristic set of fault indicators (assignments to None,
index errors, attribute lookups, etc.).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, List

from .parser import Frame, Traceback
from .summarizer import _categorize

# Patterns that suggest a frame is the direct cause of an exception.
_FAULT_PATTERNS: List[re.Pattern] = [
    re.compile(r"\bNone\b"),
    re.compile(r"\b\w+\[.+\]"),          # subscript access
    re.compile(r"\b\w+\.\w+"),           # attribute access
    re.compile(r"raise\s+\w+"),           # explicit raise
    re.compile(r"assert\s+"),             # assertion
    re.compile(r"=\s*None"),              # assignment to None
]


@dataclass
class CatalystResult:
    frame: Optional[Frame]
    """The frame identified as the root cause, or None if undetermined."""
    confidence: float
    """0.0 – 1.0 confidence score."""
    reason: str
    """Human-readable explanation."""


def _fault_score(frame: Frame) -> float:
    """Return a 0-1 score reflecting how many fault patterns match the frame."""
    if not frame.line:
        return 0.0
    hits = sum(1 for p in _FAULT_PATTERNS if p.search(frame.line))
    return min(hits / len(_FAULT_PATTERNS), 1.0)


def find_catalyst(tb: Traceback) -> CatalystResult:
    """Identify the most-likely root-cause frame in *tb*."""
    user_frames = [f for f in tb.frames if _categorize(f) == "user"]

    if not user_frames:
        # Fall back to the deepest frame regardless of category.
        if not tb.frames:
            return CatalystResult(frame=None, confidence=0.0, reason="no frames")
        candidate = tb.frames[-1]
        return CatalystResult(
            frame=candidate,
            confidence=0.1,
            reason="no user frames; using deepest frame",
        )

    # Score each user frame; prefer deeper frames (higher index) on ties.
    scored = [
        (i, f, _fault_score(f))
        for i, f in enumerate(user_frames)
    ]
    # Sort: primary key = score descending, secondary = index descending.
    scored.sort(key=lambda t: (t[2], t[1]), reverse=True)
    _, best_frame, best_score = scored[0]

    if best_score == 0.0:
        # No pattern matched – just return the deepest user frame.
        best_frame = user_frames[-1]
        return CatalystResult(
            frame=best_frame,
            confidence=0.3,
            reason="deepest user frame (no fault pattern matched)",
        )

    return CatalystResult(
        frame=best_frame,
        confidence=round(0.4 + best_score * 0.6, 3),
        reason=f"fault pattern matched in '{best_frame.function}'",
    )


def format_catalyst(result: CatalystResult, *, color: bool = True) -> str:
    """Return a human-readable summary of the catalyst result."""
    if result.frame is None:
        return "Catalyst: undetermined"

    f = result.frame
    pct = int(result.confidence * 100)
    header = f"Catalyst ({pct}% confidence): {result.reason}"
    location = f"  File \"{f.filename}\", line {f.lineno}, in {f.function}"
    source = f"    {f.line.strip()}" if f.line else ""

    if color:
        try:
            from .highlighter import highlight_line
            source = f"    {highlight_line(f.line.strip())}" if f.line else ""
        except Exception:
            pass

    parts = [header, location]
    if source:
        parts.append(source)
    return "\n".join(parts)
