"""Tests for stacktrace_filter.tagger."""
import pytest
from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.tagger import (
    TagRule,
    TaggedTraceback,
    apply_rules,
    tag_all,
    format_tagged,
)


def _frame(filename="app/views.py", function="handle", lineno=10, text="pass"):
    return Frame(filename=filename, lineno=lineno, function=function, text=text)


def _tb(exc_type="ValueError", exc_message="bad input", frames=None):
    return Traceback(
        frames=frames or [_frame()],
        exc_type=exc_type,
        exc_message=exc_message,
    )


def test_tag_rule_matches_exc_type():
    rule = TagRule(tag="value-error", pattern=r"ValueError", field="exc_type")
    assert rule.matches(_tb(exc_type="ValueError"))
    assert not rule.matches(_tb(exc_type="KeyError"))


def test_tag_rule_matches_exc_message():
    rule = TagRule(tag="auth", pattern=r"permission", field="exc_message")
    assert rule.matches(_tb(exc_message="permission denied"))
    assert not rule.matches(_tb(exc_message="not found"))


def test_tag_rule_matches_filename():
    rule = TagRule(tag="views", pattern=r"views\.py", field="filename")
    assert rule.matches(_tb(frames=[_frame(filename="app/views.py")]))
    assert not rule.matches(_tb(frames=[_frame(filename="app/models.py")]))


def test_tag_rule_matches_function():
    rule = TagRule(tag="handle", pattern=r"^handle", field="function")
    assert rule.matches(_tb(frames=[_frame(function="handle_request")]))
    assert not rule.matches(_tb(frames=[_frame(function="dispatch")]))


def test_apply_rules_multiple_tags():
    rules = [
        TagRule(tag="value-error", pattern=r"ValueError", field="exc_type"),
        TagRule(tag="views", pattern=r"views", field="filename"),
    ]
    tt = apply_rules(_tb(), rules)
    assert "value-error" in tt.tags
    assert "views" in tt.tags


def test_apply_rules_no_match():
    rules = [TagRule(tag="auth", pattern=r"AuthError", field="exc_type")]
    tt = apply_rules(_tb(exc_type="ValueError"), rules)
    assert tt.tags == []


def test_tag_all_returns_correct_count():
    tbs = [_tb(), _tb(exc_type="KeyError")]
    rules = [TagRule(tag="key", pattern=r"KeyError", field="exc_type")]
    result = tag_all(tbs, rules)
    assert len(result) == 2
    assert result[1].tags == ["key"]
    assert result[0].tags == []


def test_format_tagged_with_tags():
    tt = TaggedTraceback(traceback=_tb(), tags=["beta", "alpha"])
    assert format_tagged(tt) == "[alpha, beta]"


def test_format_tagged_no_tags():
    tt = TaggedTraceback(traceback=_tb(), tags=[])
    assert format_tagged(tt) == "[untagged]"
