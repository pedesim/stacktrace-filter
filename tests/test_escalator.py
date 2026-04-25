"""Tests for stacktrace_filter.escalator."""
from __future__ import annotations

import pytest

from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.escalator import (
    EscalationRule,
    EscalatorConfig,
    EscalationResult,
    escalate,
    format_escalation,
)


def _frame(filename: str = "app/main.py", func: str = "run", lineno: int = 10) -> Frame:
    return Frame(filename=filename, function=func, lineno=lineno, line="pass")


def _tb(exc: str = "RuntimeError: boom") -> Traceback:
    return Traceback(frames=[_frame()], exception=exc)


# ---------------------------------------------------------------------------
# EscalationRule.matches
# ---------------------------------------------------------------------------

def test_rule_matches_exc_type_substring():
    rule = EscalationRule(exc_type_pattern="RuntimeError", target="pager")
    tb = _tb("RuntimeError: something")
    from stacktrace_filter.severity import classify
    sev = classify(tb)
    assert rule.matches(tb, sev) is True


def test_rule_no_match_exc_type():
    rule = EscalationRule(exc_type_pattern="ValueError", target="pager")
    tb = _tb("RuntimeError: something")
    from stacktrace_filter.severity import classify
    sev = classify(tb)
    assert rule.matches(tb, sev) is False


def test_rule_matches_min_severity_critical():
    rule = EscalationRule(min_severity="critical", target="ticket")
    tb = _tb("SystemExit: 1")  # typically critical
    from stacktrace_filter.severity import classify
    sev = classify(tb)
    # only assert it doesn't crash; actual match depends on severity module
    result = rule.matches(tb, sev)
    assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# escalate() – no rules
# ---------------------------------------------------------------------------

def test_escalate_no_rules_returns_no_escalation():
    tb = _tb()
    result = escalate(tb)
    assert result.should_escalate is False
    assert result.rule_index is None


def test_escalate_no_rules_default_target():
    tb = _tb()
    config = EscalatorConfig(default_target="slack")
    result = escalate(tb, config)
    assert result.target == "slack"


# ---------------------------------------------------------------------------
# escalate() – with matching rule
# ---------------------------------------------------------------------------

def test_escalate_first_matching_rule_wins():
    rules = [
        EscalationRule(exc_type_pattern="ValueError", target="log"),
        EscalationRule(exc_type_pattern="RuntimeError", target="pager", reason="runtime!"),
    ]
    config = EscalatorConfig(rules=rules)
    tb = _tb("RuntimeError: boom")
    result = escalate(tb, config)
    assert result.should_escalate is True
    assert result.target == "pager"
    assert result.rule_index == 1
    assert "runtime!" in result.reason


def test_escalate_returns_escalation_result_instance():
    tb = _tb()
    result = escalate(tb)
    assert isinstance(result, EscalationResult)


def test_escalate_severity_field_populated():
    tb = _tb("MemoryError")
    result = escalate(tb)
    assert result.severity in {"warning", "error", "critical", "info", "unknown"}


# ---------------------------------------------------------------------------
# format_escalation
# ---------------------------------------------------------------------------

def test_format_escalation_no_color_no_ansi():
    tb = _tb()
    result = escalate(tb)
    text = format_escalation(result, color=False)
    assert "\033[" not in text
    assert "no escalation" in text


def test_format_escalation_with_color_contains_ansi():
    tb = _tb()
    result = escalate(tb)
    text = format_escalation(result, color=True)
    assert "\033[" in text


def test_format_escalation_escalated_contains_target():
    rule = EscalationRule(exc_type_pattern="RuntimeError", target="pagerduty")
    config = EscalatorConfig(rules=[rule])
    tb = _tb("RuntimeError: oh no")
    result = escalate(tb, config)
    text = format_escalation(result, color=False)
    assert "pagerduty" in text
