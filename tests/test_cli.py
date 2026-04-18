"""Tests for the CLI entry point."""

from __future__ import annotations

import io
import textwrap
from unittest import mock

import pytest

from stacktrace_filter.cli import main, build_parser


SAMPLE_TB = textwrap.dedent("""\
    Traceback (most recent call last):
      File "/home/user/project/app.py", line 10, in run
        result = compute()
      File "/usr/lib/python3.11/functools.py", line 75, in wrapper
        return func(*args, **kwargs)
      File "/home/user/project/app.py", line 20, in compute
        raise ValueError("bad input")
    ValueError: bad input
""")


def test_build_parser_defaults():
    args = build_parser().parse_args([])
    assert args.no_color is False
    assert args.show_stdlib is False
    assert args.show_site_packages is False
    assert args.file is None


def test_main_reads_stdin(tmp_path):
    with mock.patch("sys.stdin", io.StringIO(SAMPLE_TB)):
        rc = main([])
    assert rc == 0


def test_main_reads_file(tmp_path):
    tb_file = tmp_path / "tb.txt"
    tb_file.write_text(SAMPLE_TB)
    rc = main([str(tb_file)])
    assert rc == 0


def test_main_missing_file():
    rc = main(["/nonexistent/path/tb.txt"])
    assert rc == 1


def test_main_no_color_flag(tmp_path, capsys):
    tb_file = tmp_path / "tb.txt"
    tb_file.write_text(SAMPLE_TB)
    main(["--no-color", str(tb_file)])
    captured = capsys.readouterr()
    assert "\x1b[" not in captured.out


def test_main_non_traceback_passthrough(tmp_path, capsys):
    plain = tmp_path / "plain.txt"
    plain.write_text("hello world\n")
    rc = main([str(plain)])
    assert rc == 0
    assert "hello world" in capsys.readouterr().out
