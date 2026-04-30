"""Tests for stacktrace_filter.correlator_cli."""
from __future__ import annotations

import json
import os
import tempfile
from io import StringIO
from unittest import mock

import pytest

from stacktrace_filter.correlator_cli import build_correlator_parser, main


_TRACEBACK_A = """Traceback (most recent call last):
  File \"app.py\", line 10, in run
    do_thing()
  File \"lib.py\", line 5, in do_thing
    raise ValueError('bad')
ValueError: bad
"""

_TRACEBACK_B = """Traceback (most recent call last):
  File \"lib.py\", line 5, in do_thing
    raise ValueError('bad')
ValueError: bad
"""


def test_build_correlator_parser_defaults():
    p = build_correlator_parser()
    args = p.parse_args([])
    assert args.min_shared == 1
    assert args.no_color is False
    assert args.clusters_only is False
    assert args.files == []


def test_build_correlator_parser_flags():
    p = build_correlator_parser()
    args = p.parse_args(["--min-shared", "3", "--no-color", "--clusters-only"])
    assert args.min_shared == 3
    assert args.no_color is True
    assert args.clusters_only is True


def test_main_missing_file(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["nonexistent_file_xyz.txt"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_main_reads_stdin(capsys):
    with mock.patch("sys.stdin", StringIO(_TRACEBACK_A)):
        main([])
    captured = capsys.readouterr()
    assert "traceback" in captured.out.lower()


def test_main_reads_file(tmp_path, capsys):
    f = tmp_path / "tb.txt"
    f.write_text(_TRACEBACK_A)
    main([str(f)])
    captured = capsys.readouterr()
    assert "1 traceback" in captured.out


def test_main_two_files_shared_frame(tmp_path, capsys):
    fa = tmp_path / "a.txt"
    fb = tmp_path / "b.txt"
    fa.write_text(_TRACEBACK_A)
    fb.write_text(_TRACEBACK_B)
    main([str(fa), str(fb)])
    captured = capsys.readouterr()
    # Both tracebacks share lib.py:do_thing:5 → at least 1 edge
    assert "edge" in captured.out


def test_main_clusters_only_flag(tmp_path, capsys):
    fa = tmp_path / "a.txt"
    fb = tmp_path / "b.txt"
    fa.write_text(_TRACEBACK_A)
    fb.write_text(_TRACEBACK_B)
    main(["--clusters-only", str(fa), str(fb)])
    captured = capsys.readouterr()
    # Edge detail lines contain '<->' which should be absent in clusters-only
    assert "<->" not in captured.out
