"""Tests for stacktrace_filter.suppressor_cli."""
from __future__ import annotations

import json
import textwrap
from unittest.mock import patch

import pytest

from stacktrace_filter.suppressor_cli import build_suppressor_parser, main


_TRACEBACK_TEXT = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app.py", line 10, in run
        do_thing()
    ValueError: bad value
""").strip()


def _write_rules(tmp_path, rules):
    p = tmp_path / "rules.json"
    p.write_text(json.dumps(rules), encoding="utf-8")
    return str(p)


def test_build_suppressor_parser_defaults():
    p = build_suppressor_parser()
    args = p.parse_args(["--rules", "r.json"])
    assert args.input == "-"
    assert args.summary is False


def test_build_suppressor_parser_flags():
    p = build_suppressor_parser()
    args = p.parse_args(["--rules", "r.json", "--summary", "input.txt"])
    assert args.summary is True
    assert args.input == "input.txt"


def test_main_missing_rules_file(tmp_path):
    with pytest.raises(SystemExit):
        main(["--rules", str(tmp_path / "no_rules.json")])


def test_main_missing_input_file(tmp_path):
    rules_file = _write_rules(tmp_path, [])
    with pytest.raises(SystemExit):
        main(["--rules", rules_file, str(tmp_path / "no_input.txt")])


def test_main_reads_stdin_no_suppression(tmp_path, capsys):
    rules_file = _write_rules(tmp_path, [])
    with patch("sys.stdin.read", return_value=_TRACEBACK_TEXT):
        main(["--rules", rules_file])
    out = capsys.readouterr().out
    assert "ValueError" in out


def test_main_summary_flag(tmp_path, capsys):
    rules_file = _write_rules(
        tmp_path, [{"exc_type": "ValueError", "reason": "known-noise"}]
    )
    with patch("sys.stdin.read", return_value=_TRACEBACK_TEXT):
        main(["--rules", rules_file, "--summary"])
    out = capsys.readouterr().out
    assert "Dropped" in out
    assert "known-noise" in out
