"""Tests for stacktrace_filter.snapshot."""
import time
import pytest
from stacktrace_filter.snapshot import (
    take_snapshot, diff_snapshots, format_snapshot_diff, Snapshot, SnapshotDiff
)
from stacktrace_filter.parser import Traceback, Frame


def _frame(filename="app.py", lineno=10, name="fn", line="pass"):
    return Frame(filename=filename, lineno=lineno, name=name, line=line)


def _tb(exc_type="ValueError", exc_message="bad", frames=None):
    return Traceback(
        frames=frames or [_frame()],
        exc_type=exc_type,
        exc_message=exc_message,
    )


def test_take_snapshot_label():
    snap = take_snapshot([_tb()], label="my-snap")
    assert snap.label == "my-snap"
    assert len(snap.tracebacks) == 1


def test_take_snapshot_auto_label():
    snap = take_snapshot([], )
    assert snap.label.startswith("snapshot-")


def test_take_snapshot_metadata():
    snap = take_snapshot([_tb()], label="x", env="prod")
    assert snap.metadata["env"] == "prod"


def test_diff_snapshots_added():
    tb1 = _tb(exc_type="KeyError", exc_message="k")
    tb2 = _tb(exc_type="ValueError", exc_message="v")
    before = take_snapshot([tb1], label="before")
    after = take_snapshot([tb1, tb2], label="after")
    diff = diff_snapshots(before, after)
    assert len(diff.added) == 1
    assert diff.added[0].exc_type == "ValueError"
    assert len(diff.removed) == 0
    assert diff.unchanged_count == 1


def test_diff_snapshots_removed():
    tb1 = _tb(exc_type="KeyError", exc_message="k")
    before = take_snapshot([tb1], label="before")
    after = take_snapshot([], label="after")
    diff = diff_snapshots(before, after)
    assert len(diff.removed) == 1
    assert len(diff.added) == 0
    assert diff.unchanged_count == 0


def test_diff_snapshots_unchanged():
    tb = _tb()
    before = take_snapshot([tb], label="a")
    after = take_snapshot([tb], label="b")
    diff = diff_snapshots(before, after)
    assert diff.unchanged_count == 1
    assert diff.added == []
    assert diff.removed == []


def test_diff_elapsed():
    before = take_snapshot([], label="a")
    time.sleep(0.05)
    after = take_snapshot([], label="b")
    diff = diff_snapshots(before, after)
    assert diff.elapsed >= 0.04


def test_format_snapshot_diff_no_color():
    tb = _tb(exc_type="IOError", exc_message="disk full")
    before = take_snapshot([], label="a")
    after = take_snapshot([tb], label="b")
    diff = diff_snapshots(before, after)
    out = format_snapshot_diff(diff, color=False)
    assert "+1 added" in out
    assert "IOError" in out
    assert "\033[" not in out


def test_format_snapshot_diff_color():
    before = take_snapshot([_tb()], label="a")
    after = take_snapshot([], label="b")
    diff = diff_snapshots(before, after)
    out = format_snapshot_diff(diff, color=True)
    assert "\033[" in out
    assert "-1 removed" in out
