"""Tests for stacktrace_filter.recommender."""
from __future__ import annotations

import pytest

from stacktrace_filter.parser import Traceback
from stacktrace_filter.recommender import (
    Recommendation,
    recommend,
    format_recommendation,
    _match_advice,
    _GENERIC_ADVICE,
)


def _frame(filename="app.py", lineno=10, func="run", text="raise ValueError()"):
    from stacktrace_filter.parser import Frame
    return Frame(filename=filename, lineno=lineno, func=func, text=text)


def _tb(exc_type="ValueError", exc_msg="bad input", frames=None):
    if frames is None:
        frames = [_frame()]
    return Traceback(frames=frames, exc_type=exc_type, exc_message=exc_msg)


# --- _match_advice ---

def test_match_advice_known_type():
    advice, generic = _match_advice("KeyError", "")
    assert "`.get()`" in advice
    assert generic is False


def test_match_advice_unknown_type():
    advice, generic = _match_advice("BogusError", "something")
    assert advice == _GENERIC_ADVICE
    assert generic is True


def test_match_advice_import_error():
    advice, generic = _match_advice("ImportError", "No module named 'foo'")
    assert "pip install" in advice
    assert generic is False


# --- recommend ---

def test_recommend_returns_recommendation():
    tb = _tb(exc_type="KeyError", exc_msg="'missing_key'")
    rec = recommend(tb)
    assert isinstance(rec, Recommendation)


def test_recommend_exc_type_preserved():
    tb = _tb(exc_type="IndexError", exc_msg="list index out of range")
    rec = recommend(tb)
    assert rec.exc_type == "IndexError"


def test_recommend_known_type_not_generic():
    tb = _tb(exc_type="TypeError", exc_msg="unsupported operand")
    rec = recommend(tb)
    assert rec.generic is False


def test_recommend_unknown_type_is_generic():
    tb = _tb(exc_type="CustomError", exc_msg="something weird")
    rec = recommend(tb)
    assert rec.generic is True


def test_recommend_pinpoints_user_frame():
    frames = [_frame(filename="myapp/views.py", lineno=42)]
    tb = _tb(frames=frames)
    rec = recommend(tb)
    assert rec.pinpointed_file == "myapp/views.py"
    assert rec.pinpointed_line == 42


def test_recommend_no_frames_pin_is_none():
    tb = Traceback(frames=[], exc_type="RuntimeError", exc_message="oops")
    rec = recommend(tb)
    assert rec.pinpointed_file is None
    assert rec.pinpointed_line is None


# --- format_recommendation ---

def test_format_recommendation_contains_exc_type():
    tb = _tb(exc_type="ValueError")
    rec = recommend(tb)
    output = format_recommendation(rec, color=False)
    assert "ValueError" in output


def test_format_recommendation_contains_advice():
    tb = _tb(exc_type="ZeroDivisionError")
    rec = recommend(tb)
    output = format_recommendation(rec, color=False)
    assert rec.advice in output


def test_format_recommendation_with_color_has_ansi():
    tb = _tb(exc_type="KeyError")
    rec = recommend(tb)
    output = format_recommendation(rec, color=True)
    assert "\033[" in output


def test_format_recommendation_no_color_no_ansi():
    tb = _tb(exc_type="KeyError")
    rec = recommend(tb)
    output = format_recommendation(rec, color=False)
    assert "\033[" not in output


def test_format_recommendation_shows_location():
    frames = [_frame(filename="src/main.py", lineno=99)]
    tb = _tb(frames=frames)
    rec = recommend(tb)
    output = format_recommendation(rec, color=False)
    assert "src/main.py" in output
    assert "99" in output
