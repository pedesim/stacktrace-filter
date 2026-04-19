"""Tests for stacktrace_filter.scorer."""
import pytest
from stacktrace_filter.parser import Traceback, Frame
from stacktrace_filter.scorer import (
    score_traceback,
    score_all,
    format_scored,
    ScoredTraceback,
    _user_frame_ratio,
    _depth_score,
    _exc_type_score,
)


def _frame(filename="app/main.py", lineno=10, name="fn", line="x()"):
    return Frame(filename=filename, lineno=lineno, name=name, line=line)


def _tb(frames=None, exc_type="ValueError", exc_msg="bad"):
    return Traceback(
        frames=frames or [_frame()],
        exception_type=exc_type,
        exception_message=exc_msg,
    )


def test_score_traceback_returns_scored():
    tb = _tb()
    s = score_traceback(tb)
    assert isinstance(s, ScoredTraceback)
    assert 0.0 <= s.score <= 1.0


def test_user_frame_ratio_all_user():
    frames = [_frame("app/a.py"), _frame("app/b.py")]
    tb = _tb(frames=frames)
    assert _user_frame_ratio(tb) == 1.0


def test_user_frame_ratio_stdlib():
    import sys
    import sysconfig
    stdlib = sysconfig.get_path("stdlib")
    frames = [_frame(filename=f"{stdlib}/os.py"), _frame("app/a.py")]
    tb = _tb(frames=frames)
    ratio = _user_frame_ratio(tb)
    assert 0.0 < ratio <= 1.0


def test_user_frame_ratio_empty():
    tb = _tb(frames=[])
    assert _user_frame_ratio(tb) == 0.0


def test_depth_score_capped_at_one():
    frames = [_frame() for _ in range(100)]
    tb = _tb(frames=frames)
    assert _depth_score(tb) == 1.0


def test_depth_score_partial():
    frames = [_frame() for _ in range(25)]
    tb = _tb(frames=frames)
    assert _depth_score(tb) == pytest.approx(0.5)


def test_exc_type_score_critical():
    tb = _tb(exc_type="MemoryError")
    assert _exc_type_score(tb) == 1.0


def test_exc_type_score_warning():
    tb = _tb(exc_type="DeprecationWarning")
    assert _exc_type_score(tb) == 0.2


def test_exc_type_score_default():
    tb = _tb(exc_type="ValueError")
    assert _exc_type_score(tb) == 0.5


def test_score_all_sorted_descending():
    tb_critical = _tb(exc_type="MemoryError")
    tb_warn = _tb(exc_type="DeprecationWarning")
    results = score_all([tb_warn, tb_critical])
    assert results[0].score >= results[1].score


def test_breakdown_keys_present():
    s = score_traceback(_tb())
    assert "user_ratio" in s.breakdown
    assert "depth" in s.breakdown
    assert "exc_type" in s.breakdown


def test_format_scored_contains_score():
    scored = [score_traceback(_tb())]
    out = format_scored(scored, color=False)
    assert "score=" in out


def test_format_scored_empty():
    assert format_scored([], color=False) == ""
