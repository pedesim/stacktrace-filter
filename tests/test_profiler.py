"""Tests for stacktrace_filter.profiler."""
from __future__ import annotations
import pytest
from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.profiler import profile, format_profile, ProfileReport


def _frame(filename: str = "app.py", function: str = "run", lineno: int = 1) -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, source_line="pass")


def _tb(*frames: Frame, exc_type: str = "ValueError", exc_msg: str = "oops") -> Traceback:
    return Traceback(frames=list(frames), exc_type=exc_type, exc_message=exc_msg)


def test_profile_empty():
    report = profile([])
    assert report.total_tracebacks == 0
    assert report.total_frames == 0
    assert report.top_frames == []
    assert report.top_files == []
    assert report.top_functions == []


def test_profile_single_traceback():
    tb = _tb(_frame("a.py", "foo"), _frame("b.py", "bar"))
    report = profile([tb])
    assert report.total_tracebacks == 1
    assert report.total_frames == 2
    assert len(report.top_frames) == 2


def test_profile_counts_repeated_frames():
    f = _frame("app.py", "run")
    tb1 = _tb(f)
    tb2 = _tb(f)
    report = profile([tb1, tb2])
    assert report.top_frames[0].count == 2
    assert report.top_frames[0].function == "run"


def test_profile_pct_calculation():
    f = _frame("app.py", "run")
    report = profile([_tb(f), _tb(f), _tb(f)], top_n=5)
    assert report.top_frames[0].pct == 100.0


def test_profile_top_n_limits_results():
    frames = [_frame(f"f{i}.py", f"fn{i}") for i in range(20)]
    tb = _tb(*frames)
    report = profile([tb], top_n=5)
    assert len(report.top_frames) <= 5
    assert len(report.top_files) <= 5
    assert len(report.top_functions) <= 5


def test_profile_top_files_ordering():
    tb1 = _tb(_frame("hot.py", "a"), _frame("hot.py", "b"))
    tb2 = _tb(_frame("cold.py", "c"))
    report = profile([tb1, tb2])
    files = [f for f, _ in report.top_files]
    assert files[0] == "hot.py"


def test_format_profile_contains_sections():
    tb = _tb(_frame("app.py", "main"))
    report = profile([tb])
    text = format_profile(report)
    assert "Top frames" in text
    assert "Top files" in text
    assert "Top functions" in text
    assert "main" in text
    assert "app.py" in text
