"""Tests for stacktrace_filter.dispatcher."""
import pytest
from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.dispatcher import (
    DispatchRule,
    DispatcherConfig,
    dispatch,
    dispatch_many,
)


def _frame(filename="app/views.py", func="handle", lineno=10):
    return Frame(filename=filename, lineno=lineno, function=func, source_line="pass")


def _tb(exc="ValueError: bad input", frames=None):
    return Traceback(frames=frames or [_frame()], exception=exc)


def test_dispatch_default_when_no_rules():
    tb = _tb()
    cfg = DispatcherConfig()
    result = dispatch(tb, cfg)
    assert result.destination == "default"
    assert result.matched_rule is None


def test_dispatch_matches_exc_type():
    rule = DispatchRule(destination="value-errors", exc_type="ValueError")
    cfg = DispatcherConfig(rules=[rule])
    result = dispatch(_tb(exc="ValueError: oops"), cfg)
    assert result.destination == "value-errors"
    assert result.matched_rule is rule


def test_dispatch_no_match_exc_type():
    rule = DispatchRule(destination="type-errors", exc_type="TypeError")
    cfg = DispatcherConfig(rules=[rule])
    result = dispatch(_tb(exc="ValueError: oops"), cfg)
    assert result.destination == "default"


def test_dispatch_matches_filename_contains():
    rule = DispatchRule(destination="views", filename_contains="views.py")
    cfg = DispatcherConfig(rules=[rule])
    result = dispatch(_tb(), cfg)
    assert result.destination == "views"


def test_dispatch_filename_no_match():
    rule = DispatchRule(destination="models", filename_contains="models.py")
    cfg = DispatcherConfig(rules=[rule])
    result = dispatch(_tb(), cfg)
    assert result.destination == "default"


def test_dispatch_first_rule_wins():
    r1 = DispatchRule(destination="first", exc_type="ValueError")
    r2 = DispatchRule(destination="second", exc_type="ValueError")
    cfg = DispatcherConfig(rules=[r1, r2])
    result = dispatch(_tb(exc="ValueError: x"), cfg)
    assert result.destination == "first"


def test_dispatch_many_groups_by_destination():
    rule = DispatchRule(destination="value-errors", exc_type="ValueError")
    cfg = DispatcherConfig(rules=[rule])
    tbs = [_tb(exc="ValueError: a"), _tb(exc="KeyError: b"), _tb(exc="ValueError: c")]
    groups = dispatch_many(tbs, cfg)
    assert len(groups["value-errors"]) == 2
    assert len(groups["default"]) == 1


def test_dispatch_many_calls_handler():
    called = []
    rule = DispatchRule(destination="sink", exc_type="RuntimeError")
    cfg = DispatcherConfig(rules=[rule], handlers={"sink": lambda tb: called.append(tb)})
    tbs = [_tb(exc="RuntimeError: boom"), _tb(exc="RuntimeError: again")]
    dispatch_many(tbs, cfg)
    assert len(called) == 2
