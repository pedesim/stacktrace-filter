"""Tests for stacktrace_filter.matcher."""
import pytest
from stacktrace_filter.parser import Traceback, Frame
from stacktrace_filter.matcher import MatchRule, MatchResult, apply_rules, filter_tracebacks


def _frame(filename="app/main.py", lineno=10, func="run", line="do()"):
    return Frame(filename=filename, lineno=lineno, function=func, line=line)


def _tb(exc="ValueError: bad input", frames=None):
    return Traceback(
        frames=frames or [_frame()],
        exception_line=exc,
    )


def test_match_rule_exc_type_match():
    rule = MatchRule(name="val", exc_type_pattern="ValueError")
    assert rule.matches(_tb("ValueError: oops"))


def test_match_rule_exc_type_no_match():
    rule = MatchRule(name="key", exc_type_pattern="KeyError")
    assert not rule.matches(_tb("ValueError: oops"))


def test_match_rule_exc_message():
    rule = MatchRule(name="bad", exc_message_pattern="bad input")
    assert rule.matches(_tb("ValueError: bad input"))


def test_match_rule_exc_message_no_match():
    rule = MatchRule(name="other", exc_message_pattern="timeout")
    assert not rule.matches(_tb("ValueError: bad input"))


def test_match_rule_filename_pattern():
    rule = MatchRule(name="app", filename_pattern=r"app/")
    assert rule.matches(_tb(frames=[_frame(filename="app/views.py")]))


def test_match_rule_filename_no_match():
    rule = MatchRule(name="lib", filename_pattern=r"lib/")
    assert not rule.matches(_tb(frames=[_frame(filename="app/views.py")]))


def test_match_rule_min_depth_pass():
    rule = MatchRule(name="deep", min_depth=2)
    tb = _tb(frames=[_frame(), _frame(lineno=20)])
    assert rule.matches(tb)


def test_match_rule_min_depth_fail():
    rule = MatchRule(name="deep", min_depth=5)
    assert not rule.matches(_tb())


def test_apply_rules_multiple():
    rules = [
        MatchRule(name="r1", exc_type_pattern="ValueError"),
        MatchRule(name="r2", filename_pattern=r"app/"),
    ]
    result = apply_rules(_tb(), rules)
    assert result.matched
    assert "r1" in result.matched_rules
    assert "r2" in result.matched_rules


def test_apply_rules_none_match():
    rules = [MatchRule(name="r1", exc_type_pattern="KeyError")]
    result = apply_rules(_tb(), rules)
    assert not result.matched
    assert result.matched_rules == []


def test_filter_tracebacks():
    tbs = [_tb("ValueError: x"), _tb("KeyError: y")]
    rules = [MatchRule(name="val", exc_type_pattern="ValueError")]
    results = filter_tracebacks(tbs, rules)
    assert len(results) == 1
    assert results[0].matched_rules == ["val"]


def test_match_result_matched_property():
    r = MatchResult(traceback=_tb(), matched_rules=["x"])
    assert r.matched
    r2 = MatchResult(traceback=_tb())
    assert not r2.matched
