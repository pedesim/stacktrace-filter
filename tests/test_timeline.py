"""Tests for stacktrace_filter.timeline."""
from __future__ import annotations

from datetime import datetime

import pytest

from stacktrace_filter.parser import Traceback, Frame
from stacktrace_filter.timeline import (
    Timeline,
    TimestampedTraceback,
    build_timeline,
    format_timeline,
)


def _tb(exc: str) -> Traceback:
    return Traceback(frames=[Frame(filename="app.py", lineno=1, name="f", line="x()")],
                     exception=exc)


T1 = datetime(2024, 1, 1, 10, 0, 0)
T2 = datetime(2024, 1, 1, 11, 0, 0)
T3 = datetime(2024, 1, 1, 9, 0, 0)


def test_build_timeline_length():
    tl = build_timeline([_tb("E1"), _tb("E2")], [T1, T2])
    assert len(tl.entries) == 2


def test_build_timeline_mismatched_lengths():
    with pytest.raises(ValueError):
        build_timeline([_tb("E1")], [T1, T2])


def test_sorted_entries_order():
    tl = build_timeline([_tb("E1"), _tb("E2"), _tb("E3")], [T1, T2, T3])
    sorted_ts = [e.timestamp for e in tl.sorted_entries()]
    assert sorted_ts == sorted(sorted_ts)


def test_labels_attached():
    tl = build_timeline([_tb("E1"), _tb("E2")], [T1, T2], labels=["a", "b"])
    assert tl.entries[0].label == "a"
    assert tl.entries[1].label == "b"


def test_format_timeline_contains_exception():
    tl = build_timeline([_tb("ValueError: bad")], [T1])
    out = format_timeline(tl, color=False)
    assert "ValueError: bad" in out


def test_format_timeline_contains_timestamp():
    tl = build_timeline([_tb("E")], [T1])
    out = format_timeline(tl, color=False)
    assert "2024-01-01 10:00:00" in out


def test_format_timeline_contains_label():
    tl = build_timeline([_tb("E")], [T1], labels=["worker-1"])
    out = format_timeline(tl, color=False)
    assert "worker-1" in out


def test_format_timeline_no_label_no_bracket():
    tl = build_timeline([_tb("E")], [T1])
    out = format_timeline(tl, color=False)
    assert "[" not in out


def test_timeline_add_method():
    tl = Timeline()
    tl.add(_tb("E"), T1, label="x")
    assert len(tl.entries) == 1
    assert isinstance(tl.entries[0], TimestampedTraceback)
