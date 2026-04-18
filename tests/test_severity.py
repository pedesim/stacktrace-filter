"""Tests for stacktrace_filter.severity and severity_cli."""
import pytest
from unittest.mock import patch
from stacktrace_filter.parser import Traceback, Frame
from stacktrace_filter.severity import (
    classify, format_severity,
    LEVEL_CRITICAL, LEVEL_ERROR, LEVEL_WARNING, LEVEL_INFO,
)


def _tb(exc_line):
    return Traceback(frames=[], exception_line=exc_line)


def test_classify_critical_exc_type():
    result = classify(_tb("MemoryError: out of memory"))
    assert result.level == LEVEL_CRITICAL
    assert result.score == 100


def test_classify_warning_exc_type():
    result = classify(_tb("DeprecationWarning: old api"))
    assert result.level == LEVEL_WARNING


def test_classify_error_exc_type():
    result = classify(_tb("ValueError: bad value"))
    assert result.level == LEVEL_ERROR


def test_classify_exception_exc_type():
    result = classify(_tb("BaseException: something"))
    assert result.level == LEVEL_ERROR
    assert result.score == 50


def test_classify_info_fallback():
    result = classify(_tb("StopIteration"))
    assert result.level == LEVEL_INFO


def test_classify_no_exception_line():
    result = classify(_tb(None))
    assert result.level == LEVEL_INFO


def test_classify_critical_keyword():
    result = classify(_tb("RuntimeError: database corrupted"), critical_keywords=["corrupted"])
    assert result.level == LEVEL_CRITICAL
    assert result.score == 90


def test_classify_critical_keyword_case_insensitive():
    result = classify(_tb("RuntimeError: Disk FULL"), critical_keywords=["disk full"])
    assert result.level == LEVEL_CRITICAL


def test_format_severity_no_color():
    result = classify(_tb("ValueError: x"))
    out = format_severity(result, color=False)
    assert "[ERROR]" in out
    assert "\033[" not in out


def test_format_severity_color():
    result = classify(_tb("MemoryError: oom"))
    out = format_severity(result, color=True)
    assert "\033[" in out
    assert "[CRITICAL]" in out


def test_severity_cli_main(tmp_path, capsys):
    from stacktrace_filter.severity_cli import main
    f = tmp_path / "tb.txt"
    f.write_text("Traceback (most recent call last):\n  File \"a.py\", line 1, in foo\n    x()\nValueError: bad\n")
    main([str(f), "--no-color"])
    out = capsys.readouterr().out
    assert "ERROR" in out


def test_severity_cli_min_score_filters(tmp_path, capsys):
    from stacktrace_filter.severity_cli import main
    f = tmp_path / "tb.txt"
    f.write_text("Traceback (most recent call last):\n  File \"a.py\", line 1, in foo\n    x()\nValueError: bad\n")
    main([str(f), "--no-color", "--min-score", "99"])
    out = capsys.readouterr().out
    assert out.strip() == ""


def test_severity_cli_missing_file(capsys):
    from stacktrace_filter.severity_cli import main
    with pytest.raises(SystemExit):
        main(["nonexistent_file.txt"])
