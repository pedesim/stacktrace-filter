"""Tests for traceback parsing and formatting."""
import pytest
from stacktrace_filter.parser import parse, Frame, Traceback
from stacktrace_filter.formatter import format_traceback

SAMPLE_TB = """\
Traceback (most recent call last):
  File "/home/user/project/app.py", line 42, in main
    result = compute(x)
  File "/usr/lib/python3.11/functools.py", line 888, in wrapper
    return func(*args, **kwargs)
  File "/home/user/project/compute.py", line 10, in compute
    raise ValueError("bad input")
ValueError: bad input
"""


def test_parse_frame_count():
    tb = parse(SAMPLE_TB)
    assert len(tb.frames) == 3


def test_parse_frame_attributes():
    tb = parse(SAMPLE_TB)
    first = tb.frames[0]
    assert first.path == "/home/user/project/app.py"
    assert first.lineno == 42
    assert first.func == "main"
    assert first.code == "result = compute(x)"


def test_parse_exception():
    tb = parse(SAMPLE_TB)
    assert tb.exception == "ValueError"
    assert tb.message == "bad input"


def test_is_stdlib():
    tb = parse(SAMPLE_TB)
    stdlib_frame = tb.frames[1]
    assert stdlib_frame.is_stdlib is True
    assert tb.frames[0].is_stdlib is False


def test_format_collapses_stdlib():
    tb = parse(SAMPLE_TB)
    output = format_traceback(tb, collapse_stdlib=True, color=False)
    assert "collapsed" in output
    assert "functools.py" not in output


def test_format_no_collapse():
    tb = parse(SAMPLE_TB)
    output = format_traceback(tb, collapse_stdlib=False, color=False)
    assert "functools.py" in output
    assert "collapsed" not in output


def test_format_contains_exception():
    tb = parse(SAMPLE_TB)
    output = format_traceback(tb, color=False)
    assert "ValueError: bad input" in output


def test_empty_traceback():
    tb = parse("")
    assert tb.frames == []
    assert tb.exception is None
    output = format_traceback(tb, color=False)
    assert "Traceback" in output
