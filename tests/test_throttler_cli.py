"""Tests for stacktrace_filter.throttler_cli."""
import json
from unittest.mock import patch, MagicMock
import pytest
from stacktrace_filter.throttler_cli import build_throttler_parser, main


SIMPLE_TB = """Traceback (most recent call last):
  File "app.py", line 10, in run
    do_thing()
ValueError: bad input
"""


def test_build_throttler_parser_defaults():
    p = build_throttler_parser()
    args = p.parse_args([])
    assert args.max == 10
    assert args.window == 60.0
    assert args.format == "plain"
    assert args.no_color is False


def test_build_throttler_parser_flags():
    p = build_throttler_parser()
    args = p.parse_args(["--max", "5", "--window", "30", "--format", "json", "--no-color"])
    assert args.max == 5
    assert args.window == 30.0
    assert args.format == "json"
    assert args.no_color is True


def test_main_missing_file(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["nonexistent_file_xyz.txt"])
    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "error" in captured.err


def test_main_reads_stdin(capsys):
    with patch("stacktrace_filter.throttler_cli.read_source", return_value=SIMPLE_TB):
        main([])
    captured = capsys.readouterr()
    assert "ValueError" in captured.out


def test_main_max_one_keeps_single(capsys):
    repeated = SIMPLE_TB * 3
    with patch("stacktrace_filter.throttler_cli.read_source", return_value=repeated):
        main(["--max", "1"])
    captured = capsys.readouterr()
    assert captured.out.count("ValueError") == 1
