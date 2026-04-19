"""Tests for stacktrace_filter.comparator."""
from __future__ import annotations
import pytest
from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.comparator import (
    compare,
    format_comparison,
    ComparisonResult,
    _frame_similarity,
)


def _frame(filename="app.py", lineno=10, name="fn", line="pass") -> Frame:
    return Frame(filename=filename, lineno=lineno, name=name, line=line)


def _tb(frames, exc_type="ValueError", exc_message="bad") -> Traceback:
    return Traceback(frames=frames, exc_type=exc_type, exc_message=exc_message)


def test_identical_tracebacks_score_one():
    f = _frame()
    tb = _tb([f])
    result = compare(tb, tb)
    assert result.overall_score == pytest.approx(1.0)
    assert result.exc_type_match is True
    assert result.exc_message_match is True
    assert result.frame_similarity == pytest.approx(1.0)


def test_completely_different_tracebacks():
    tb1 = _tb([_frame("a.py", 1, "f1")], exc_type="ValueError", exc_message="x")
    tb2 = _tb([_frame("b.py", 2, "f2")], exc_type="TypeError", exc_message="y")
    result = compare(tb1, tb2)
    assert result.frame_similarity == pytest.approx(0.0)
    assert result.exc_type_match is False
    assert result.exc_message_match is False
    assert result.overall_score == pytest.approx(0.0)


def test_same_exc_type_different_frames():
    tb1 = _tb([_frame("a.py", 1, "f")], exc_type="KeyError")
    tb2 = _tb([_frame("b.py", 2, "g")], exc_type="KeyError")
    result = compare(tb1, tb2)
    assert result.exc_type_match is True
    assert result.frame_similarity == pytest.approx(0.0)
    assert result.overall_score == pytest.approx(0.3)


def test_partial_frame_overlap():
    shared = _frame("shared.py", 5, "common")
    only_left = _frame("left.py", 1, "l")
    only_right = _frame("right.py", 2, "r")
    tb1 = _tb([shared, only_left], exc_type="E", exc_message="m")
    tb2 = _tb([shared, only_right], exc_type="E", exc_message="m")
    result = compare(tb1, tb2)
    # union=3, intersection=1 => 1/3
    assert result.frame_similarity == pytest.approx(1 / 3)
    assert result.exc_type_match is True
    assert result.exc_message_match is True


def test_empty_frames_both():
    tb1 = _tb([])
    tb2 = _tb([])
    result = compare(tb1, tb2)
    assert result.frame_similarity == pytest.approx(1.0)


def test_frame_similarity_empty_lists():
    assert _frame_similarity([], []) == pytest.approx(1.0)


def test_format_comparison_no_color():
    tb = _tb([_frame()])
    result = compare(tb, tb)
    text = format_comparison(result, color=False)
    assert "frame similarity" in text
    assert "overall score" in text
    assert "\033[" not in text


def test_format_comparison_with_color():
    tb = _tb([_frame()])
    result = compare(tb, tb)
    text = format_comparison(result, color=True)
    assert "\033[" in text


def test_overall_score_capped_components():
    f = _frame()
    tb1 = _tb([f], exc_type="E", exc_message="msg")
    tb2 = _tb([f], exc_type="E", exc_message="other")
    result = compare(tb1, tb2)
    # frame_sim=1 *0.6 + exc_type=0.3 + exc_msg=0
    assert result.overall_score == pytest.approx(0.9)
