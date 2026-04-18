"""Tests for frame deduplication."""
import pytest
from stacktrace_filter.parser import Frame
from stacktrace_filter.deduplicator import (
    deduplicate_frames,
    DeduplicatedGroup,
    render_dedup_groups,
    _frames_equal,
)


def _frame(filename="app.py", lineno=10, name="foo", line="pass"):
    return Frame(filename=filename, lineno=lineno, name=name, line=line)


def test_empty():
    assert deduplicate_frames([]) == []


def test_single_frame():
    f = _frame()
    groups = deduplicate_frames([f])
    assert len(groups) == 1
    assert groups[0].count == 1
    assert groups[0].frame is f


def test_no_duplicates():
    frames = [_frame(lineno=1), _frame(lineno=2), _frame(lineno=3)]
    groups = deduplicate_frames(frames)
    assert len(groups) == 3
    assert all(g.count == 1 for g in groups)


def test_consecutive_duplicates():
    f = _frame(lineno=5)
    frames = [f, _frame(lineno=5), _frame(lineno=5)]
    groups = deduplicate_frames(frames)
    assert len(groups) == 1
    assert groups[0].count == 3


def test_non_consecutive_duplicates():
    f1 = _frame(lineno=1)
    f2 = _frame(lineno=2)
    frames = [f1, f2, _frame(lineno=1)]
    groups = deduplicate_frames(frames)
    assert len(groups) == 3
    assert groups[0].count == 1


def test_mixed_duplicates():
    frames = [
        _frame(lineno=1), _frame(lineno=1),
        _frame(lineno=2),
        _frame(lineno=3), _frame(lineno=3), _frame(lineno=3),
    ]
    groups = deduplicate_frames(frames)
    assert len(groups) == 3
    assert groups[0].count == 2
    assert groups[1].count == 1
    assert groups[2].count == 3


def test_frames_equal_same():
    f = _frame()
    assert _frames_equal(f, f)


def test_frames_equal_different_lineno():
    assert not _frames_equal(_frame(lineno=1), _frame(lineno=2))


def test_render_no_repeats():
    groups = [DeduplicatedGroup(frame=_frame(), count=1)]
    lines = render_dedup_groups(groups, color=False)
    assert len(lines) == 1
    assert "repeated" not in lines[0]


def test_render_with_repeats_no_color():
    groups = [DeduplicatedGroup(frame=_frame(), count=4)]
    lines = render_dedup_groups(groups, color=False)
    assert "repeated 4x" in lines[0]


def test_render_with_repeats_color():
    groups = [DeduplicatedGroup(frame=_frame(), count=2)]
    lines = render_dedup_groups(groups, color=True)
    assert "repeated 2x" in lines[0]
    assert "\033[" in lines[0]
