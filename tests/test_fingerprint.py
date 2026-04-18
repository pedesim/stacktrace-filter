"""Tests for stacktrace_filter.fingerprint."""
import pytest
from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.fingerprint import (
    fingerprint,
    fingerprint_group,
    are_similar,
    Fingerprint,
)


def _frame(filename="app.py", lineno=10, name="fn", line="pass"):
    return Frame(filename=filename, lineno=lineno, name=name, line=line)


def _tb(frames, exc="ValueError: bad"):
    return Traceback(frames=frames, exception_line=exc)


def test_fingerprint_returns_fingerprint_instance():
    tb = _tb([_frame()])
    fp = fingerprint(tb)
    assert isinstance(fp, Fingerprint)
    assert len(fp.hex) == 64  # sha256 hex


def test_short_fingerprint_length():
    tb = _tb([_frame()])
    fp = fingerprint(tb)
    assert len(fp.short()) == 8
    assert len(fp.short(12)) == 12


def test_same_traceback_same_fingerprint():
    tb1 = _tb([_frame()])
    tb2 = _tb([_frame()])
    assert fingerprint(tb1).hex == fingerprint(tb2).hex


def test_different_exc_type_different_fingerprint():
    tb1 = _tb([_frame()], exc="ValueError: x")
    tb2 = _tb([_frame()], exc="TypeError: x")
    assert fingerprint(tb1).hex != fingerprint(tb2).hex


def test_different_lineno_different_fingerprint():
    tb1 = _tb([_frame(lineno=1)])
    tb2 = _tb([_frame(lineno=99)])
    assert fingerprint(tb1).hex != fingerprint(tb2).hex


def test_ignore_line_numbers_makes_similar():
    tb1 = _tb([_frame(lineno=1)])
    tb2 = _tb([_frame(lineno=99)])
    fp1 = fingerprint(tb1, include_line_numbers=False)
    fp2 = fingerprint(tb2, include_line_numbers=False)
    assert fp1.hex == fp2.hex


def test_frame_keys_populated():
    tb = _tb([_frame(filename="a.py", lineno=5, name="go")])
    fp = fingerprint(tb)
    assert fp.frame_keys == ["a.py:5:go"]


def test_exc_type_extracted():
    tb = _tb([_frame()], exc="KeyError: 'missing'")
    fp = fingerprint(tb)
    assert fp.exc_type == "KeyError"


def test_fingerprint_group_length():
    tbs = [_tb([_frame(lineno=i)]) for i in range(5)]
    fps = fingerprint_group(tbs)
    assert len(fps) == 5


def test_are_similar_identical():
    tb = _tb([_frame()])
    assert are_similar(tb, tb) is True


def test_are_similar_different():
    tb1 = _tb([_frame(name="foo")])
    tb2 = _tb([_frame(name="bar")])
    assert are_similar(tb1, tb2) is False


def test_are_similar_ignoring_lineno():
    tb1 = _tb([_frame(lineno=1)])
    tb2 = _tb([_frame(lineno=2)])
    assert are_similar(tb1, tb2, include_line_numbers=False) is True
