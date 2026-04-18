"""Group multiple tracebacks by their exception type and message."""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import defaultdict
from typing import List, Dict, Tuple
from .parser import Traceback


@dataclass
class TracebackGroup:
    key: Tuple[str, str]  # (exc_type, exc_message)
    tracebacks: List[Traceback] = field(default_factory=list)

    @property
    def exc_type(self) -> str:
        return self.key[0]

    @property
    def exc_message(self) -> str:
        return self.key[1]

    @property
    def count(self) -> int:
        return len(self.tracebacks)


def _group_key(tb: Traceback) -> Tuple[str, str]:
    """Return a stable key for grouping."""
    exc_type = tb.exc_type or ""
    # Normalise message: strip leading/trailing whitespace
    exc_msg = (tb.exc_message or "").strip()
    return (exc_type, exc_msg)


def group_tracebacks(tracebacks: List[Traceback]) -> List[TracebackGroup]:
    """Group tracebacks by (exc_type, exc_message).

    Groups are returned ordered by descending count.
    """
    buckets: Dict[Tuple[str, str], TracebackGroup] = defaultdict(
        lambda: TracebackGroup(key=("", ""))  # placeholder
    )
    for tb in tracebacks:
        key = _group_key(tb)
        if key not in buckets:
            buckets[key] = TracebackGroup(key=key)
        buckets[key].tracebacks.append(tb)
    return sorted(buckets.values(), key=lambda g: g.count, reverse=True)


def format_groups(groups: List[TracebackGroup], *, color: bool = True) -> str:
    """Render a summary table of traceback groups."""
    if not groups:
        return "No tracebacks to group.\n"
    lines = []
    header = f"{'Count':>6}  {'Exception':<40}  Message"
    lines.append(header)
    lines.append("-" * max(len(header), 60))
    for g in groups:
        exc = g.exc_type or "(unknown)"
        msg = g.exc_message or ""
        if len(msg) > 60:
            msg = msg[:57] + "..."
        lines.append(f"{g.count:>6}  {exc:<40}  {msg}")
    return "\n".join(lines) + "\n"
