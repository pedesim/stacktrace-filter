"""Tests for stacktrace_filter.inspector."""
from __future__ import annotations

import pytest

from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.inspector import (
    InspectionResult,
    inspect,
    format_inspection,
    _categorize,
)


def _frame(filename: str, function: str = "fn", lineno: int = 1) -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, source_line="pass")


def _tb(frames: list, exc_type: str = "ValueError", exc_message: str = "bad") -> Traceback:
    return Traceback(frames=frames, exc_type=exc_type, exc_message=exc_message)


# ---------------------------------------------------------------------------
# _categorize
# ---------------------------------------------------------------------------

def test_categorize_stdlib():
    f = _frame("/usr/lib/python3.11/os.py")
    assert _categorize(f) == "stdlib"


def test_categorize_library():
    f = _frame("/usr/local/lib/python3.11/site-packages/requests/api.py")
    assert _categorize(f) == "library"


def test_categorize_user():
    f = _frame("/home/user/project/app.py")
    assert _categorize(f) == "user"


# ---------------------------------------------------------------------------
# inspect
# ---------------------------------------------------------------------------

def test_inspect_counts():
    frames = [
        _frame("/usr/lib/python3.11/os.py", "getcwd"),
        _frame("/home/user/app.py", "run"),
        _frame("/home/user/app.py", "handle"),
    ]
    result = inspect(_tb(frames))
    assert result.total_frames == 3
    assert result.user_frames == 2
    assert result.stdlib_frames == 1
    assert result.library_frames == 0


def test_inspect_user_ratio():
    frames = [
        _frame("/usr/lib/python3.11/os.py"),
        _frame("/home/user/app.py"),
    ]
    result = inspect(_tb(frames))
    assert result.user_ratio == pytest.approx(0.5)


def test_inspect_no_frames_ratio():
    result = inspect(_tb([]))
    assert result.user_ratio == 0.0
    assert result.has_user_code is False


def test_inspect_deepest_user_frame():
    frames = [
        _frame("/usr/lib/python3.11/os.py", "a"),
        _frame("/home/user/app.py", "b"),
        _frame("/home/user/app.py", "c"),
    ]
    result = inspect(_tb(frames))
    assert result.deepest_user_frame is not None
    assert result.deepest_user_frame.function == "c"


def test_inspect_no_user_frames_deepest_is_none():
    frames = [_frame("/usr/lib/python3.11/os.py")]
    result = inspect(_tb(frames))
    assert result.deepest_user_frame is None
    assert result.has_user_code is False


def test_inspect_unique_files_deduped():
    frames = [
        _frame("/home/user/app.py", "a"),
        _frame("/home/user/app.py", "b"),
        _frame("/home/user/utils.py", "c"),
    ]
    result = inspect(_tb(frames))
    assert len(result.unique_files) == 2


def test_inspect_exc_fields():
    result = inspect(_tb([], exc_type="RuntimeError", exc_message="oops"))
    assert result.exc_type == "RuntimeError"
    assert result.exc_message == "oops"


# ---------------------------------------------------------------------------
# format_inspection
# ---------------------------------------------------------------------------

def test_format_inspection_contains_exc_type():
    result = inspect(_tb([], exc_type="KeyError", exc_message="missing"))
    output = format_inspection(result, color=False)
    assert "KeyError" in output


def test_format_inspection_no_color_no_ansi():
    result = inspect(_tb([]))
    output = format_inspection(result, color=False)
    assert "\033[" not in output


def test_format_inspection_with_color_has_ansi():
    result = inspect(_tb([]))
    output = format_inspection(result, color=True)
    assert "\033[" in output
