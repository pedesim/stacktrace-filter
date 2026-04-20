"""Tests for stacktrace_filter.retrier."""
from __future__ import annotations

import pytest

from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.retrier import (
    RetryAdvice,
    RetrierConfig,
    advise,
    format_advice,
)


def _tb(exc_line: str) -> Traceback:
    frame = Frame(
        filename="app/service.py",
        lineno=10,
        function="call",
        source_line="result = client.get(url)",
    )
    return Traceback(frames=[frame], exception_line=exc_line)


def test_advise_retryable_exc_type():
    tb = _tb("ConnectionError: timed out")
    advice = advise(tb)
    assert advice.retryable is True
    assert advice.fatal is False
    assert advice.exc_type == "ConnectionError"
    assert advice.matched_rule == "retryable_list"


def test_advise_fatal_exc_type():
    tb = _tb("SystemExit: 1")
    advice = advise(tb)
    assert advice.retryable is False
    assert advice.fatal is True
    assert advice.matched_rule == "fatal_list"
    assert advice.suggested_delay_s == 0.0


def test_advise_unknown_exc_type():
    tb = _tb("ValueError: bad input")
    advice = advise(tb)
    assert advice.retryable is False
    assert advice.fatal is False
    assert advice.matched_rule is None


def test_advise_extra_retryable():
    tb = _tb("MyTransientError: blip")
    cfg = RetrierConfig(extra_retryable=["MyTransientError"])
    advice = advise(tb, cfg)
    assert advice.retryable is True
    assert advice.matched_rule == "retryable_list"


def test_advise_extra_fatal():
    tb = _tb("CriticalDBError: disk full")
    cfg = RetrierConfig(extra_fatal=["CriticalDBError"])
    advice = advise(tb, cfg)
    assert advice.fatal is True
    assert advice.retryable is False


def test_advise_custom_delay():
    tb = _tb("TimeoutError: slow")
    cfg = RetrierConfig(default_delay_s=5.0)
    advice = advise(tb, cfg)
    assert advice.suggested_delay_s == 5.0


def test_advise_fatal_overrides_retryable():
    """If a type appears in both lists, fatal wins."""
    tb = _tb("ConnectionError: gone")
    cfg = RetrierConfig(extra_fatal=["ConnectionError"])
    advice = advise(tb, cfg)
    assert advice.fatal is True
    assert advice.retryable is False


def test_format_advice_retryable():
    advice = RetryAdvice(
        exc_type="TimeoutError",
        retryable=True,
        fatal=False,
        reason="transient",
        suggested_delay_s=2.0,
    )
    out = format_advice(advice)
    assert "RETRYABLE" in out
    assert "2.0" in out


def test_format_advice_fatal():
    advice = RetryAdvice(
        exc_type="SystemExit",
        retryable=False,
        fatal=True,
        reason="fatal",
        suggested_delay_s=0.0,
    )
    out = format_advice(advice)
    assert "FATAL" in out


def test_format_advice_unknown():
    advice = RetryAdvice(
        exc_type="ValueError",
        retryable=False,
        fatal=False,
        reason="unknown",
    )
    out = format_advice(advice)
    assert "UNKNOWN" in out
