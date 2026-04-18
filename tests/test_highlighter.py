"""Tests for stacktrace_filter.highlighter."""
import pytest
from stacktrace_filter.highlighter import highlight_line, highlight_exception_line

_RESET = "\033[0m"
_BOLD = "\033[1m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_CYAN = "\033[36m"


def strip_ansi(text: str) -> str:
    import re
    return re.sub(r"\033\[[\d;]*m", "", text)


def test_highlight_line_no_color():
    line = "return x + 1"
    assert highlight_line(line, color=False) == line


def test_highlight_line_keyword_present():
    result = highlight_line("return value", color=True)
    assert _YELLOW in result
    assert "return" in strip_ansi(result)


def test_highlight_line_comment():
    result = highlight_line("x = 1  # comment", color=True)
    assert _CYAN in result
    assert "# comment" in strip_ansi(result)


def test_highlight_line_number():
    result = highlight_line("x = 42", color=True)
    assert "42" in strip_ansi(result)


def test_highlight_line_preserves_content():
    line = "for i in range(10):"
    result = highlight_line(line, color=True)
    assert strip_ansi(result) == line


def test_highlight_exception_no_color():
    text = "ValueError: something went wrong"
    assert highlight_exception_line(text, color=False) == text


def test_highlight_exception_colors_type():
    text = "ValueError: bad input"
    result = highlight_exception_line(text, color=True)
    assert _RED in result
    assert _BOLD in result
    assert "ValueError" in strip_ansi(result)
    assert "bad input" in strip_ansi(result)


def test_highlight_exception_unknown_format():
    text = "something unexpected"
    result = highlight_exception_line(text, color=True)
    assert _RED in result
    assert strip_ansi(result) == text


def test_highlight_exception_nested_module():
    text = "json.decoder.JSONDecodeError: Expecting value"
    result = highlight_exception_line(text, color=True)
    assert "JSONDecodeError" in strip_ansi(result)
