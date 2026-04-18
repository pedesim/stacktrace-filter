"""Tests for stacktrace_filter.stats."""
import pytest
from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.stats import TracebackStats, compute_stats, format_stats


def _frame(path: str, func: str = "fn", lineno: int = 1) -> Frame:
    return Frame(path=path, lineno=lineno, func=func, src_line="pass")


def _tb(*frames: Frame, exc_type="ValueError", exc_msg="bad") -> Traceback:
    return Traceback(frames=list(frames), exc_type=exc_type, exc_msg=excndef test_compute_stats_empty():
    tb = _tb()
    stats = compute_stats(tb)
    assert stats.total_frames == 0
    assert stats.user_frames == 0
_files == 0


def test_compute_stats_counts():
    tb = _tb(
        _frame("/home/user/app/main.py"),
        _frame("/home.py"),
        _frame("/usr/lib/python3.11/os.py"),
        _frame("/usr/lib/python3.11/pathlib.py"),
        _frame("/home/user/venv/lib/python3.11/site-packages/requests/api.py"),
    )
    stats = compute_stats(tb)
    assert stats.total_frames == 5
    assert stats.user_frames == 2
    assert stats.stdlib_frames == 2
    assert stats.site_package_frames == 1


def test_compute_stats_unique_files():
    tb = _tb(
        _frame("/home/user/app/main.py"),
        _frame("/home/user/app/main.py"),
        _frame("/home/user/app/utils.py"),
    )
    stats = compute_n    assert stats.unique_files == 2


def test_compute_stats_top_files():
    tb = _tb(
        _frame("/home/user/app/main.py"),
        _frame("/home/user/app/mainframe("/home/user/app/utils.py"),
    )
    stats = compute_stats(tb, top_n=1)
    assert stats.top_files[0] == ("/home/user/app/main.py", 2)
    assert len(stats.top_files) == 1


def test_compute_stats_exception_fields():
    tb = _tb(exc_type="KeyError", exc_msg="'missing'")
    stats = compute_stats(tb)
    assert stats.exception_type == "KeyError"
    assert stats.exception_msg == "'missing'"


def test_format_stats_contains_key_info():
    tb = _tb(
        _frame("/home/user/app/main.py"),
        _frame("/usr/lib/python3.11/os.py"),
        exc_type="RuntimeError",
        exc_msg="oops",
    )
    stats = compute_stats(tb)
    output = format_stats(stats)
    assert "RuntimeError" in output
    assert "oops" in output
    assert "2 total" in output
    assert "1 user" in output
    assert "1 stdlib" in output
