"""Tests for stacktrace_filter.ranker."""
from __future__ import annotations

import pytest

from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.ranker import (
    RankedEntry,
    _depth_score,
    _exc_type_score,
    _user_frame_score,
    format_rank,
    rank_traceback,
    rank_tracebacks,
)


def _frame(filename: str = "app.py", lineno: int = 10, func: str = "fn") -> Frame:
    return Frame(
        filename=filename,
        lineno=lineno,
        function=func,
        source_line="pass",
        is_stdlib=filename.startswith("/usr/lib"),
        is_site_package=False,
    )


def _tb(
    frames=None,
    exc_type: str = "ValueError",
    exc_message: str = "bad value",
) -> Traceback:
    return Traceback(
        frames=frames or [_frame()],
        exc_type=exc_type,
        exc_message=exc_message,
    )


# ---- unit tests for scoring helpers ----

def test_user_frame_score_all_user():
    tb = _tb(frames=[_frame("app.py"), _frame("models.py")])
    assert _user_frame_score(tb) == 1.0


def test_user_frame_score_no_frames():
    tb = _tb(frames=[])
    assert _user_frame_score(tb) == 0.0


def test_depth_score_capped():
    frames = [_frame() for _ in range(60)]
    tb = _tb(frames=frames)
    assert _depth_score(tb) == 1.0


def test_depth_score_partial():
    frames = [_frame() for _ in range(15)]
    tb = _tb(frames=frames)
    assert _depth_score(tb) == pytest.approx(0.5)


def test_exc_type_score_noisy():
    tb = _tb(exc_type="KeyboardInterrupt")
    assert _exc_type_score(tb) == 0.0


def test_exc_type_score_normal():
    tb = _tb(exc_type="ValueError")
    assert _exc_type_score(tb) == 1.0


def test_exc_type_score_partial():
    tb = _tb(exc_type="RuntimeError")
    assert _exc_type_score(tb) == 0.5


# ---- rank_traceback ----

def test_rank_traceback_returns_ranked_entry():
    entry = rank_traceback(_tb())
    assert isinstance(entry, RankedEntry)
    assert 0.0 <= entry.score <= 1.0


def test_rank_traceback_breakdown_keys():
    entry = rank_traceback(_tb())
    assert set(entry.breakdown) == {"user_frame", "depth", "exc_type", "deepest_user"}


# ---- rank_tracebacks ----

def test_rank_tracebacks_descending_order():
    tb_noisy = _tb(exc_type="KeyboardInterrupt")
    tb_normal = _tb(exc_type="ValueError")
    ranked = rank_tracebacks([tb_noisy, tb_normal])
    assert ranked[0].score >= ranked[1].score


def test_rank_tracebacks_ascending_order():
    tb_noisy = _tb(exc_type="KeyboardInterrupt")
    tb_normal = _tb(exc_type="ValueError")
    ranked = rank_tracebacks([tb_noisy, tb_normal], ascending=True)
    assert ranked[0].score <= ranked[1].score


# ---- format_rank ----

def test_format_rank_contains_score():
    entry = rank_traceback(_tb())
    text = format_rank(entry, index=0)
    assert "score=" in text
    assert "#1" in text


def test_format_rank_contains_exc_type():
    entry = rank_traceback(_tb(exc_type="TypeError"))
    text = format_rank(entry)
    assert "TypeError" in text
