"""Tests for stacktrace_filter.baseline_cli."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from stacktrace_filter.baseline_cli import build_baseline_parser, main

_SAMPLE_TB = """Traceback (most recent call last):
  File \"app.py\", line 10, in run
    result = compute()
ValueError: bad input
"""


def test_build_baseline_parser_defaults() -> None:
    p = build_baseline_parser()
    args = p.parse_args(["capture"])
    assert args.mode == "capture"
    assert args.baseline == "baseline.json"
    assert args.input is None
    assert args.no_color is False


def test_build_baseline_parser_compare_mode() -> None:
    p = build_baseline_parser()
    args = p.parse_args(["compare", "--baseline", "my.json", "trace.txt"])
    assert args.mode == "compare"
    assert args.baseline == "my.json"
    assert args.input == "trace.txt"


def test_main_capture_stdin(tmp_path: Path, capsys) -> None:
    baseline_file = tmp_path / "b.json"
    with patch("sys.stdin") as mock_stdin:
        mock_stdin.read.return_value = _SAMPLE_TB
        main(["capture", "--baseline", str(baseline_file)])
    out = capsys.readouterr().out
    assert "Baseline saved" in out
    assert baseline_file.exists()


def test_main_capture_file(tmp_path: Path, capsys) -> None:
    input_file = tmp_path / "trace.txt"
    input_file.write_text(_SAMPLE_TB)
    baseline_file = tmp_path / "b.json"
    main(["capture", "--baseline", str(baseline_file), str(input_file)])
    out = capsys.readouterr().out
    assert "Baseline saved" in out


def test_main_missing_input_file(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        main(["capture", "--baseline", str(tmp_path / "b.json"), "nonexistent.txt"])


def test_main_compare_missing_baseline(tmp_path: Path) -> None:
    input_file = tmp_path / "trace.txt"
    input_file.write_text(_SAMPLE_TB)
    with pytest.raises(SystemExit):
        main(["compare", "--baseline", str(tmp_path / "missing.json"), str(input_file)])


def test_main_compare_no_regressions(tmp_path: Path, capsys) -> None:
    input_file = tmp_path / "trace.txt"
    input_file.write_text(_SAMPLE_TB)
    baseline_file = tmp_path / "b.json"
    main(["capture", "--baseline", str(baseline_file), str(input_file)])
    capsys.readouterr()
    main(["compare", "--baseline", str(baseline_file), str(input_file)])
    out = capsys.readouterr().out
    assert "New (regressions) : 0" in out
    assert "Resolved          : 0" in out
