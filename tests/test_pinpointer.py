"""Tests for stacktrace_filter.pinpointer."""
from __future__ import annotations

import pytest

from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.pinpointer import (
    PinpointResult,
    pinpoint,
    format_pinpoint,
)


def _frame(
    filename: str = "/app/myapp/views.py",
    lineno: int = 42,
    function: str = "handle",
    text: str = "    return process(request)",
) -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, text=text)


def _stdlib_frame() -> Frame:
    return Frame(
        filename="/usr/lib/python3.11/json/__init__.py",
        lineno=10,
        function="loads",
        text="    return _default_decoder.decode(s)",
    )


def _tb(frames, exception="SomeError: boom") -> Traceback:
    return Traceback(frames=frames, exception=exception)


# ---------------------------------------------------------------------------
# pinpoint()
# ---------------------------------------------------------------------------

def test_pinpoint_no_frames_returns_none_frame():
    tb = _tb([])
    result = pinpoint(tb)
    assert isinstance(result, PinpointResult)
    assert result.frame is None
    assert result.index is None
    assert result.reason == "no frames"


def test_pinpoint_single_user_frame():
    frame = _frame()
    tb = _tb([frame])
    result = pinpoint(tb)
    assert result.frame is frame
    assert result.index == 0
    assert "user" in result.reason


def test_pinpoint_prefers_user_over_stdlib():
    stdlib = _stdlib_frame()
    user = _frame()
    tb = _tb([stdlib, user])
    result = pinpoint(tb)
    assert result.frame is user


def test_pinpoint_all_stdlib_returns_innermost():
    f1 = _stdlib_frame()
    f2 = Frame(
        filename="/usr/lib/python3.11/threading.py",
        lineno=5,
        function="run",
        text="    self._target()",
    )
    tb = _tb([f1, f2])
    result = pinpoint(tb)
    # Both stdlib; innermost (last) wins on tie-break
    assert result.frame is f2
    assert result.index == 1


def test_pinpoint_exc_message_boosts_score():
    # frame whose filename appears in the exception message should win
    generic = _frame(filename="/app/other.py", function="other")
    mentioned = _frame(filename="/app/views.py", function="handle")
    tb = _tb([generic, mentioned], exception="KeyError in /app/views.py")
    result = pinpoint(tb)
    assert result.frame is mentioned


def test_pinpoint_index_matches_frame_position():
    frames = [_frame(lineno=i) for i in range(5)]
    tb = _tb(frames)
    result = pinpoint(tb)
    assert tb.frames[result.index] is result.frame


# ---------------------------------------------------------------------------
# format_pinpoint()
# ---------------------------------------------------------------------------

def test_format_pinpoint_no_frame():
    tb = _tb([])
    result = pinpoint(tb)
    output = format_pinpoint(result)
    assert "No frames" in output


def test_format_pinpoint_includes_location():
    frame = _frame(filename="/app/views.py", lineno=99, function="dispatch")
    tb = _tb([frame])
    result = pinpoint(tb)
    output = format_pinpoint(result)
    assert "/app/views.py" in output
    assert "99" in output
    assert "dispatch" in output


def test_format_pinpoint_includes_source_text():
    frame = _frame(text="    raise ValueError('bad')")
    tb = _tb([frame])
    result = pinpoint(tb)
    output = format_pinpoint(result)
    assert "raise ValueError" in output
