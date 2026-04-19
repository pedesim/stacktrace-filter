"""Tests for stacktrace_filter.pruner."""
from __future__ import annotations
from unittest.mock import patch

import pytest

from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.pruner import (
    PruneConfig, PruneResult, prune, format_prune_result,
)
from stacktrace_filter.pruner_cli import build_pruner_parser, main


def _frame(filename="app.py", lineno=10, function="fn") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, source_line="pass")


def _tb(*frames, exception="ValueError: oops") -> Traceback:
    return Traceback(frames=list(frames), exception=exception)


def test_prune_no_config_keeps_all():
    tb = _tb(_frame(), _frame(), _frame())
    result = prune(tb, PruneConfig())
    assert result.pruned_count == 3
    assert result.delta == 0


def test_prune_max_frames_keeps_tail():
    frames = [_frame(lineno=i) for i in range(5)]
    tb = _tb(*frames)
    result = prune(tb, PruneConfig(max_frames=3))
    assert result.pruned_count == 3
    assert result.traceback.frames[-1].lineno == 4


def test_prune_drop_filename_pattern():
    f1 = _frame(filename="/lib/site-packages/django/core.py")
    f2 = _frame(filename="app/views.py")
    f3 = _frame(filename="app/models.py")
    tb = _tb(f1, f2, f3)
    config = PruneConfig(drop_filenames=[r"site-packages"])
    result = prune(tb, config)
    assert result.pruned_count == 2
    assert all("site-packages" not in f.filename for f in result.traceback.frames)


def test_prune_drop_function_pattern():
    f1 = _frame(function="_internal_call")
    f2 = _frame(function="user_view")
    tb = _tb(f1, f2)
    config = PruneConfig(drop_functions=[r"^_"])
    result = prune(tb, config)
    assert result.pruned_count == 1
    assert result.traceback.frames[0].function == "user_view"


def test_prune_keep_last_protects_bottom_frames():
    f1 = _frame(filename="site-packages/x.py", lineno=1)
    f2 = _frame(filename="site-packages/y.py", lineno=2)
    f3 = _frame(filename="site-packages/z.py", lineno=3)
    tb = _tb(f1, f2, f3)
    config = PruneConfig(drop_filenames=[r"site-packages"], keep_last=2)
    result = prune(tb, config)
    # last 2 are protected even though they match the drop pattern
    assert result.pruned_count == 2
    assert result.traceback.frames[0].lineno == 2


def test_format_prune_result_no_delta():
    tb = _tb(_frame())
    result = PruneResult(traceback=tb, original_count=1, pruned_count=1)
    out = format_prune_result(result, color=False)
    assert "[pruner]" not in out


def test_format_prune_result_with_delta():
    tb = _tb(_frame())
    result = PruneResult(traceback=tb, original_count=3, pruned_count=1)
    out = format_prune_result(result, color=False)
    assert "removed 2 frame(s)" in out


def test_build_pruner_parser_defaults():
    p = build_pruner_parser()
    args = p.parse_args([])
    assert args.max_frames is None
    assert args.drop_filenames == []
    assert args.keep_last == 1
    assert not args.no_color


def test_main_missing_file(capsys):
    with pytest.raises(SystemExit):
        main(["nonexistent_file_xyz.txt"])


def test_main_reads_stdin(tmp_path, capsys):
    tb_text = (
        "Traceback (most recent call last):\n"
        '  File "app.py", line 5, in run\n'
        "    foo()\n"
        "RuntimeError: boom\n"
    )
    with patch("stacktrace_filter.pruner_cli.read_source", return_value=tb_text):
        main([])
    captured = capsys.readouterr()
    assert "app.py" in captured.out
