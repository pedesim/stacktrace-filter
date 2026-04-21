"""Tests for stacktrace_filter.catalyst."""
from __future__ import annotations

import pytest

from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.catalyst import (
    CatalystResult,
    _fault_score,
    find_catalyst,
    format_catalyst,
)


def _frame(
    filename: str = "app/main.py",
    lineno: int = 10,
    function: str = "run",
    line: str = "",
) -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, line=line)


def _tb(*frames: Frame, exc_type: str = "RuntimeError", exc_msg: str = "oops") -> Traceback:
    return Traceback(frames=list(frames), exc_type=exc_type, exc_message=exc_msg)


# ---------------------------------------------------------------------------
# _fault_score
# ---------------------------------------------------------------------------

def test_fault_score_empty_line():
    f = _frame(line="")
    assert _fault_score(f) == 0.0


def test_fault_score_raise_statement():
    f = _frame(line="raise ValueError('bad')")
    score = _fault_score(f)
    assert score > 0.0


def test_fault_score_attribute_access():
    f = _frame(line="result = obj.value")
    score = _fault_score(f)
    assert score > 0.0


def test_fault_score_capped_at_one():
    # A line that matches many patterns at once.
    f = _frame(line="raise ValueError(obj.attr[0])  # result = None")
    assert _fault_score(f) <= 1.0


# ---------------------------------------------------------------------------
# find_catalyst – edge cases
# ---------------------------------------------------------------------------

def test_find_catalyst_no_frames():
    tb = _tb(exc_type="ValueError")
    result = find_catalyst(tb)
    assert result.frame is None
    assert result.confidence == 0.0


def test_find_catalyst_no_user_frames():
    """When all frames are stdlib, fall back to deepest frame."""
    f = _frame(filename="/usr/lib/python3.11/json/__init__.py", line="data = loads(s)")
    tb = _tb(f)
    result = find_catalyst(tb)
    assert result.frame is f
    assert result.confidence == pytest.approx(0.1)


def test_find_catalyst_single_user_frame_no_pattern():
    f = _frame(filename="app/main.py", line="pass")
    tb = _tb(f)
    result = find_catalyst(tb)
    assert result.frame is f
    assert result.confidence == pytest.approx(0.3)
    assert "deepest user frame" in result.reason


def test_find_catalyst_picks_frame_with_raise():
    f1 = _frame(filename="app/views.py", lineno=5, function="view", line="x = 1")
    f2 = _frame(filename="app/models.py", lineno=20, function="save", line="raise IntegrityError()")
    tb = _tb(f1, f2)
    result = find_catalyst(tb)
    assert result.frame is f2
    assert result.confidence > 0.3


def test_find_catalyst_confidence_between_zero_and_one():
    f = _frame(filename="app/utils.py", line="raise RuntimeError(obj.msg)")
    tb = _tb(f)
    result = find_catalyst(tb)
    assert 0.0 <= result.confidence <= 1.0


# ---------------------------------------------------------------------------
# format_catalyst
# ---------------------------------------------------------------------------

def test_format_catalyst_none_frame():
    result = CatalystResult(frame=None, confidence=0.0, reason="no frames")
    text = format_catalyst(result, color=False)
    assert "undetermined" in text


def test_format_catalyst_contains_location():
    f = _frame(filename="app/main.py", lineno=42, function="main", line="run()")
    result = CatalystResult(frame=f, confidence=0.8, reason="fault pattern matched")
    text = format_catalyst(result, color=False)
    assert "app/main.py" in text
    assert "42" in text
    assert "main" in text


def test_format_catalyst_shows_confidence_percent():
    f = _frame(filename="app/main.py", line="raise ValueError()")
    result = CatalystResult(frame=f, confidence=0.75, reason="test")
    text = format_catalyst(result, color=False)
    assert "75%" in text
