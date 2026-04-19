"""Tests for stacktrace_filter.comparator_cli."""
from __future__ import annotations
import textwrap
from unittest.mock import patch, MagicMock
import pytest
from stacktrace_filter.comparator_cli import build_comparator_parser, main


TB_TEXT = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app.py", line 10, in run
        do_thing()
    ValueError: something went wrong
""")


def test_build_comparator_parser_defaults():
    p = build_comparator_parser()
    args = p.parse_args(["a.txt", "b.txt"])
    assert args.left == "a.txt"
    assert args.right == "b.txt"
    assert args.no_color is False
    assert args.score_only is False


def test_build_comparator_parser_flags():
    p = build_comparator_parser()
    args = p.parse_args(["a.txt", "b.txt", "--no-color", "--score-only"])
    assert args.no_color is True
    assert args.score_only is True


def test_main_missing_left_file(tmp_path, capsys):
    right = tmp_path / "right.txt"
    right.write_text(TB_TEXT)
    with pytest.raises(SystemExit) as exc:
        main(["nonexistent.txt", str(right)])
    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_main_missing_right_file(tmp_path, capsys):
    left = tmp_path / "left.txt"
    left.write_text(TB_TEXT)
    with pytest.raises(SystemExit) as exc:
        main([str(left), "nonexistent.txt"])
    assert exc.value.code == 1


def test_main_identical_files(tmp_path, capsys):
    f = tmp_path / "tb.txt"
    f.write_text(TB_TEXT)
    main([str(f), str(f), "--no-color"])
    out = capsys.readouterr().out
    assert "frame similarity" in out
    assert "overall score" in out


def test_main_score_only(tmp_path, capsys):
    f = tmp_path / "tb.txt"
    f.write_text(TB_TEXT)
    main([str(f), str(f), "--score-only"])
    out = capsys.readouterr().out.strip()
    score = float(out)
    assert 0.0 <= score <= 1.0
