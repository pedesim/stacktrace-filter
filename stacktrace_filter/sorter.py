"""Sort and rank tracebacks by various criteria."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List

from stacktrace_filter.parser import Traceback


@dataclass
class RankedTraceback:
    traceback: Traceback
    score: float
    rank: int


def _score_by_depth(tb: Traceback) -> float:
    return float(len(tb.frames))


def _score_by_user_frames(tb: Traceback) -> float:
    from stacktrace_filter.parser import is_stdlib, is_site_package
    return float(sum(
        1 for f in tb.frames
        if not is_stdlib(f) and not is_site_package(f)
    ))


def _score_by_exc_type(tb: Traceback) -> float:
    """Alphabetical score — useful for grouping, not true ranking."""
    return float(sum(ord(c) for c in (tb.exc_type or "")))


_STRATEGIES: dict[str, Callable[[Traceback], float]] = {
    "depth": _score_by_depth,
    "user_frames": _score_by_user_frames,
    "exc_type": _score_by_exc_type,
}


def sort_tracebacks(
    tracebacks: List[Traceback],
    strategy: str = "depth",
    descending: bool = True,
) -> List[RankedTraceback]:
    """Return tracebacks sorted and ranked by *strategy*.

    Parameters
    ----------
    tracebacks:
        Sequence of :class:`Traceback` objects to rank.
    strategy:
        One of ``'depth'``, ``'user_frames'``, or ``'exc_type'``.
    descending:
        When *True* (default) highest score comes first.
    """
    if strategy not in _STRATEGIES:
        raise ValueError(
            f"Unknown strategy {strategy!r}. Choose from: {sorted(_STRATEGIES)}"
        )
    scorer = _STRATEGIES[strategy]
    scored = sorted(
        tracebacks,
        key=scorer,
        reverse=descending,
    )
    return [
        RankedTraceback(traceback=tb, score=scorer(tb), rank=idx + 1)
        for idx, tb in enumerate(scored)
    ]


def format_ranked(ranked: List[RankedTraceback]) -> str:
    """Return a compact text summary of ranked tracebacks."""
    lines: list[str] = []
    for r in ranked:
        exc = r.traceback.exc_type or "(unknown)"
        msg = (r.traceback.exc_message or "")[:60]
        lines.append(f"#{r.rank:>3}  score={r.score:.0f}  {exc}: {msg}")
    return "\n".join(lines)
