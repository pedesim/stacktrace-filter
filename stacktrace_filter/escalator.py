"""escalator.py – decide whether a traceback warrants escalation.

An *escalation* is a recommendation to page on-call, open a ticket, or
otherwise raise the urgency level beyond normal logging.  Rules are
evaluated in order; the first match wins.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .parser import Traceback
from .severity import classify, SeverityResult


@dataclass
class EscalationRule:
    """A single rule that may trigger escalation."""
    exc_type_pattern: Optional[str] = None   # substring match on exc type
    min_severity: Optional[str] = None       # 'warning' | 'error' | 'critical'
    target: str = "log"                      # escalation target label
    reason: str = ""

    _SEVERITY_ORDER = {"warning": 0, "error": 1, "critical": 2}

    def matches(self, tb: Traceback, severity: SeverityResult) -> bool:
        exc = (tb.exception or "").lower()
        if self.exc_type_pattern and self.exc_type_pattern.lower() not in exc:
            return False
        if self.min_severity:
            threshold = self._SEVERITY_ORDER.get(self.min_severity, 0)
            actual = self._SEVERITY_ORDER.get(severity.level, 0)
            if actual < threshold:
                return False
        return True


@dataclass
class EscalationResult:
    """Outcome of evaluating escalation rules against a traceback."""
    should_escalate: bool
    target: str
    reason: str
    severity: str
    rule_index: Optional[int]  # index of matching rule, or None

    def summary(self) -> str:
        if not self.should_escalate:
            return f"[no escalation] severity={self.severity}"
        tag = f"rule#{self.rule_index}" if self.rule_index is not None else "default"
        return (
            f"[escalate -> {self.target}] severity={self.severity} "
            f"via {tag}: {self.reason}"
        )


@dataclass
class EscalatorConfig:
    rules: List[EscalationRule] = field(default_factory=list)
    default_target: str = "log"
    default_reason: str = "no rule matched"


def escalate(
    tb: Traceback,
    config: Optional[EscalatorConfig] = None,
) -> EscalationResult:
    """Evaluate *config* rules against *tb* and return an EscalationResult."""
    if config is None:
        config = EscalatorConfig()

    sev: SeverityResult = classify(tb)

    for idx, rule in enumerate(config.rules):
        if rule.matches(tb, sev):
            return EscalationResult(
                should_escalate=True,
                target=rule.target,
                reason=rule.reason or f"matched rule #{idx}",
                severity=sev.level,
                rule_index=idx,
            )

    return EscalationResult(
        should_escalate=False,
        target=config.default_target,
        reason=config.default_reason,
        severity=sev.level,
        rule_index=None,
    )


def format_escalation(result: EscalationResult, *, color: bool = True) -> str:
    """Return a human-readable string describing *result*."""
    if not color:
        return result.summary()
    if result.should_escalate:
        return f"\033[1;31m{result.summary()}\033[0m"
    return f"\033[2m{result.summary()}\033[0m"
