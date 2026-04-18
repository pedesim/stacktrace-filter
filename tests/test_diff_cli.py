import textwrap
import pytest
from unittest.mock import patch, mock_open
from stacktrace_filter.diff_cli import build_diff_parser, main

TB_A = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app.py", line 10, in run
        do_thing()
    ValueError: bad value
""")

TB_B = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app.py", line 10, in run
        do_other()
    ValueError: bad value
""")


def test_build_diff_parser_defaults():
    p = build_diff_parser()
    args = p.parse_args(["left.txt", "right.txt"])
    assert args.left == "left.txt"
    assert args.right == "right.txt"
    assert not args.no_color


def test_build_diff_parser_no_color():
    p = build_diff_parser()
    args = p.parse_args(["--no-color", "l.txt", "r.txt"])
    assert args.no_color


def test_main_missing_file(tmp_path):
    result = main([str(tmp_path / "nope.txt"), str(tmp_path / "also.txt")])
    assert result == 1


def test_main_identical_files(tmp_path):
    f = tmp_path / "tb.txt"
    f.write_text(TB_A)
    result = main(["--no-color", str(f), str(f)])
    assert result == 0


def test_main_diff_files(tmp_path, capsys):
    fa = tmp_path / "a.txt"
    fb = tmp_path / "b.txt"
    fa.write_text(TB_A)
    fb.write_text(TB_B)
    result = main(["--no-color", str(fa), str(fb)])
    assert result == 0
    captured = capsys.readouterr()
    assert "app.py" in captured.out
