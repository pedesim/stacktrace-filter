"""Tag tracebacks with user-defined labels based on pattern matching."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_filter.parser import Traceback


@dataclass
class TagRule:
    tag: str
    pattern: str
    field: str = "exc_type"  # exc_type | exc_message | filename | function

    def __post_init__(self) -> None:
        self._re = re.compile(self.pattern)

    def matches(self, tb: Traceback) -> bool:
        if self.field == "exc_type":
            return bool(self._re.search(tb.exc_type or ""))
        if self.field == "exc_message":
            return bool(self._re.search(tb.exc_message or ""))
        if self.field == "filename":
            return any(self._re.search(f.filename) for f in tb.frames)
        if self.field == "function":
            return any(self._re.search(f.function) for f in tb.frames)
        return False


@dataclass
class TaggedTraceback:
    traceback: Traceback
    tags: List[str] = field(default_factory=list)


def apply_rules(tb: Traceback, rules: List[TagRule]) -> TaggedTraceback:
    """Apply all matching rules and return a TaggedTraceback."""
    tags = [rule.tag for rule in rules if rule.matches(tb)]
    return TaggedTraceback(traceback=tb, tags=tags)


def tag_all(tracebacks: List[Traceback], rules: List[TagRule]) -> List[TaggedTraceback]:
    """Tag a list of tracebacks using the provided rules."""
    return [apply_rules(tb, rules) for tb in tracebacks]


def format_tagged(tt: TaggedTraceback, sep: str = ", ") -> str:
    """Return a short string representation of tags for display."""
    if not tt.tags:
        return "[untagged]"
    return "[" + sep.join(sorted(tt.tags)) + "]"
