"""Route tracebacks to named destinations based on rules."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
import re
from stacktrace_filter.parser import Traceback


@dataclass
class RouteRule:
    destination: str
    exc_type: Optional[str] = None
    exc_message: Optional[str] = None
    filename_contains: Optional[str] = None

    def matches(self, tb: Traceback) -> bool:
        if self.exc_type and not re.search(self.exc_type, tb.exc_type or ""):
            return False
        if self.exc_message and not re.search(self.exc_message, tb.exc_message or "", re.IGNORECASE):
            return False
        if self.filename_contains:
            if not any(self.filename_contains in (f.filename or "") for f in tb.frames):
                return False
        return True


@dataclass
class RoutedTraceback:
    traceback: Traceback
    destination: str
    rule: Optional[RouteRule]


@dataclass
class RouterConfig:
    rules: List[RouteRule] = field(default_factory=list)
    default_destination: str = "default"


def route(tb: Traceback, config: RouterConfig) -> RoutedTraceback:
    for rule in config.rules:
        if rule.matches(tb):
            return RoutedTraceback(traceback=tb, destination=rule.destination, rule=rule)
    return RoutedTraceback(traceback=tb, destination=config.default_destination, rule=None)


def route_all(tbs: List[Traceback], config: RouterConfig) -> dict[str, List[RoutedTraceback]]:
    result: dict[str, List[RoutedTraceback]] = {}
    for tb in tbs:
        rt = route(tb, config)
        result.setdefault(rt.destination, []).append(rt)
    return result


def format_routing_report(grouped: dict[str, List[RoutedTraceback]]) -> str:
    lines = []
    for dest, entries in sorted(grouped.items()):
        lines.append(f"[{dest}] {len(entries)} traceback(s)")
        for rt in entries:
            exc = rt.traceback.exc_type or "<unknown>"
            lines.append(f"  - {exc}")
    return "\n".join(lines)
