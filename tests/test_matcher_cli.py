"""Tests for stacktrace_filter.matcher_cli."""
import json
import pytest
from unittest.mock import patch, mock_open
from stacktrace_filter.matcher_cli import build_matcher_parser, main


SAMPLE_TB = """Traceback (most recent call last):
  File \"app/main.py\", line 5, in run
    do()
ValueError: bad input
"""

SAMPLE_RULES = json.dumps([
    {"name": "val_rule", "exc_type_pattern": "ValueError"}
])


def test_build_matcher_parser_defaults():
    p = build_matcher_parser()
    args = p.parse_args(["--rules", "rules.json"])
    assert args.file is None
    assert args.rules == "rules.json"
    assert not args.only_matched


def test_build_matcher_parser_only_matched():
    p = build_matcher_parser()
    args = p.parse_args(["--rules", "r.json", "--only-matched"])
    assert args.only_matched


def test_main_missing_rules_file(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--rules", "nonexistent_rules.json"])
    assert exc.value.code == 1


def test_main_missing_input_file(tmp_path, capsys):
    rules_file = tmp_path / "rules.json"
    rules_file.write_text(SAMPLE_RULES)
    with pytest.raises(SystemExit) as exc:
        main(["--rules", str(rules_file), "no_such_file.txt"])
    assert exc.value.code == 1


def test_main_matched(tmp_path, capsys):
    rules_file = tmp_path / "rules.json"
    rules_file.write_text(SAMPLE_RULES)
    tb_file = tmp_path / "tb.txt"
    tb_file.write_text(SAMPLE_TB)
    main(["--rules", str(rules_file), str(tb_file)])
    out = capsys.readouterr().out
    assert "val_rule" in out


def test_main_no_match_prints_message(tmp_path, capsys):
    rules = json.dumps([{"name": "key_rule", "exc_type_pattern": "KeyError"}])
    rules_file = tmp_path / "rules.json"
    rules_file.write_text(rules)
    tb_file = tmp_path / "tb.txt"
    tb_file.write_text(SAMPLE_TB)
    main(["--rules", str(rules_file), str(tb_file)])
    out = capsys.readouterr().out
    assert "No rules matched" in out


def test_main_only_matched_suppresses_output(tmp_path, capsys):
    rules = json.dumps([{"name": "key_rule", "exc_type_pattern": "KeyError"}])
    rules_file = tmp_path / "rules.json"
    rules_file.write_text(rules)
    tb_file = tmp_path / "tb.txt"
    tb_file.write_text(SAMPLE_TB)
    main(["--rules", str(rules_file), str(tb_file), "--only-matched"])
    out = capsys.readouterr().out
    assert out == ""
