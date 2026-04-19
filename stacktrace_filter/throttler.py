"""Rate-based throttling for traceback streams."""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import defaultdict
from typing import List, Dict
import time

from stacktrace_filter.parser import Traceback
from stacktrace_filter.fingerprint import fingerprint


@dataclass
class ThrottlerConfig:
    max_per_window: int = 10
    window_seconds: float = 60.0


@dataclass
class ThrottleResult:
    traceback: Traceback
    allowed: bool
    count_in_window: int
    fingerprint: str


@dataclass
class _WindowState:
    timestamps: List[float] = field(default_factory=list)

    def prune(self, cutoff: float) -> None:
        self.timestamps = [t for t in self.timestamps if t >= cutoff]

    def record(self, ts: float) -> None:
        self.timestamps.append(ts)

    def count(self) -> int:
        return len(self.timestamps)


class Throttler:
    def __init__(self, config: ThrottlerConfig | None = None) -> None:
        self.config = config or ThrottlerConfig()
        self._states: Dict[str, _WindowState] = defaultdict(_WindowState)

    def check(self, tb: Traceback, now: float | None = None) -> ThrottleResult:
        ts = now if now is not None else time.monotonic()
        fp = fingerprint(tb).full
        state = self._states[fp]
        cutoff = ts - self.config.window_seconds
        state.prune(cutoff)
        count = state.count()
        allowed = count < self.config.max_per_window
        if allowed:
            state.record(ts)
            count += 1
        return ThrottleResult(
            traceback=tb,
            allowed=allowed,
            count_in_window=count,
            fingerprint=fp,
        )

    def filter(self, tracebacks: List[Traceback], now: float | None = None) -> List[Traceback]:
        return [r.traceback for r in (self.check(tb, now) for tb in tracebacks) if r.allowed]

    def reset(self) -> None:
        self._states.clear()


def throttle(tracebacks: List[Traceback], config: ThrottlerConfig | None = None) -> List[Traceback]:
    return Throttler(config).filter(tracebacks)
