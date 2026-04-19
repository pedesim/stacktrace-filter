"""Tests for stacktrace_filter.censor and censor_cli."""
from __future__ import annotations
import json
import os
import tempfile
import pytest
from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.censor import CensorRule, CensorConfig, censor, format_censor_result


def _frame(filename="app/views.py", lineno=10, function="handle", text="return secret"):
    return Frame(filename=filename, lineno=lineno, function=function, text=text)


def _tb(frames=None):
    return Traceback(
        frames=frames or [_frame()],
        exception_type="ValueError",
        exception_message="bad value",
    )


def test_censor_no_rules_unchanged():
    tb = _tb()
    result = censor(tb, CensorConfig())
    assert result.censored_count == 0
    assert result.traceback.frames[0].text == "return secret"


def test_censor_rule_replaces_text():
    rule = CensorRule(field="text", pattern=r"secret", replacement="***")
    config = CensorConfig(rules=[rule])
    result = censor(_tb(), config)
    assert result.traceback.frames[0].text == "return ***"
    assert result.censored_count == 1


def test_censor_rule_replaces_filename():
    rule = CensorRule(field="filename", pattern=r"app/", replacement="")
    config = CensorConfig(rules=[rule])
    result = censor(_tb(), config)
    assert result.traceback.frames[0].filename == "views.py"


def test_censor_no_match_no_change():
    rule = CensorRule(field="text", pattern=r"password")
    config = CensorConfig(rules=[rule])
    result = censor(_tb(), config)
    assert result.censored_count == 0


def test_censor_multiple_frames():
    frames = [
        _frame(text="token = abc123"),
        _frame(text="safe line"),
        _frame(text="api_key = xyz"),
    ]
    rule = CensorRule(field="text", pattern=r"(token|api_key) = \S+", replacement="<censored>")
    result = censor(_tb(frames=frames), CensorConfig(rules=[rule]))
    assert result.censored_count == 2
    assert "<censored>" in result.traceback.frames[0].text
    assert result.traceback.frames[1].text == "safe line"


def test_format_censor_result_includes_count():
    result = censor(_tb(), CensorConfig())
    output = format_censor_result(result)
    assert "censored fields: 0" in output


def test_censor_rule_function_field():
    rule = CensorRule(field="function", pattern=r"handle", replacement="fn")
    result = censor(_tb(), CensorConfig(rules=[rule]))
    assert result.traceback.frames[0].function == "fn"
    assert result.censored_count == 1


def test_censor_preserves_exception():
    tb = _tb()
    result = censor(tb, CensorConfig())
    assert result.traceback.exception_type == "ValueError"
    assert result.traceback.exception_message == "bad value"
