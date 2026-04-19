"""Tests for stacktrace_filter.merger and merger_cli."""
from __future__ import annotations
import pytest
from unittest.mock import patch
from stacktrace_filter.parser import Traceback, Frame
from stacktrace_filter.merger import merge, format_merge_result, MergeResult


def _frame(filename: str = "app.py", lineno: int = 1, name: str = "fn") -> Frame:
    return Frame(filename=filename, lineno=lineno, name=name, source_line="pass")


def _tb(exc: str = "ValueError", frames=None) -> Traceback:
    return Traceback(frames=frames or [_frame()], exception=exc)


def test_merge_empty_groups():
    result = merge([])
    assert result.kept == 0
    assert result.dropped == 0
    assert result.total_input == 0


def test_merge_single_group_no_dedup():
    tbs = [_tb("ValueError"), _tb("TypeError", [_frame("other.py")])]
    result = merge([tbs], dedup=False)
    assert result.total_input == 2
    assert result.kept == 2
    assert result.dropped == 0


def test_merge_dedup_removes_identical():
    tb = _tb("ValueError")
    result = merge([[tb, tb, tb]], dedup=True)
    assert result.kept == 1
    assert result.dropped == 2
    assert result.total_input == 3


def test_merge_across_groups_dedup():
    tb = _tb("ValueError")
    result = merge([[tb], [tb]], dedup=True)
    assert result.kept == 1
    assert result.dropped == 1


def test_merge_no_dedup_keeps_all_duplicates():
    tb = _tb("ValueError")
    result = merge([[tb], [tb]], dedup=False)
    assert result.kept == 2
    assert result.dropped == 0


def test_merge_sort_by_depth():
    shallow = _tb("A", [_frame()])
    deep = _tb("B", [_frame(), _frame("b.py"), _frame("c.py")])
    result = merge([[shallow, deep]], dedup=False, sort_by="depth", ascending=False)
    assert result.tracebacks[0].exception == "B"


def test_format_merge_result_contains_summary():
    result = MergeResult(tracebacks=[_tb("ValueError")], dropped=2, total_input=3)
    text = format_merge_result(result)
    assert "3" in text
    assert "1 unique" in text
    assert "2 duplicates" in text
    assert "ValueError" in text


def test_merger_cli_missing_file(capsys):
    from stacktrace_filter.merger_cli import main
    with pytest.raises(SystemExit):
        main(["nonexistent_file.txt"])
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_merger_cli_json_output(tmp_path, capsys):
    import json
    tb_text = "Traceback (most recent call last):\n  File \"app.py\", line 1, in fn\n    pass\nValueError: oops\n"
    f = tmp_path / "tb.txt"
    f.write_text(tb_text)
    from stacktrace_filter.merger_cli import main
    main([str(f), "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "kept" in data
    assert "dropped" in data
