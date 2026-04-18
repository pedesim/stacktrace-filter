"""Tests for stacktrace_filter.sorter."""
import pytest

from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.sorter import (
    RankedTraceback,
    format_ranked,
    sort_tracebacks,
)


def _frame(path: str = "/app/foo.py", lineno: int = 1, name: str = "fn") -> Frame:
    return Frame(filename=path, lineno=lineno, name=name, source_line="pass")


def _tb(exc_type: str, frames: list) -> Traceback:
    return Traceback(
        frames=frames,
        exc_type=exc_type,
        exc_message=f"{exc_type} happened",
    )


def test_sort_by_depth_descending():
    tb_shallow = _tb("ValueError", [_frame()])
    tb_deep = _tb("RuntimeError", [_frame(), _frame(), _frame()])
    ranked = sort_tracebacks([tb_shallow, tb_deep], strategy="depth")
    assert ranked[0].traceback is tb_deep
    assert ranked[0].rank == 1
    assert ranked[1].rank == 2


def test_sort_by_depth_ascending():
    tb_shallow = _tb("ValueError", [_frame()])
    tb_deep = _tb("RuntimeError", [_frame(), _frame()])
    ranked = sort_tracebacks([tb_shallow, tb_deep], strategy="depth", descending=False)
    assert ranked[0].traceback is tb_shallow


def test_sort_by_user_frames():
    stdlib_frame = _frame(path="/usr/lib/python3.11/os.py")
    user_frame = _frame(path="/app/mycode.py")
    tb_mostly_stdlib = _tb("A", [stdlib_frame, stdlib_frame])
    tb_user = _tb("B", [user_frame, user_frame, user_frame])
    ranked = sort_tracebacks([tb_mostly_stdlib, tb_user], strategy="user_frames")
    assert ranked[0].traceback is tb_user


def test_sort_by_exc_type():
    tb_a = _tb("AAA", [_frame()])
    tb_z = _tb("ZZZ", [_frame()])
    ranked = sort_tracebacks([tb_a, tb_z], strategy="exc_type", descending=True)
    assert ranked[0].traceback is tb_z


def test_unknown_strategy_raises():
    with pytest.raises(ValueError, match="Unknown strategy"):
        sort_tracebacks([], strategy="bogus")


def test_empty_list():
    assert sort_tracebacks([], strategy="depth") == []


def test_scores_stored():
    tb = _tb("E", [_frame(), _frame()])
    ranked = sort_tracebacks([tb], strategy="depth")
    assert ranked[0].score == 2.0


def test_format_ranked():
    tb = _tb("ValueError", [_frame()])
    ranked = sort_tracebacks([tb], strategy="depth")
    output = format_ranked(ranked)
    assert "#  1" in output
    assert "ValueError" in output
