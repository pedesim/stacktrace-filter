"""Tests for stacktrace_filter.replayer."""
from __future__ import annotations

import json
import os
import tempfile
from typing import List

import pytest

from stacktrace_filter.archiver import ArchiveEntry, append_entry
from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.replayer import ReplayConfig, iter_replay, replay


def _frame(filename: str = "app.py", lineno: int = 10, function: str = "fn") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, source_line="pass")


def _tb(exc: str = "ValueError", msg: str = "oops") -> Traceback:
    return Traceback(frames=[_frame()], exception=f"{exc}: {msg}")


def _write_archive(path: str, entries: List[tuple]) -> None:
    for label, tb in entries:
        append_entry(path, tb, label=label)


def test_replay_returns_all_entries(tmp_path):
    archive = str(tmp_path / "arc.jsonl")
    _write_archive(archive, [("a", _tb()), ("b", _tb()), ("c", _tb())])
    result = replay(archive)
    assert result.total == 3
    assert result.skipped == 0


def test_replay_max_entries(tmp_path):
    archive = str(tmp_path / "arc.jsonl")
    _write_archive(archive, [("a", _tb()), ("b", _tb()), ("c", _tb())])
    result = replay(archive, config=ReplayConfig(max_entries=2))
    assert result.total == 2


def test_replay_reverse(tmp_path):
    archive = str(tmp_path / "arc.jsonl")
    _write_archive(archive, [("first", _tb()), ("second", _tb())])
    result = replay(archive, config=ReplayConfig(reverse=True))
    assert result.entries[0].label == "second"
    assert result.entries[1].label == "first"


def test_replay_filter_label(tmp_path):
    archive = str(tmp_path / "arc.jsonl")
    _write_archive(archive, [("keep", _tb()), ("drop", _tb()), ("keep", _tb())])
    result = replay(archive, config=ReplayConfig(filter_label="keep"))
    assert result.total == 2
    assert result.skipped == 1


def test_replay_callback_called(tmp_path):
    archive = str(tmp_path / "arc.jsonl")
    _write_archive(archive, [("x", _tb()), ("y", _tb())])
    seen: list = []
    replay(archive, callback=lambda e: seen.append(e.label))
    assert seen == ["x", "y"]


def test_iter_replay_yields_entries(tmp_path):
    archive = str(tmp_path / "arc.jsonl")
    _write_archive(archive, [("a", _tb()), ("b", _tb())])
    entries = list(iter_replay(archive))
    assert len(entries) == 2


def test_iter_replay_filter_label(tmp_path):
    archive = str(tmp_path / "arc.jsonl")
    _write_archive(archive, [("yes", _tb()), ("no", _tb()), ("yes", _tb())])
    entries = list(iter_replay(archive, config=ReplayConfig(filter_label="yes")))
    assert len(entries) == 2
    assert all(e.label == "yes" for e in entries)


def test_replay_empty_archive(tmp_path):
    archive = str(tmp_path / "empty.jsonl")
    archive_path = open(archive, "w").close()
    result = replay(archive)
    assert result.total == 0
