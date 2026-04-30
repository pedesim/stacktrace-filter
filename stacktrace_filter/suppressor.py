"""Suppress tracebacks that match known-noisy or ignorable patterns."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
import re

from stacktrace_filter.parser import Traceback


@dataclass
class SuppressRule:
    exc_type: Optional[str] = None
    exc_message: Optional[str] = None
    filename: Optional[str] = None
    reason: str = "suppressed"

    def matches(self, tb: Traceback) -> bool:
        if self.exc_type and not re.search(self.exc_type, tb.exc_type or "", re.IGNORECASE):
            return False
        if self.exc_message and not re.search(self.exc_message, tb.exc_message or "", re.IGNORECASE):
            return False
        if self.filename:
            if not any(re.search(self.filename, f.filename or "") for f in tb.frames):
                return False
        return True


@dataclass
class SuppressResult:
    kept: List[Traceback]
    suppressed: List[Traceback]
    reasons: List[str]

    @property
    def total(self) -> int:
        return len(self.kept) + len(self.suppressed)

    @property
    def suppressed_count(self) -> int:
        return len(self.suppressed)


@dataclass
class SuppressorConfig:
    rules: List[SuppressRule] = field(default_factory=list)


def suppress(tracebacks: List[Traceback], config: SuppressorConfig) -> SuppressResult:
    """Apply suppression rules; tracebacks matching any rule are dropped."""
    kept: List[Traceback] = []
    suppressed: List[Traceback] = []
    reasons: List[str] = []

    for tb in tracebacks:
        matched_reason: Optional[str] = None
        for rule in config.rules:
            if rule.matches(tb):
                matched_reason = rule.reason
                break
        if matched_reason is not None:
            suppressed.append(tb)
            reasons.append(matched_reason)
        else:
            kept.append(tb)

    return SuppressResult(kept=kept, suppressed=suppressed, reasons=reasons)


def format_suppress_result(result: SuppressResult) -> str:
    lines = [
        f"Total : {result.total}",
        f"Kept  : {len(result.kept)}",
        f"Dropped: {result.suppressed_count}",
    ]
    if result.suppressed:
        lines.append("Suppressed reasons:")
        for tb, reason in zip(result.suppressed, result.reasons):
            exc = tb.exc_type or "<unknown>"
            lines.append(f"  [{reason}] {exc}: {tb.exc_message or ''}".rstrip())
    return "\n".join(lines)
