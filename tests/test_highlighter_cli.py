"""Tests for stacktrace_filter.highlighter_cli."""
from __future__ import annotations

import re
import textwrap
from unittest.mock import patch

import pytest

from stacktrace_filter.highlighter_cli import build_highlighter_parser, main


def strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


TRACEBACK = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app.py", line 10, in run
        result = compute(x)
    ValueError: invalid literal
""").strip()


def test_build_highlighter_parser_defaults():
    p = build_highlighter_parser()
    args = p.parse_args([])
    assert args.file is None
    assert args.no_color is False
    assert args.exception_only is False


def test_build_highlighter_parser_no_color():
    p = build_highlighter_parser()
    args = p.parse_args(["--no-color"])
    assert args.no_color is True


def test_build_highlighter_parser_exception_only():
    p = build_highlighter_parser()
    args = p.parse_args(["--exception-only"])
    assert args.exception_only is True


def test_main_reads_stdin(capsys):
    with patch("sys.stdin") as mock_stdin:
        mock_stdin.read.return_value = TRACEBACK
        main(["--no-color"])
    out = capsys.readouterr().out
    assert "ValueError" in out
    assert "app.py" in out


def test_main_reads_file(tmp_path, capsys):
    tb_file = tmp_path / "tb.txt"
    tb_file.write_text(TRACEBACK)
    main([str(tb_file), "--no-color"])
    out = capsys.readouterr().out
    assert "ValueError" in out
    assert "app.py" in out


def test_main_missing_file(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["nonexistent_file.txt"])
    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "not found" in err


def test_main_no_color_produces_plain_output(capsys):
    with patch("sys.stdin") as mock_stdin:
        mock_stdin.read.return_value = TRACEBACK
        main(["--no-color"])
    out = capsys.readouterr().out
    assert "\x1b[" not in out


def test_main_exception_only_flag(capsys):
    with patch("sys.stdin") as mock_stdin:
        mock_stdin.read.return_value = TRACEBACK
        main(["--exception-only", "--no-color"])
    out = capsys.readouterr().out
    # File lines should pass through unchanged (no highlight markup side-effects)
    assert "File \"app.py\"" in out
    assert "ValueError" in out
