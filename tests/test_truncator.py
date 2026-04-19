"""Tests for stacktrace_filter.truncator."""
import pytest
from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.truncator import (
    TruncateConfig,
    TruncatedTraceback,
    truncate,
    format_truncated,
)


def _frame(name: str, lineno: int = 1, filename: str = "app.py") -> Frame:
    return Frame(filename=filename, lineno=lineno, name=name, line=f"pass  # {name}")


def _tb(n: int) -> Traceback:
    return Traceback(
        frames=[_frame(f"fn{i}", lineno=i + 1) for i in range(n)],
        exception_line="ValueError: oops",
    )


def test_no_truncation_when_under_limit():
    tb = _tb(5)
    result = truncate(tb, TruncateConfig(max_frames=10))
    assert result.omitted == 0
    assert len(result.frames) == 5
    assert not result.was_truncated


def test_truncation_omitted_count():
    tb = _tb(20)
    cfg = TruncateConfig(max_frames=10, keep_top=3, keep_bottom=7)
    result = truncate(tb, cfg)
    assert result.omitted == 10
    assert len(result.frames) == 10
    assert result.was_truncated


def test_truncation_keeps_top_frames():
    tb = _tb(20)
    cfg = TruncateConfig(max_frames=10, keep_top=3, keep_bottom=7)
    result = truncate(tb, cfg)
    assert result.frames[0].name == "fn0"
    assert result.frames[1].name == "fn1"
    assert result.frames[2].name == "fn2"


def test_truncation_keeps_bottom_frames():
    tb = _tb(20)
    cfg = TruncateConfig(max_frames=10, keep_top=3, keep_bottom=7)
    result = truncate(tb, cfg)
    assert result.frames[-1].name == "fn19"
    assert result.frames[-7].name == "fn13"


def test_exact_limit_no_truncation():
    tb = _tb(10)
    cfg = TruncateConfig(max_frames=10, keep_top=3, keep_bottom=7)
    result = truncate(tb, cfg)
    assert result.omitted == 0


def test_format_truncated_contains_omission_label():
    tb = _tb(20)
    cfg = TruncateConfig(max_frames=10, keep_top=3, keep_bottom=7)
    tt = truncate(tb, cfg)
    output = format_truncated(tt, cfg)
    assert "10 frames omitted" in output


def test_format_truncated_contains_exception_line():
    tb = _tb(20)
    tt = truncate(tb)
    output = format_truncated(tt)
    assert "ValueError: oops" in output


def test_format_not_truncated_no_omission_label():
    tb = _tb(5)
    tt = truncate(tb)
    output = format_truncated(tt)
    assert "omitted" not in output


def test_default_config_used_when_none():
    tb = _tb(50)
    result = truncate(tb)
    assert result.omitted == 40
    assert len(result.frames) == 10
