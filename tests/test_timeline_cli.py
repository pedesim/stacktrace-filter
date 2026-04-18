"""Tests for stacktrace_filter.timeline_cli."""
from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from stacktrace_filter.timeline_cli import build_timeline_parser, main

_TRACEBACK_TEXT = (
    "Traceback (most recent call last):\n"
    '  File "app.py", line 5, in run\n'
    "    do_thing()\n"
    "RuntimeError: oops\n"
)

_MANIFEST = json.dumps([
    {"text": _TRACEBACK_TEXT, "timestamp": "2024-06-01T12:00:00", "label": "job-1"},
    {"text": _TRACEBACK_TEXT, "timestamp": "2024-06-01T11:00:00"},
])


def test_build_timeline_parser_defaults():
    p = build_timeline_parser()
    args = p.parse_args([])
    assert args.manifest == "-"
    assert not args.no_color


def test_build_timeline_parser_no_color():
    p = build_timeline_parser()
    args = p.parse_args(["--no-color"])
    assert args.no_color


def test_main_reads_stdin(capsys):
    with patch("sys.stdin.read", return_value=_MANIFEST):
        main([])
    out = capsys.readouterr().out
    assert "RuntimeError" in out


def test_main_reads_file(tmp_path, capsys):
    f = tmp_path / "manifest.json"
    f.write_text(_MANIFEST)
    main([str(f)])
    out = capsys.readouterr().out
    assert "2024-06-01" in out


def test_main_missing_file(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["nonexistent_manifest.json"])
    assert exc_info.value.code == 1


def test_main_invalid_json(capsys):
    with patch("sys.stdin.read", return_value="not json"):
        with pytest.raises(SystemExit) as exc_info:
            main([])
    assert exc_info.value.code == 1


def test_main_sorted_output(tmp_path, capsys):
    f = tmp_path / "m.json"
    f.write_text(_MANIFEST)
    main([str(f), "--no-color"])
    out = capsys.readouterr().out
    lines = [l for l in out.splitlines() if l.strip()]
    # earlier timestamp should appear first
    assert lines[0].startswith("2024-06-01 11:00:00")
