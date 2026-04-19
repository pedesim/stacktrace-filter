"""Tests for stacktrace_filter.denoiser."""
import pytest
from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.denoiser import (
    DenoiserConfig,
    DenoiseResult,
    denoise,
    format_denoise_result,
)


def _frame(filename="app.py", lineno=10, function="run", text="run()"):
    return Frame(filename=filename, lineno=lineno, function=function, text=text)


def _tb(*frames, exception="ValueError: bad"):
    return Traceback(frames=list(frames), exception=exception)


def test_denoise_no_config_keeps_all():
    tb = _tb(_frame(), _frame(filename="lib.py", function="helper"))
    result = denoise(tb)
    assert result.removed_count == 0
    assert len(result.traceback.frames) == 2


def test_denoise_filename_pattern_removes_frame():
    cfg = DenoiserConfig(filename_patterns=[r"lib\.py"])
    tb = _tb(_frame(), _frame(filename="lib.py", function="helper"))
    result = denoise(tb, cfg)
    assert result.removed_count == 1
    assert result.removed_frames[0].filename == "lib.py"
    assert len(result.traceback.frames) == 1


def test_denoise_function_pattern_removes_frame():
    cfg = DenoiserConfig(function_patterns=[r"^_internal"])
    tb = _tb(_frame(), _frame(function="_internal_call"))
    result = denoise(tb, cfg)
    assert result.removed_count == 1
    assert result.traceback.frames[0].function == "run"


def test_denoise_respects_min_frames():
    cfg = DenoiserConfig(filename_patterns=[r".*"], min_frames=1)
    tb = _tb(_frame(filename="noise.py"))
    result = denoise(tb, cfg)
    # Would remove the only frame but min_frames=1 prevents it
    assert len(result.traceback.frames) == 1
    assert result.removed_count == 0


def test_denoise_multiple_patterns():
    cfg = DenoiserConfig(
        filename_patterns=[r"vendor/"],
        function_patterns=[r"middleware"],
    )
    frames = [
        _frame(filename="app.py", function="view"),
        _frame(filename="vendor/django.py", function="dispatch"),
        _frame(filename="app.py", function="middleware_hook"),
    ]
    tb = _tb(*frames)
    result = denoise(tb, cfg)
    assert result.removed_count == 2
    assert result.traceback.frames[0].function == "view"


def test_denoise_preserves_exception():
    cfg = DenoiserConfig(filename_patterns=[r"noise"])
    tb = _tb(_frame(), _frame(filename="noise.py"), exception="RuntimeError: oops")
    result = denoise(tb, cfg)
    assert result.traceback.exception == "RuntimeError: oops"


def test_format_denoise_result_with_removed():
    cfg = DenoiserConfig(filename_patterns=[r"lib\.py"])
    tb = _tb(_frame(), _frame(filename="lib.py", function="helper", lineno=42))
    result = denoise(tb, cfg)
    output = format_denoise_result(result)
    assert "removed 1 noise frame" in output
    assert "lib.py" in output


def test_format_denoise_result_none_removed():
    tb = _tb(_frame())
    result = denoise(tb)
    output = format_denoise_result(result)
    assert "no noise frames found" in output
