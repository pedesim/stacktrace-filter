"""Tests for stacktrace_filter.retrier_cli."""
from __future__ import annotations

import json
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from stacktrace_filter.retrier_cli import build_retrier_parser, main

_TRACEBACK = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app/client.py", line 42, in fetch
        resp = session.get(url, timeout=5)
    ConnectionError: HTTPSConnectionPool: Max retries exceeded
""")

_FATAL_TRACEBACK = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app/main.py", line 5, in run
        sys.exit(2)
    SystemExit: 2
""")


def test_build_retrier_parser_defaults():
    p = build_retrier_parser()
    args = p.parse_args([])
    assert args.file == "-"
    assert args.extra_retryable == []
    assert args.extra_fatal == []
    assert args.default_delay_s == 1.0
    assert args.json is False


def test_build_retrier_parser_flags():
    p = build_retrier_parser()
    args = p.parse_args([
        "--retryable", "MyError",
        "--fatal", "CriticalError",
        "--delay", "3.5",
        "--json",
    ])
    assert "MyError" in args.extra_retryable
    assert "CriticalError" in args.extra_fatal
    assert args.default_delay_s == pytest.approx(3.5)
    assert args.json is True


def test_main_missing_file(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["no_such_file_xyz.txt"])
    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_main_reads_stdin(tmp_path, capsys):
    with patch("stacktrace_filter.retrier_cli.read_source", return_value=_TRACEBACK):
        main(["-"])
    out = capsys.readouterr().out
    assert "ConnectionError" in out
    assert "RETRYABLE" in out


def test_main_reads_file(tmp_path, capsys):
    tb_file = tmp_path / "tb.txt"
    tb_file.write_text(_TRACEBACK)
    main([str(tb_file)])
    out = capsys.readouterr().out
    assert "RETRYABLE" in out


def test_main_json_output(tmp_path, capsys):
    tb_file = tmp_path / "tb.txt"
    tb_file.write_text(_TRACEBACK)
    main([str(tb_file), "--json"])
    data = json.loads(capsys.readouterr().out)
    assert data["retryable"] is True
    assert data["exc_type"] == "ConnectionError"
    assert "reason" in data


def test_main_fatal_traceback(tmp_path, capsys):
    tb_file = tmp_path / "tb.txt"
    tb_file.write_text(_FATAL_TRACEBACK)
    main([str(tb_file), "--json"])
    data = json.loads(capsys.readouterr().out)
    assert data["fatal"] is True
    assert data["retryable"] is False
