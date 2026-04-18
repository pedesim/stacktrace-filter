"""Tests for stacktrace_filter.redactor."""
import pytest
from stacktrace_filter.redactor import (
    RedactorConfig,
    redact_locals,
    redact_annotated_frames,
    should_redact,
    _compile_patterns,
    REDACTED,
)
from stacktrace_filter.annotator import AnnotatedFrame
from stacktrace_filter.parser import Frame


def _af(locals_dict):
    f = Frame(filename="app.py", lineno=1, name="fn", line="pass")
    return AnnotatedFrame(frame=f, locals=locals_dict)


def test_should_redact_password():
    compiled = _compile_patterns(["password"], False)
    assert should_redact("password", compiled)
    assert should_redact("user_password", compiled)
    assert not should_redact("username", compiled)


def test_should_redact_case_insensitive():
    compiled = _compile_patterns(["token"], False)
    assert should_redact("ACCESS_TOKEN", compiled)


def test_should_redact_case_sensitive():
    compiled = _compile_patterns(["token"], True)
    assert not should_redact("TOKEN", compiled)
    assert should_redact("token", compiled)


def test_redact_locals_sensitive_keys():
    result = redact_locals({"password": "s3cr3t", "username": "alice"})
    assert result["password"] == REDACTED
    assert result["username"] == "alice"


def test_redact_locals_custom_placeholder():
    cfg = RedactorConfig(placeholder="***")
    result = redact_locals({"api_key": "abc123"}, cfg)
    assert result["api_key"] == "***"


def test_redact_locals_no_sensitive():
    data = {"x": "1", "y": "2"}
    assert redact_locals(data) == data


def test_redact_locals_custom_pattern():
    cfg = RedactorConfig(patterns=["ssn"])
    result = redact_locals({"ssn": "123-45-6789", "name": "Bob"}, cfg)
    assert result["ssn"] == REDACTED
    assert result["name"] == "Bob"


def test_redact_annotated_frames_empty():
    assert redact_annotated_frames([]) == []


def test_redact_annotated_frames_redacts_locals():
    frames = [_af({"secret": "xyz", "count": "3"})]
    result = redact_annotated_frames(frames)
    assert result[0].locals["secret"] == REDACTED
    assert result[0].locals["count"] == "3"


def test_redact_annotated_frames_preserves_note():
    af = _af({"x": "1"})
    af = AnnotatedFrame(frame=af.frame, locals=af.locals, note="important")
    result = redact_annotated_frames([af])
    assert result[0].note == "important"


def test_redact_annotated_frames_returns_new_objects():
    frames = [_af({"token": "abc"})]
    result = redact_annotated_frames(frames)
    assert result[0] is not frames[0]
