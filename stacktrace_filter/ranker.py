"""Rank tracebacks by a composite relevance score."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence

from .parser import Traceback
from .summarizer import summarize


@dataclass
class RankedEntry:
    traceback: Traceback
    score: float
    breakdown: dict = field(default_factory=dict)


# ---------- individual scoring components ----------

def _user_frame_score(tb: Traceback) -> float:
    """Fraction of frames that are user code (0-1)."""
    if not tb.frames:
        return 0.0
    user = sum(1 for f in tb.frames if not f.is_stdlib and not f.is_site_package)
    return user / len(tb.frames)


def _depth_score(tb: Traceback, max_depth: int = 30) -> float:
    """Deeper tracebacks are more interesting, capped at max_depth."""
    return min(len(tb.frames) / max_depth, 1.0)


def _exc_type_score(tb: Traceback) -> float:
    """Penalise common 'noisy' exception types."""
    noisy = {"KeyboardInterrupt", "SystemExit", "GeneratorExit", "StopIteration"}
    if tb.exc_type in noisy:
        return 0.0
    if tb.exc_type in {"RuntimeError", "AssertionError"}:
        return 0.5
    return 1.0


def _deepest_user_score(tb: Traceback) -> float:
    """Reward tracebacks whose deepest user frame is near the bottom."""
    summary = summarize(tb)
    if summary.deepest_user_frame is None:
        return 0.0
    idx = tb.frames.index(summary.deepest_user_frame)
    return (idx + 1) / len(tb.frames) if tb.frames else 0.0


# ---------- public API ----------

WEIGHTS = {
    "user_frame": 0.35,
    "depth": 0.20,
    "exc_type": 0.25,
    "deepest_user": 0.20,
}


def rank_traceback(tb: Traceback) -> RankedEntry:
    breakdown = {
        "user_frame": _user_frame_score(tb),
        "depth": _depth_score(tb),
        "exc_type": _exc_type_score(tb),
        "deepest_user": _deepest_user_score(tb),
    }
    score = sum(breakdown[k] * WEIGHTS[k] for k in breakdown)
    return RankedEntry(traceback=tb, score=round(score, 4), breakdown=breakdown)


def rank_tracebacks(
    tracebacks: Sequence[Traceback],
    ascending: bool = False,
) -> List[RankedEntry]:
    """Return tracebacks wrapped in RankedEntry, sorted by score."""
    ranked = [rank_traceback(tb) for tb in tracebacks]
    ranked.sort(key=lambda e: e.score, reverse=not ascending)
    return ranked


def format_rank(entry: RankedEntry, index: int = 0) -> str:
    bd = entry.breakdown
    lines = [
        f"[#{index + 1}] score={entry.score:.4f}  exc={entry.traceback.exc_type}",
        f"  user_frame={bd['user_frame']:.2f}  depth={bd['depth']:.2f}"
        f"  exc_type={bd['exc_type']:.2f}  deepest_user={bd['deepest_user']:.2f}",
    ]
    return "\n".join(lines)
