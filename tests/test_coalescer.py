"""Tests for stacktrace_filter.coalescer."""
import pytest

from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.coalescer import (
    CoalescedGroup,
    CoalesceResult,
    _root_cause_key,
    coalesce,
    format_coalesce_result,
)


def _frame(filename: str = "app.py", lineno: int = 10, function: str = "fn") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, line="pass")


def _tb(
    frames=None,
    exc_type: str = "ValueError",
    exc_message: str = "bad value",
) -> Traceback:
    return Traceback(
        frames=frames or [_frame()],
        exc_type=exc_type,
        exc_message=exc_message,
    )


# --- _root_cause_key ---

def test_root_cause_key_uses_last_frame():
    tb = _tb(frames=[_frame("a.py", 1, "foo"), _frame("b.py", 2, "bar")])
    assert _root_cause_key(tb) == "b.py:2:bar"


def test_root_cause_key_no_frames_returns_none():
    tb = _tb(frames=[])
    assert _root_cause_key(tb) is None


# --- coalesce ---

def test_coalesce_empty_list():
    result = coalesce([])
    assert result.total == 0
    assert result.group_count == 0


def test_coalesce_single_traceback():
    result = coalesce([_tb()])
    assert result.total == 1
    assert result.group_count == 1


def test_coalesce_identical_root_causes_grouped():
    frame = _frame("app.py", 42, "crash")
    tb1 = _tb(frames=[frame], exc_type="ValueError")
    tb2 = _tb(frames=[frame], exc_type="ValueError")
    result = coalesce([tb1, tb2])
    assert result.group_count == 1
    assert result.total == 2


def test_coalesce_different_root_causes_separate_groups():
    tb1 = _tb(frames=[_frame("a.py", 1, "f1")])
    tb2 = _tb(frames=[_frame("b.py", 2, "f2")])
    result = coalesce([tb1, tb2])
    assert result.group_count == 2


def test_coalesce_no_frames_grouped_under_no_frames_key():
    tb1 = _tb(frames=[])
    tb2 = _tb(frames=[])
    result = coalesce([tb1, tb2])
    assert result.group_count == 1
    assert result.groups[0].root_cause_key == "<no-frames>"


def test_coalesce_representative_is_first_member():
    frame = _frame("app.py", 5, "go")
    tb1 = _tb(frames=[frame], exc_type="TypeError")
    tb2 = _tb(frames=[frame], exc_type="TypeError")
    result = coalesce([tb1, tb2])
    assert result.groups[0].representative is tb1


def test_coalesce_get_returns_group():
    tb = _tb(frames=[_frame("x.py", 3, "run")])
    result = coalesce([tb])
    group = result.get("x.py:3:run")
    assert group is not None
    assert group.count == 1


def test_coalesce_get_missing_key_returns_none():
    result = coalesce([_tb()])
    assert result.get("nonexistent") is None


def test_coalesced_group_exc_types_deduped():
    frame = _frame()
    tb1 = _tb(frames=[frame], exc_type="ValueError")
    tb2 = _tb(frames=[frame], exc_type="ValueError")
    tb3 = _tb(frames=[frame], exc_type="TypeError")
    result = coalesce([tb1, tb2, tb3])
    group = result.groups[0]
    assert sorted(group.exc_types) == ["TypeError", "ValueError"]


# --- format_coalesce_result ---

def test_format_coalesce_result_no_color():
    tb = _tb(frames=[_frame("app.py", 10, "main")])
    result = coalesce([tb])
    output = format_coalesce_result(result, color=False)
    assert "1 group" in output
    assert "app.py:10:main" in output


def test_format_coalesce_result_shows_count():
    frame = _frame("app.py", 1, "fn")
    tbs = [_tb(frames=[frame]) for _ in range(3)]
    result = coalesce(tbs)
    output = format_coalesce_result(result, color=False)
    assert "3 occurrence" in output
