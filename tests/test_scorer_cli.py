"""Tests for stacktrace_filter.scorer_cli."""
import json
import textwrap
from unittest.mock import patch
import pytest
from stacktrace_filter.scorer_cli import build_scorer_parser, main


SAMPLE_TB = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app/main.py", line 5, in run
        do_thing()
      File "app/utils.py", line 12, in do_thing
        raise ValueError("oops")
    ValueError: oops
""")


def test_build_scorer_parser_defaults():
    p = build_scorer_parser()
    args = p.parse_args([])
    assert args.weight_user == 0.5
    assert args.weight_depth == 0.3
    assert args.weight_exc == 0.2
    assert args.top == 0
    assert not args.no_color


def test_build_scorer_parser_flags():
    p = build_scorer_parser()
    args = p.parse_args(["--no-color", "--top", "3", "--weight-user", "0.8"])
    assert args.no_color
    assert args.top == 3
    assert args.weight_user == pytest.approx(0.8)


def test_main_missing_file(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["nonexistent_file_xyz.txt"])
    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_main_reads_stdin(capsys):
    with patch("sys.stdin") as mock_stdin:
        mock_stdin.read.return_value = SAMPLE_TB
        main(["--no-color"])
    captured = capsys.readouterr()
    assert "score=" in captured.out


def test_main_reads_file(tmp_path, capsys):
    f = tmp_path / "tb.txt"
    f.write_text(SAMPLE_TB)
    main(["--no-color", str(f)])
    captured = capsys.readouterr()
    assert "score=" in captured.out


def test_main_top_limits_output(capsys):
    with patch("sys.stdin") as mock_stdin:
        mock_stdin.read.return_value = SAMPLE_TB
        main(["--no-color", "--top", "1"])
    captured = capsys.readouterr()
    lines = [l for l in captured.out.splitlines() if "score=" in l]
    assert len(lines) <= 1
