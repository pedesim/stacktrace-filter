"""Timeline: attach timestamps to tracebacks and render a chronological view."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from stacktrace_filter.parser import Traceback


@dataclass
class TimestampedTraceback:
    traceback: Traceback
    timestamp: datetime
    label: Optional[str] = None


@dataclass
class Timeline:
    entries: List[TimestampedTraceback] = field(default_factory=list)

    def add(self, tb: Traceback, timestamp: datetime, label: Optional[str] = None) -> None:
        self.entries.append(TimestampedTraceback(tb, timestamp, label))

    def sorted_entries(self) -> List[TimestampedTraceback]:
        return sorted(self.entries, key=lambda e: e.timestamp)

    def filter_by_label(self, label: str) -> "Timeline":
        """Return a new Timeline containing only entries matching the given label."""
        filtered = Timeline()
        filtered.entries = [e for e in self.entries if e.label == label]
        return filtered


def build_timeline(tracebacks: List[Traceback], timestamps: List[datetime],
                   labels: Optional[List[str]] = None) -> Timeline:
    if len(tracebacks) != len(timestamps):
        raise ValueError("tracebacks and timestamps must have equal length")
    if labels is not None and len(labels) != len(tracebacks):
        raise ValueError("labels must have the same length as tracebacks")
    tl = Timeline()
    for i, (tb, ts) in enumerate(zip(tracebacks, timestamps)):
        label = labels[i] if labels else None
        tl.add(tb, ts, label)
    return tl


def format_timeline(tl: Timeline, color: bool = True) -> str:
    lines: List[str] = []
    reset = "\033[0m" if color else ""
    cyan = "\033[36m" if color else ""
    yellow = "\033[33m" if color else ""
    for entry in tl.sorted_entries():
        ts_str = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        label_str = f" [{entry.label}]" if entry.label else ""
        header = f"{cyan}{ts_str}{reset}{yellow}{label_str}{reset}"
        exc = entry.traceback.exception or ""
        lines.append(f"{header}  {exc}")
    return "\n".join(lines)
