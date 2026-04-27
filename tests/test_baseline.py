"""Tests for stacktrace_filter.baseline."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from stacktrace_filter.baseline import (
    BaselineEntry,
    BaselineReport,
    compare_to_baseline,
    load_baseline,
    save_baseline,
)
from stacktrace_filter.parser import Frame, Traceback


def _frame(filename: str = "app.py", lineno: int = 10, function: str = "fn") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, line="pass")


def _tb(exc_type: str = "ValueError", exc_message: str = "bad", frames: list | None = None) -> Traceback:
    return Traceback(
        frames=frames or [_frame()],
        exc_type=exc_type,
        exc_message=exc_message,
        raw="",
    )


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    tb = _tb()
    out = tmp_path / "baseline.json"
    save_baseline([tb], out)
    loaded = load_baseline(out)
    assert len(loaded) == 1
    entry = next(iter(loaded.values()))
    assert entry.exc_type == "ValueError"
    assert entry.frame_count == 1


def test_save_creates_valid_json(tmp_path: Path) -> None:
    tb = _tb()
    out = tmp_path / "b.json"
    save_baseline([tb], out)
    data = json.loads(out.read_text())
    assert isinstance(data, list)
    assert "fp" in data[0]
    assert "short" in data[0]


def test_compare_no_change(tmp_path: Path) -> None:
    tb = _tb()
    out = tmp_path / "b.json"
    save_baseline([tb], out)
    baseline = load_baseline(out)
    report = compare_to_baseline([tb], baseline)
    assert report.regression_count == 0
    assert report.resolved_count == 0
    assert len(report.persisted) == 1


def test_compare_new_regression(tmp_path: Path) -> None:
    tb_old = _tb(exc_type="ValueError", exc_message="old")
    tb_new = _tb(exc_type="RuntimeError", exc_message="new", frames=[_frame("other.py")])
    out = tmp_path / "b.json"
    save_baseline([tb_old], out)
    baseline = load_baseline(out)
    report = compare_to_baseline([tb_new], baseline)
    assert report.regression_count == 1
    assert report.resolved_count == 1


def test_compare_resolved(tmp_path: Path) -> None:
    tb = _tb()
    out = tmp_path / "b.json"
    save_baseline([tb], out)
    baseline = load_baseline(out)
    report = compare_to_baseline([], baseline)
    assert report.resolved_count == 1
    assert report.regression_count == 0


def test_baseline_report_properties() -> None:
    r = BaselineReport(new=[], resolved=["a", "b"], persisted=["c"])
    assert r.regression_count == 0
    assert r.resolved_count == 2


def test_save_empty_list(tmp_path: Path) -> None:
    out = tmp_path / "empty.json"
    save_baseline([], out)
    loaded = load_baseline(out)
    assert loaded == {}
