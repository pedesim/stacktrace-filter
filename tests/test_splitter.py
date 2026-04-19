"""Tests for stacktrace_filter.splitter."""
import pytest
from stacktrace_filter.parser import Traceback, Frame
from stacktrace_filter.splitter import SplitRule, SplitResult, split, format_split_result


def _frame(filename="app.py", lineno=1, func="fn", line="pass"):
    return Frame(filename=filename, lineno=lineno, function=func, source_line=line)


def _tb(exc="ValueError: bad", frames=None):
    return Traceback(frames=frames or [_frame()], exception=exc)


def test_split_empty_list():
    rules = [SplitRule("errors", lambda tb: True)]
    result = split([], rules)
    assert result.get("errors") == []
    assert result.unmatched == []


def test_split_single_match():
    tb = _tb(exc="ValueError: oops")
    rules = [SplitRule("value_errors", lambda tb: "ValueError" in (tb.exception or ""))]
    result = split([tb], rules)
    assert len(result.get("value_errors")) == 1
    assert result.unmatched == []


def test_split_unmatched():
    tb = _tb(exc="TypeError: bad")
    rules = [SplitRule("value_errors", lambda tb: "ValueError" in (tb.exception or ""))]
    result = split([tb], rules)
    assert result.get("value_errors") == []
    assert len(result.unmatched) == 1


def test_split_first_rule_wins():
    tb = _tb(exc="ValueError: bad")
    rules = [
        SplitRule("first", lambda tb: "ValueError" in (tb.exception or "")),
        SplitRule("second", lambda tb: "ValueError" in (tb.exception or "")),
    ]
    result = split([tb], rules)
    assert len(result.get("first")) == 1
    assert result.get("second") == []


def test_split_multiple_tracebacks():
    tbs = [_tb("ValueError: a"), _tb("TypeError: b"), _tb("ValueError: c")]
    rules = [
        SplitRule("ve", lambda tb: "ValueError" in (tb.exception or "")),
        SplitRule("te", lambda tb: "TypeError" in (tb.exception or "")),
    ]
    result = split(tbs, rules)
    assert len(result.get("ve")) == 2
    assert len(result.get("te")) == 1


def test_all_names():
    rules = [SplitRule("a", lambda tb: False), SplitRule("b", lambda tb: False)]
    result = split([], rules)
    assert result.all_names() == ["a", "b"]


def test_format_split_result():
    rules = [SplitRule("errors", lambda tb: True)]
    result = split([_tb()], rules)
    out = format_split_result(result)
    assert "[errors]" in out
    assert "1 traceback" in out


def test_format_split_result_with_unmatched():
    rules = [SplitRule("errors", lambda tb: False)]
    result = split([_tb()], rules)
    out = format_split_result(result)
    assert "unmatched" in out
