"""Pattern-based traceback matcher for filtering and routing."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
import re

from stacktrace_filter.parser import Traceback


@dataclass
class MatchRule:
    name: str
    exc_type_pattern: Optional[str] = None
    exc_message_pattern: Optional[str] = None
    filename_pattern: Optional[str] = None
    min_depth: Optional[int] = None

    def _exc_type(self, tb: Traceback) -> str:
        if tb.exception_line:
            return tb.exception_line.split(":")[0].strip()
        return ""

    def _exc_message(self, tb: Traceback) -> str:
        if tb.exception_line and ":" in tb.exception_line:
            return tb.exception_line.split(":", 1)[1].strip()
        return ""

    def matches(self, tb: Traceback) -> bool:
        if self.exc_type_pattern:
            if not re.search(self.exc_type_pattern, self._exc_type(tb)):
                return False
        if self.exc_message_pattern:
            if not re.search(self.exc_message_pattern, self._exc_message(tb)):
                return False
        if self.filename_pattern:
            if not any(re.search(self.filename_pattern, f.filename) for f in tb.frames):
                return False
        if self.min_depth is not None:
            if len(tb.frames) < self.min_depth:
                return False
        return True


@dataclass
class MatchResult:
    traceback: Traceback
    matched_rules: List[str] = field(default_factory=list)

    @property
    def matched(self) -> bool:
        return len(self.matched_rules) > 0


def apply_rules(tb: Traceback, rules: List[MatchRule]) -> MatchResult:
    result = MatchResult(traceback=tb)
    for rule in rules:
        if rule.matches(tb):
            result.matched_rules.append(rule.name)
    return result


def filter_tracebacks(tbs: List[Traceback], rules: List[MatchRule]) -> List[MatchResult]:
    return [r for tb in tbs if (r := apply_rules(tb, rules)).matched]
