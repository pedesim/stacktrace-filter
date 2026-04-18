"""Tests for stacktrace_filter.grouper_cli."""
import textwrap
from unittest.mock import patch, MagicMock
import pytest
from stacktrace_filter.grouper_cli import build_grouper_parser, main


TRACEBACK_TEXT = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app.py", line 5, in run
        foo()
    ValueError: bad value
""")


def test_build_grouper_parser_defaults():
    p = build_grouper_parser()
    args = p.parse_args([])
    assert args.file == "-"
    assert args.no_color is False
    assert args.min_count == 1


def test_build_grouper_parser_flags():
    p = build_grouper_parser()
    args = p.parse_args(["--no-color", "--min-count", "3", "trace.log"])
    assert args.no_color is True
    assert args.min_count == 3
    assert args.file == "trace.log"


def test_main_missing_file(capsys):
    rc = main(["nonexistent_file_xyz.log"])
    assert rc == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_main_reads_stdin(capsys):
    double = TRACEBACK_TEXT + "\n" + TRACEBACK_TEXT
    with patch("stacktrace_filter.grouper_cli.read_source", return_value=double):
        rc = main(["-"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "ValueError" in out


def test_main_min_count_filters(capsys):
    # Two identical + one different
    single = textwrap.dedent("""\
        Traceback (most recent call last):
          File "app.py", line 1, in f
            pass()
        TypeError: bad type
    """)
    text = TRACEBACK_TEXT + "\n" + TRACEBACK_TEXT + "\n" + single
    with patch("stacktrace_filter.grouper_cli.read_source", return_value=text):
        rc = main(["--min-count", "2", "-"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "ValueError" in out
    assert "TypeError" not in out
