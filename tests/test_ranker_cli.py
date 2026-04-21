"""Tests for stacktrace_filter.ranker_cli."""
from __future__ import annotations

import textwrap
from unittest.mock import patch

import pytest

from stacktrace_filter.ranker_cli import build_ranker_parser, main

_SAMPLE_TB = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app.py", line 10, in run
        do_thing()
      File "app.py", line 20, in do_thing
        raise ValueError("oops")
    ValueError: oops
""")


def test_build_ranker_parser_defaults():
    p = build_ranker_parser()
    args = p.parse_args([])
    assert args.file == "-"
    assert args.ascending is False
    assert args.top == 0
    assert args.scores_only is False


def test_build_ranker_parser_flags():
    p = build_ranker_parser()
    args = p.parse_args(["--ascending", "--top", "3", "--scores-only", "input.txt"])
    assert args.ascending is True
    assert args.top == 3
    assert args.scores_only is True
    assert args.file == "input.txt"


def test_main_missing_file(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["nonexistent_file_xyz.txt"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_main_reads_stdin(capsys):
    with patch("stacktrace_filter.ranker_cli.read_source", return_value=_SAMPLE_TB):
        main(["-"])
    captured = capsys.readouterr()
    assert "score=" in captured.out


def test_main_scores_only(capsys):
    with patch("stacktrace_filter.ranker_cli.read_source", return_value=_SAMPLE_TB):
        main(["--scores-only", "-"])
    captured = capsys.readouterr()
    lines = [l for l in captured.out.strip().splitlines() if l]
    assert len(lines) == 1
    float(lines[0])  # should be a valid float


def test_main_top_limits_output(capsys):
    with patch("stacktrace_filter.ranker_cli.read_source", return_value=_SAMPLE_TB):
        main(["--top", "1", "-"])
    captured = capsys.readouterr()
    assert "score=" in captured.out
