"""Tests for stacktrace_filter.flattener."""
import pytest
from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.chain import ChainedTraceback
from stacktrace_filter.flattener import (
    flatten,
    format_flattened,
    LabeledFrame,
    FlattenedTraceback,
)


def _frame(filename="app.py", lineno=10, name="foo", line="x = 1") -> Frame:
    return Frame(filename=filename, lineno=lineno, name=name, line=line)


def _tb(frames, exc="ValueError: bad") -> Traceback:
    return Traceback(frames=frames, exception_line=exc)


def test_flatten_single_traceback():
    tb = _tb([_frame()])
    chained = ChainedTraceback(tracebacks=[tb], links=[])
    ft = flatten(chained)
    assert ft.total_frames == 1
    assert ft.chain_labels == ["origin"]


def test_flatten_two_tracebacks_frame_count():
    tb1 = _tb([_frame("a.py"), _frame("b.py")])
    tb2 = _tb([_frame("c.py")])
    chained = ChainedTraceback(tracebacks=[tb1, tb2], links=["cause"])
    ft = flatten(chained)
    assert ft.total_frames == 3


def test_flatten_chain_indices():
    tb1 = _tb([_frame("a.py")])
    tb2 = _tb([_frame("b.py")])
    chained = ChainedTraceback(tracebacks=[tb1, tb2], links=["cause"])
    ft = flatten(chained)
    assert ft.frames[0].chain_index == 0
    assert ft.frames[1].chain_index == 1


def test_flatten_origin_label_last():
    tb1 = _tb([_frame()])
    tb2 = _tb([_frame()])
    chained = ChainedTraceback(tracebacks=[tb1, tb2], links=["context"])
    ft = flatten(chained)
    assert ft.chain_labels[-1] == "origin"


def test_flatten_exception_lines_collected():
    tb1 = _tb([_frame()], exc="TypeError: oops")
    tb2 = _tb([_frame()], exc="ValueError: bad")
    chained = ChainedTraceback(tracebacks=[tb1, tb2], links=[])
    ft = flatten(chained)
    assert "TypeError: oops" in ft.exception_lines
    assert "ValueError: bad" in ft.exception_lines


def test_frames_for_chain_filters_correctly():
    tb1 = _tb([_frame("a.py"), _frame("b.py")])
    tb2 = _tb([_frame("c.py")])
    chained = ChainedTraceback(tracebacks=[tb1, tb2], links=[])
    ft = flatten(chained)
    assert len(ft.frames_for_chain(0)) == 2
    assert len(ft.frames_for_chain(1)) == 1


def test_format_flattened_contains_filename():
    tb = _tb([_frame("myapp.py", lineno=42)])
    chained = ChainedTraceback(tracebacks=[tb], links=[])
    ft = flatten(chained)
    output = format_flattened(ft, color=False)
    assert "myapp.py" in output
    assert "42" in output


def test_format_flattened_no_color_no_ansi():
    tb = _tb([_frame()])
    chained = ChainedTraceback(tracebacks=[tb], links=[])
    ft = flatten(chained)
    output = format_flattened(ft, color=False)
    assert "\033[" not in output


def test_format_flattened_with_color_has_ansi():
    tb = _tb([_frame()])
    chained = ChainedTraceback(tracebacks=[tb], links=[])
    ft = flatten(chained)
    output = format_flattened(ft, color=True)
    assert "\033[" in output
