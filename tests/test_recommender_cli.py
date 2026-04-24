"""Tests for stacktrace_filter.recommender_cli."""
from __future__ import annotations

import textwrap
from unittest.mock import patch

import pytest

from stacktrace_filter.recommender_cli import build_recommender_parser, main


_SAMPLE_TB = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app.py", line 5, in run
        result = data[key]
    KeyError: 'missing'
""")


def test_build_recommender_parser_defaults():
    p = build_recommender_parser()
    args = p.parse_args([])
    assert args.file == "-"
    assert args.no_color is False
    assert args.advice_only is False


def test_build_recommender_parser_no_color():
    p = build_recommender_parser()
    args = p.parse_args(["--no-color"])
    assert args.no_color is True


def test_build_recommender_parser_advice_only():
    p = build_recommender_parser()
    args = p.parse_args(["--advice-only"])
    assert args.advice_only is True


def test_main_missing_file(tmp_path, capsys):
    missing = str(tmp_path / "nope.txt")
    rc = main([missing])
    assert rc == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_main_reads_stdin(tmp_path, monkeypatch):
    import io
    monkeypatch.setattr("sys.stdin", io.StringIO(_SAMPLE_TB))
    rc = main(["-", "--no-color"])
    assert rc == 0


def test_main_reads_file(tmp_path, capsys):
    f = tmp_path / "tb.txt"
    f.write_text(_SAMPLE_TB)
    rc = main([str(f), "--no-color"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "KeyError" in captured.out


def test_main_advice_only(tmp_path, capsys):
    f = tmp_path / "tb.txt"
    f.write_text(_SAMPLE_TB)
    rc = main([str(f), "--advice-only"])
    assert rc == 0
    captured = capsys.readouterr()
    lines = [l for l in captured.out.splitlines() if l.strip()]
    assert len(lines) == 1


def test_main_output_contains_advice(tmp_path, capsys):
    f = tmp_path / "tb.txt"
    f.write_text(_SAMPLE_TB)
    rc = main([str(f), "--no-color"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "Advice:" in captured.out
