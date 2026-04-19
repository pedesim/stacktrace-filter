"""Dispatch tracebacks to named handlers based on routing rules."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional
from stacktrace_filter.parser import Traceback

Handler = Callable[[Traceback], None]


@dataclass
class DispatchRule:
    destination: str
    exc_type: Optional[str] = None
    filename_contains: Optional[str] = None

    def matches(self, tb: Traceback) -> bool:
        if self.exc_type and self.exc_type not in tb.exception:
            return False
        if self.filename_contains:
            if not any(self.filename_contains in f.filename for f in tb.frames):
                return False
        return True


@dataclass
class DispatchResult:
    traceback: Traceback
    destination: str
    matched_rule: Optional[DispatchRule]


@dataclass
class DispatcherConfig:
    rules: List[DispatchRule] = field(default_factory=list)
    default_destination: str = "default"
    handlers: Dict[str, Handler] = field(default_factory=dict)


def dispatch(tb: Traceback, config: DispatcherConfig) -> DispatchResult:
    """Match traceback against rules and return a DispatchResult."""
    for rule in config.rules:
        if rule.matches(tb):
            return DispatchResult(traceback=tb, destination=rule.destination, matched_rule=rule)
    return DispatchResult(traceback=tb, destination=config.default_destination, matched_rule=None)


def dispatch_many(
    tracebacks: List[Traceback], config: DispatcherConfig
) -> Dict[str, List[Traceback]]:
    """Dispatch a list of tracebacks and group by destination."""
    groups: Dict[str, List[Traceback]] = {}
    for tb in tracebacks:
        result = dispatch(tb, config)
        groups.setdefault(result.destination, []).append(tb)
        handler = config.handlers.get(result.destination)
        if handler:
            handler(tb)
    return groups
