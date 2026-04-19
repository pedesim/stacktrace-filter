"""Merge multiple tracebacks into a deduplicated, ranked list."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Sequence
from stacktrace_filter.parser import Traceback
from stacktrace_filter.fingerprint import fingerprint
from stacktrace_filter.sorter import sort_tracebacks, RankedTraceback


@dataclass
class MergeResult:
    tracebacks: List[Traceback]
    dropped: int
    total_input: int

    @property
    def kept(self) -> int:
        return len(self.tracebacks)


def _dedup(tracebacks: Sequence[Traceback]) -> tuple[list[Traceback], int]:
    seen: set[str] = set()
    unique: list[Traceback] = []
    dropped = 0
    for tb in tracebacks:
        fp = fingerprint(tb).full
        if fp in seen:
            dropped += 1
        else:
            seen.add(fp)
            unique.append(tb)
    return unique, dropped


def merge(
    groups: Sequence[Sequence[Traceback]],
    *,
    dedup: bool = True,
    sort_by: str = "depth",
    ascending: bool = False,
) -> MergeResult:
    """Flatten, optionally deduplicate, and sort tracebacks from multiple groups."""
    flat: list[Traceback] = [tb for group in groups for tb in group]
    total_input = len(flat)
    dropped = 0
    if dedup:
        flat, dropped = _dedup(flat)
    ranked: list[RankedTraceback] = sort_tracebacks(flat, by=sort_by, ascending=ascending)
    return MergeResult(
        tracebacks=[r.traceback for r in ranked],
        dropped=dropped,
        total_input=total_input,
    )


def format_merge_result(result: MergeResult) -> str:
    lines = [
        f"Merged {result.total_input} tracebacks: "
        f"{result.kept} unique, {result.dropped} duplicates dropped.",
    ]
    for i, tb in enumerate(result.tracebacks, 1):
        exc = tb.exception or "(unknown)"
        depth = len(tb.frames)
        lines.append(f"  [{i}] {exc}  ({depth} frames)")
    return "\n".join(lines)
