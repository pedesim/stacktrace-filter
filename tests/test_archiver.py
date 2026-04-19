"""Tests for archiver module and CLI."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from stacktrace_filter.archiver import (
    ArchiveEntry,
    append_entry,
    archive_many,
    entry_to_dict,
    load_archive,
)
from stacktrace_filter.parser import Frame, Traceback


def _frame(fn="app.py", lineno=10, func="run", src="x()"):
    return Frame(filename=fn, lineno=lineno, function=func, source=src)


def _tb(exc="ValueError: bad"):
    return Traceback(frames=[_frame()], exception=exc)


def test_entry_to_dict_keys():
    e = ArchiveEntry(traceback=_tb(), timestamp=1000.0, label="test")
    d = entry_to_dict(e)
    assert d["timestamp"] == 1000.0
    assert d["label"] == "test"
    assert "traceback" in d


def test_append_and_load_roundtrip(tmp_path):
    p = tmp_path / "archive.ndjson"
    entry = ArchiveEntry(traceback=_tb(), timestamp=42.0, label="lbl")
    append_entry(p, entry)
    entries = list(load_archive(p))
    assert len(entries) == 1
    assert entries[0].label == "lbl"
    assert abs(entries[0].timestamp - 42.0) < 0.001
    assert entries[0].traceback.exception == "ValueError: bad"


def test_archive_many(tmp_path):
    p = tmp_path / "archive.ndjson"
    tbs = [ArchiveEntry(traceback=_tb(f"Err{i}: x"), label=str(i)) for i in range(5)]
    count = archive_many(p, tbs)
    assert count == 5
    loaded = list(load_archive(p))
    assert len(loaded) == 5


def test_load_archive_empty_lines(tmp_path):
    p = tmp_path / "archive.ndjson"
    entry = ArchiveEntry(traceback=_tb(), timestamp=1.0)
    append_entry(p, entry)
    # inject blank line
    with p.open("a") as fh:
        fh.write("\n")
    loaded = list(load_archive(p))
    assert len(loaded) == 1


def test_cli_append_and_list(tmp_path):
    from stacktrace_filter.archiver_cli import main

    tb_text = (
        "Traceback (most recent call last):\n"
        '  File "app.py", line 5, in run\n'
        "    do()\n"
        "RuntimeError: boom\n"
    )
    inp = tmp_path / "tb.txt"
    inp.write_text(tb_text)
    archive = tmp_path / "out.ndjson"

    main([str(archive), "append", str(inp), "--label", "ci"])
    assert archive.exists()

    entries = list(load_archive(archive))
    assert entries[0].label == "ci"


def test_cli_list_count(tmp_path, capsys):
    from stacktrace_filter.archiver_cli import main

    p = tmp_path / "arc.ndjson"
    archive_many(p, [ArchiveEntry(traceback=_tb(), label="x") for _ in range(3)])
    main([str(p), "list", "--count"])
    out = capsys.readouterr().out.strip()
    assert out == "3"


def test_cli_missing_archive_list(tmp_path):
    from stacktrace_filter.archiver_cli import main

    with pytest.raises(SystemExit):
        main([str(tmp_path / "nope.ndjson"), "list"])
