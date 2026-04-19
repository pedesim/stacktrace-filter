"""Tests for stacktrace_filter.router_cli."""
import json
import pytest
from unittest.mock import patch, mock_open
from stacktrace_filter.router_cli import build_router_parser, main


SAMPLE_TB = """Traceback (most recent call last):
  File \"app/views.py\", line 10, in view
    result = compute()
ValueError: bad input
"""

SAMPLE_RULES = {"rules": [{"destination": "value_errors", "exc_type": "ValueError"}]}


def test_build_router_parser_defaults():
    p = build_router_parser()
    args = p.parse_args(["rules.json"])
    assert args.default == "default"
    assert not args.summary
    assert args.input is None


def test_build_router_parser_flags():
    p = build_router_parser()
    args = p.parse_args(["rules.json", "tb.txt", "--default", "catch", "--summary"])
    assert args.default == "catch"
    assert args.summary
    assert args.input == "tb.txt"


def test_main_missing_rules_file(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        main([str(tmp_path / "no_rules.json")])
    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_main_missing_input_file(tmp_path, capsys):
    rules = tmp_path / "rules.json"
    rules.write_text(json.dumps(SAMPLE_RULES))
    with pytest.raises(SystemExit) as exc:
        main([str(rules), str(tmp_path / "missing.txt")])
    assert exc.value.code == 1


def test_main_reads_stdin(tmp_path, capsys):
    rules = tmp_path / "rules.json"
    rules.write_text(json.dumps(SAMPLE_RULES))
    with patch("sys.stdin.read", return_value=SAMPLE_TB):
        main([str(rules)])
    captured = capsys.readouterr()
    assert "value_errors" in captured.out or "ValueError" in captured.out


def test_main_summary_flag(tmp_path, capsys):
    rules = tmp_path / "rules.json"
    rules.write_text(json.dumps(SAMPLE_RULES))
    tb_file = tmp_path / "tb.txt"
    tb_file.write_text(SAMPLE_TB)
    main([str(rules), str(tb_file), "--summary"])
    captured = capsys.readouterr()
    assert "traceback" in captured.out
