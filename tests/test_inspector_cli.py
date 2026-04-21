"""Tests for stacktrace_filter.inspector_cli."""
from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from stacktrace_filter.inspector_cli import build_inspector_parser, main


SAMPLE_TB = """Traceback (most recent call last):
  File "/home/user/app.py", line 10, in run
    result = compute()
  File "/home/user/utils.py", line 5, in compute
    return 1 / 0
ZeroDivisionError: division by zero
"""


def test_build_inspector_parser_defaults():
    parser = build_inspector_parser()
    args = parser.parse_args([])
    assert args.file == "-"
    assert args.no_color is False
    assert args.json is False


def test_build_inspector_parser_flags():
    parser = build_inspector_parser()
    args = parser.parse_args(["myfile.txt", "--no-color", "--json"])
    assert args.file == "myfile.txt"
    assert args.no_color is True
    assert args.json is True


def test_main_reads_stdin(capsys):
    with patch("stacktrace_filter.inspector_cli.read_source", return_value=SAMPLE_TB):
        main(["-"])
    out = capsys.readouterr().out
    assert "ZeroDivisionError" in out


def test_main_reads_file(capsys, tmp_path):
    p = tmp_path / "tb.txt"
    p.write_text(SAMPLE_TB)
    main([str(p), "--no-color"])
    out = capsys.readouterr().out
    assert "ZeroDivisionError" in out
    assert "\033[" not in out


def test_main_missing_file():
    with pytest.raises(SystemExit) as exc_info:
        main(["nonexistent_file_xyz.txt"])
    assert exc_info.value.code == 1


def test_main_json_output(capsys):
    with patch("stacktrace_filter.inspector_cli.read_source", return_value=SAMPLE_TB):
        main(["--json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["exc_type"] == "ZeroDivisionError"
    assert "total_frames" in data
    assert "user_ratio" in data
    assert isinstance(data["unique_files"], list)


def test_main_json_deepest_user_frame(capsys):
    with patch("stacktrace_filter.inspector_cli.read_source", return_value=SAMPLE_TB):
        main(["--json"])
    data = json.loads(capsys.readouterr().out)
    deepest = data["deepest_user_frame"]
    assert deepest is not None
    assert "filename" in deepest
    assert "lineno" in deepest
    assert "function" in deepest
