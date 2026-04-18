"""Tests for summarizer and report modules."""
import pytest
from stacktrace_filter.parser import Traceback, Frame
from stacktrace_filter.summarizer import summarize, TracebackSummary
from stacktrace_filter.report import render_report, render_frame_table


def _make_tb(frames, exc_type="ValueError", exc_msg="bad input"):
    return Traceback(frames=frames, exc_type=exc_type, exc_msg=exc_msg)


def _frame(filename, lineno=10, name="fn", line="pass"):
    return Frame(filename=filename, lineno=lineno, name=name, line=line)


USER_FILE = "/home/user/project/app.py"
STDLIB_FILE = "/usr/lib/python3.11/os.py"
SITE_FILE = "/usr/lib/python3.11/site-packages/requests/api.py"


def test_summarize_counts():
    tb = _make_tb([
        _frame(USER_FILE),
        _frame(STDLIB_FILE),
        _frame(SITE_FILE),
        _frame(USER_FILE, lineno=42),
    ])
    s = summarize(tb)
    assert s.user_frame_count == 2
    assert s.stdlib_frame_count == 1
    assert s.site_frame_count == 1
    assert len(s.frames) == 4


def test_summarize_deepest_user_frame():
    tb = _make_tb([
        _frame(STDLIB_FILE),
        _frame(USER_FILE, lineno=99, name="my_func"),
    ])
    s = summarize(tb)
    assert s.deepest_user_frame is not None
    assert s.deepest_user_frame.lineno == 99
    assert s.deepest_user_frame.name == "my_func"


def test_summarize_no_user_frames():
    tb = _make_tb([_frame(STDLIB_FILE)])
    s = summarize(tb)
    assert s.deepest_user_frame is None
    assert s.user_frame_count == 0


def test_summarize_exception_fields():
    tb = _make_tb([], exc_type="KeyError", exc_msg="'missing'")
    s = summarize(tb)
    assert s.exception_type == "KeyError"
    assert s.exception_msg == "'missing'"


def test_render_report_contains_exception():
    tb = _make_tb([_frame(USER_FILE)], exc_type="RuntimeError", exc_msg="oops")
    s = summarize(tb)
    report = render_report(s, color=False)
    assert "RuntimeError" in report
    assert "oops" in report


def test_render_report_frame_counts():
    tb = _make_tb([_frame(USER_FILE), _frame(STDLIB_FILE)])
    s = summarize(tb)
    report = render_report(s, color=False)
    assert "2 total" in report
    assert "1 user" in report


def test_render_frame_table_rows():
    tb = _make_tb([_frame(USER_FILE, lineno=5, name="run")])
    s = summarize(tb)
    table = render_frame_table(s)
    assert "run" in table
    assert "user" in table
