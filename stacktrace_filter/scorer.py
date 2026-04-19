"""Score tracebacks by relevance for prioritization."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
from stacktrace_filter.parser import Traceback, Frame
from stacktrace_filter.parser import is_stdlib, is_site_package


@dataclass
class ScoredTraceback:
    traceback: Traceback
    score: float
    breakdown: dict = field(default_factory=dict)


def _user_frame_ratio(tb: Traceback) -> float:
    if not tb.frames:
        return 0.0
    user = sum(1 for f in tb.frames if not is_stdlib(f) and not is_site_package(f))
    return user / len(tb.frames)


def _depth_score(tb: Traceback, max_depth: int = 50) -> float:
    return min(len(tb.frames) / max_depth, 1.0)


def _exc_type_score(tb: Traceback) -> float:
    critical = {"SystemExit", "MemoryError", "KeyboardInterrupt", "RecursionError"}
    warning = {"DeprecationWarning", "UserWarning", "ResourceWarning"}
    exc = tb.exception_type or ""
    if exc in critical:
        return 1.0
    if exc in warning:
        return 0.2
    return 0.5


def score_traceback(
    tb: Traceback,
    weight_user: float = 0.5,
    weight_depth: float = 0.3,
    weight_exc: float = 0.2,
) -> ScoredTraceback:
    u = _user_frame_ratio(tb)
    d = _depth_score(tb)
    e = _exc_type_score(tb)
    total = weight_user * u + weight_depth * d + weight_exc * e
    return ScoredTraceback(
        traceback=tb,
        score=round(total, 4),
        breakdown={"user_ratio": u, "depth": d, "exc_type": e},
    )


def score_all(tracebacks: List[Traceback], **kwargs) -> List[ScoredTraceback]:
    scored = [score_traceback(tb, **kwargs) for tb in tracebacks]
    scored.sort(key=lambda s: s.score, reverse=True)
    return scored


def format_scored(scored: List[ScoredTraceback], color: bool = True) -> str:
    lines = []
    for i, s in enumerate(scored, 1):
        exc = s.traceback.exception_type or "Unknown"
        msg = s.traceback.exception_message or ""
        prefix = f"[{i}] score={s.score:.4f}"
        if color:
            prefix = f"\033[33m{prefix}\033[0m"
        lines.append(f"{prefix}  {exc}: {msg}")
        bd = s.breakdown
        lines.append(
            f"     user={bd['user_ratio']:.2f}  depth={bd['depth']:.2f}  exc={bd['exc_type']:.2f}"
        )
    return "\n".join(lines)
