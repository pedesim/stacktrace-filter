"""Split a list of tracebacks into named partitions based on rules."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional
from stacktrace_filter.parser import Traceback


@dataclass
class SplitRule:
    name: str
    predicate: Callable[[Traceback], bool]


@dataclass
class SplitResult:
    partitions: Dict[str, List[Traceback]] = field(default_factory=dict)
    unmatched: List[Traceback] = field(default_factory=list)

    def all_names(self) -> List[str]:
        return list(self.partitions.keys())

    def get(self, name: str) -> List[Traceback]:
        return self.partitions.get(name, [])


def split(tracebacks: List[Traceback], rules: List[SplitRule]) -> SplitResult:
    """Assign each traceback to the first matching rule's partition."""
    result = SplitResult(partitions={r.name: [] for r in rules})
    for tb in tracebacks:
        matched = False
        for rule in rules:
            if rule.predicate(tb):
                result.partitions[rule.name].append(tb)
                matched = True
                break
        if not matched:
            result.unmatched.append(tb)
    return result


def format_split_result(result: SplitResult) -> str:
    lines: List[str] = []
    for name, tbs in result.partitions.items():
        lines.append(f"[{name}] {len(tbs)} traceback(s)")
    if result.unmatched:
        lines.append(f"[unmatched] {len(result.unmatched)} traceback(s)")
    return "\n".join(lines)
