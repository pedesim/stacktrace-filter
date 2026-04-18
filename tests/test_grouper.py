"""Tests for stacktrace_filter.grouper."""
import pytest
from stacktrace_filter.parser import Traceback, Frame
from stacktrace_filter.grouper import (
    TracebackGroup,
    _group_key,
    group_tracebacks,
    format_groups,
)


def _tb(exc_type="ValueError", exc_message="bad value", frames=None):
    return Traceback(
        frames=frames or [
            Frame(filename="app.py", lineno=10, name="run", line="x = 1")
        ],
        exc_type=exc_type,
        exc_message=exc_message,
    )


def test_group_key_basic():
    tb = _tb("TypeError", "  must be int  ")
    assert _group_key(tb) == ("TypeError", "must be int")


def test_group_key_empty():
    tb = _tb("", None)
    assert _group_key(tb) == ("", "")


def test_group_tracebacks_single():
    groups = group_tracebacks([_tb()])
    assert len(groups) == 1
    assert groups[0].count == 1
    assert groups[0].exc_type == "ValueError"


def test_group_tracebacks_duplicates():
    tbs = [_tb("ValueError", "bad"), _tb("ValueError", "bad"), _tb("TypeError", "x")]
    groups = group_tracebacks(tbs)
    assert groups[0].count == 2
    assert groups[0].exc_type == "ValueError"
    assert groups[1].count == 1
    assert groups[1].exc_type == "TypeError"


def test_group_tracebacks_empty():
    assert group_tracebacks([]) == []


def test_group_tracebacks_ordered_desc():
    tbs = (
        [_tb("KeyError", "k")] * 3
        + [_tb("ValueError", "v")] * 5
        + [_tb("TypeError", "t")] * 1
    )
    groups = group_tracebacks(tbs)
    counts = [g.count for g in groups]
    assert counts == sorted(counts, reverse=True)


def test_format_groups_empty():
    out = format_groups([])
    assert "No tracebacks" in out


def test_format_groups_contains_exc_type():
    groups = group_tracebacks([_tb("RuntimeError", "oops")])
    out = format_groups(groups)
    assert "RuntimeError" in out
    assert "oops" in out


def test_format_groups_truncates_long_message():
    long_msg = "x" * 100
    groups = group_tracebacks([_tb("ValueError", long_msg)])
    out = format_groups(groups)
    assert "..." in out
