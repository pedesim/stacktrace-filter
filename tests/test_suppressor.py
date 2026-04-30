"""Tests for stacktrace_filter.suppressor."""
from __future__ import annotations

import pytest

from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.suppressor import (
    SuppressRule,
    SuppressorConfig,
    SuppressResult,
    suppress,
    format_suppress_result,
)


def _frame(filename="app.py", lineno=10, function="fn", text="pass") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, text=text)


def _tb(exc_type="ValueError", exc_message="bad value", frames=None) -> Traceback:
    return Traceback(
        exc_type=exc_type,
        exc_message=exc_message,
        frames=frames or [_frame()],
        raw="",
    )


def test_suppress_no_rules_keeps_all():
    tbs = [_tb(), _tb(exc_type="KeyError")]
    result = suppress(tbs, SuppressorConfig())
    assert result.kept == tbs
    assert result.suppressed == []


def test_suppress_exc_type_match():
    tbs = [_tb(exc_type="ValueError"), _tb(exc_type="KeyError")]
    rules = [SuppressRule(exc_type="ValueError", reason="noisy")]
    result = suppress(tbs, SuppressorConfig(rules=rules))
    assert len(result.kept) == 1
    assert result.kept[0].exc_type == "KeyError"
    assert len(result.suppressed) == 1
    assert result.reasons == ["noisy"]


def test_suppress_exc_message_match():
    tbs = [_tb(exc_message="connection refused"), _tb(exc_message="timeout")]
    rules = [SuppressRule(exc_message="connection")]
    result = suppress(tbs, SuppressorConfig(rules=rules))
    assert len(result.kept) == 1
    assert result.kept[0].exc_message == "timeout"


def test_suppress_filename_match():
    frames_noise = [_frame(filename="/usr/lib/python/noise.py")]
    frames_user = [_frame(filename="app/main.py")]
    tbs = [_tb(frames=frames_noise), _tb(frames=frames_user)]
    rules = [SuppressRule(filename=r"usr/lib/python")]
    result = suppress(tbs, SuppressorConfig(rules=rules))
    assert len(result.kept) == 1
    assert result.kept[0].frames[0].filename == "app/main.py"


def test_suppress_combined_conditions_all_must_match():
    tbs = [
        _tb(exc_type="ValueError", exc_message="bad"),
        _tb(exc_type="ValueError", exc_message="ok"),
    ]
    rules = [SuppressRule(exc_type="ValueError", exc_message="bad")]
    result = suppress(tbs, SuppressorConfig(rules=rules))
    assert len(result.kept) == 1
    assert result.kept[0].exc_message == "ok"


def test_suppress_total_property():
    tbs = [_tb(), _tb(), _tb()]
    rules = [SuppressRule(exc_type="ValueError")]
    result = suppress(tbs, SuppressorConfig(rules=rules))
    assert result.total == 3


def test_format_suppress_result_contains_counts():
    tbs = [_tb(exc_type="ValueError"), _tb(exc_type="KeyError")]
    rules = [SuppressRule(exc_type="ValueError", reason="noisy")]
    result = suppress(tbs, SuppressorConfig(rules=rules))
    output = format_suppress_result(result)
    assert "Kept" in output
    assert "Dropped" in output
    assert "noisy" in output
    assert "ValueError" in output


def test_format_suppress_result_no_suppressions():
    tbs = [_tb()]
    result = suppress(tbs, SuppressorConfig())
    output = format_suppress_result(result)
    assert "Dropped: 0" in output
