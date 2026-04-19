"""Tests for stacktrace_filter.patcher."""
import pytest

from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.patcher import (
    PatchRule,
    PatcherConfig,
    PatchResult,
    patch,
    format_patch_result,
)


def _frame(filename="/app/src/foo.py", lineno=10, name="bar", line="x = 1"):
    return Frame(filename=filename, lineno=lineno, name=name, line=line)


def _tb(frames=None, exception="ValueError: oops"):
    return Traceback(frames=frames or [_frame()], exception=exception)


def test_patch_no_rules_unchanged():
    tb = _tb()
    config = PatcherConfig(rules=[])
    result = patch(tb, config)
    assert result.patched_count == 0
    assert result.traceback.frames[0].filename == "/app/src/foo.py"


def test_patch_single_rule_matches():
    tb = _tb()
    config = PatcherConfig(rules=[PatchRule(prefix="/app/src", replacement="/home/user/project")])
    result = patch(tb, config)
    assert result.patched_count == 1
    assert result.traceback.frames[0].filename == "/home/user/project/foo.py"


def test_patch_rule_no_match():
    tb = _tb(frames=[_frame(filename="/other/path.py")])
    config = PatcherConfig(rules=[PatchRule(prefix="/app", replacement="/x")])
    result = patch(tb, config)
    assert result.patched_count == 0
    assert result.traceback.frames[0].filename == "/other/path.py"


def test_patch_multiple_frames_partial_match():
    frames = [
        _frame(filename="/app/a.py"),
        _frame(filename="/lib/b.py"),
        _frame(filename="/app/c.py"),
    ]
    tb = _tb(frames=frames)
    config = PatcherConfig(rules=[PatchRule(prefix="/app", replacement="/src")])
    result = patch(tb, config)
    assert result.patched_count == 2
    assert result.traceback.frames[0].filename == "/src/a.py"
    assert result.traceback.frames[1].filename == "/lib/b.py"
    assert result.traceback.frames[2].filename == "/src/c.py"


def test_patch_first_matching_rule_wins():
    tb = _tb(frames=[_frame(filename="/app/foo.py")])
    config = PatcherConfig(rules=[
        PatchRule(prefix="/app", replacement="/first"),
        PatchRule(prefix="/app", replacement="/second"),
    ])
    result = patch(tb, config)
    assert result.traceback.frames[0].filename == "/first/foo.py"


def test_patch_preserves_exception():
    tb = _tb(exception="RuntimeError: boom")
    config = PatcherConfig()
    result = patch(tb, config)
    assert result.traceback.exception == "RuntimeError: boom"


def test_patch_result_is_new_traceback():
    tb = _tb()
    config = PatcherConfig(rules=[PatchRule("/app/src", "/x")])
    result = patch(tb, config)
    assert result.traceback is not tb


def test_format_patch_result_contains_count():
    tb = _tb()
    config = PatcherConfig(rules=[PatchRule("/app/src", "/x")])
    result = patch(tb, config)
    text = format_patch_result(result)
    assert "Patched 1 frame" in text
    assert "/x/foo.py" in text
