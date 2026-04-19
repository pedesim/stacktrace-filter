"""Tests for stacktrace_filter.splitter_cli."""
import json
import textwrap
from pathlib import Path
import pytest
from stacktrace_filter.splitter_cli import build_splitter_parser, main


SAMPLE_TB = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app.py", line 10, in run
        do_thing()
    ValueError: something went wrong
""")


def test_build_splitter_parser_defaults():
    p = build_splitter_parser()
    args = p.parse_args(["--rules", "r.json"])
    assert args.input == "-"
    assert args.rules == "r.json"
    assert args.json is False


def test_build_splitter_parser_json_flag():
    p = build_splitter_parser()
    args = p.parse_args(["--rules", "r.json", "--json"])
    assert args.json is True


def test_main_missing_rules_file(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--rules", str(tmp_path / "missing.json")])
    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "rules file not found" in captured.err


def test_main_reads_stdin(tmp_path, monkeypatch, capsys):
    rules_file = tmp_path / "rules.json"
    rules_file.write_text(json.dumps([{"name": "ve", "exc_type": "ValueError"}]))
    import io
    monkeypatch.setattr("sys.stdin", io.StringIO(SAMPLE_TB))
    main(["--rules", str(rules_file)])
    out = capsys.readouterr().out
    assert "ve" in out


def test_main_json_output(tmp_path, monkeypatch, capsys):
    rules_file = tmp_path / "rules.json"
    rules_file.write_text(json.dumps([{"name": "ve", "exc_type": "ValueError"}]))
    tb_file = tmp_path / "tb.txt"
    tb_file.write_text(SAMPLE_TB)
    main(["--rules", str(rules_file), "--json", str(tb_file)])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "ve" in data
    assert data["ve"] == 1
