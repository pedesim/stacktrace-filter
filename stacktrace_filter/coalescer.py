"""Coalesce multiple tracebacks that share the same root cause frame."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from .parser import Traceback, Frame


def _root_cause_key(tb: Traceback) -> Optional[str]:
    """Return a string key identifying the root-cause frame (last frame)."""
    if not tb.frames:
        return None
    last: Frame = tb.frames[-1]
    return f"{last.filename}:{last.lineno}:{last.function}"


@dataclass
class CoalescedGroup:
    root_cause_key: str
    representative: Traceback
    members: List[Traceback] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.members)

    @property
    def exc_types(self) -> List[str]:
        seen: list = []
        for tb in self.members:
            if tb.exc_type and tb.exc_type not in seen:
                seen.append(tb.exc_type)
        return seen


@dataclass
class CoalesceResult:
    groups: List[CoalescedGroup] = field(default_factory=list)

    @property
    def total(self) -> int:
        return sum(g.count for g in self.groups)

    @property
    def group_count(self) -> int:
        return len(self.groups)

    def get(self, key: str) -> Optional[CoalescedGroup]:
        for g in self.groups:
            if g.root_cause_key == key:
                return g
        return None


def coalesce(tracebacks: Sequence[Traceback]) -> CoalesceResult:
    """Group tracebacks by their root-cause frame key."""
    index: dict[str, CoalescedGroup] = {}
    ungrouped_key = "<no-frames>"

    for tb in tracebacks:
        key = _root_cause_key(tb) or ungrouped_key
        if key not in index:
            index[key] = CoalescedGroup(
                root_cause_key=key,
                representative=tb,
                members=[tb],
            )
        else:
            index[key].members.append(tb)

    return CoalesceResult(groups=list(index.values()))


def format_coalesce_result(result: CoalesceResult, *, color: bool = True) -> str:
    """Render a human-readable summary of coalesced groups."""
    lines: list[str] = []
    reset = "\033[0m" if color else ""
    bold = "\033[1m" if color else ""
    dim = "\033[2m" if color else ""

    lines.append(f"{bold}Coalesced {result.total} tracebacks into {result.group_count} group(s){reset}")
    for i, group in enumerate(result.groups, 1):
        exc_label = ", ".join(group.exc_types) or "unknown"
        lines.append(
            f"  {bold}[{i}]{reset} {group.root_cause_key} "
            f"{dim}({group.count} occurrence(s), exc: {exc_label}){reset}"
        )
    return "\n".join(lines)
