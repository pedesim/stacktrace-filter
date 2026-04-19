"""Tests for stacktrace_filter.enricher."""
import sys
import types
from unittest.mock import patch

import pytest

from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.enricher import (
    EnrichedFrame,
    EnrichedTraceback,
    enrich_frame,
    enrich,
    format_enriched_frame,
)


def _frame(filename="app.py", lineno=10, name="do_thing"):
    return Frame(filename=filename, lineno=lineno, name=name, line="x = 1")


def _tb(frames=None):
    if frames is None:
        frames = [_frame()]
    return Traceback(
        frames=frames,
        exception_type="ValueError",
        exception_message="bad value",
    )


def test_enrich_frame_no_source():
    frame = _frame(filename="/nonexistent/file.py", lineno=1)
    ef = enrich_frame(frame, context=2)
    assert isinstance(ef, EnrichedFrame)
    assert ef.source_line is None
    assert ef.has_source is False
    assert ef.context_before == []
    assert ef.context_after == []


def test_enrich_frame_with_source(tmp_path):
    src = tmp_path / "sample.py"
    src.write_text("line1\nline2\nline3\nline4\nline5\n")
    frame = _frame(filename=str(src), lineno=3)
    ef = enrich_frame(frame, context=1)
    assert ef.source_line == "line3"
    assert ef.context_before == ["line2"]
    assert ef.context_after == ["line4"]
    assert ef.has_source is True


def test_enrich_frame_context_zero(tmp_path):
    src = tmp_path / "sample.py"
    src.write_text("a\nb\nc\n")
    frame = _frame(filename=str(src), lineno=2)
    ef = enrich_frame(frame, context=0)
    assert ef.source_line == "b"
    assert ef.context_before == []
    assert ef.context_after == []


def test_enrich_traceback(tmp_path):
    src = tmp_path / "app.py"
    src.write_text("def foo():\n    raise ValueError\n")
    frames = [
        _frame(filename=str(src), lineno=1),
        _frame(filename=str(src), lineno=2),
    ]
    tb = _tb(frames=frames)
    et = enrich(tb, context=0)
    assert isinstance(et, EnrichedTraceback)
    assert len(et.frames) == 2
    assert et.exception_type == "ValueError"
    assert et.exception_message == "bad value"
    assert et.frames[0].source_line == "def foo():"
    assert et.frames[1].source_line == "    raise ValueError"


def test_format_enriched_frame_no_source():
    ef = EnrichedFrame(frame=_frame(), source_line=None)
    result = format_enriched_frame(ef)
    assert result == ""


def test_format_enriched_frame_with_context():
    ef = EnrichedFrame(
        frame=_frame(),
        source_line="x = 1",
        context_before=["# comment"],
        context_after=["y = 2"],
    )
    result = format_enriched_frame(ef)
    assert ">> x = 1" in result
    assert "# comment" in result
    assert "y = 2" in result
    lines = result.splitlines()
    assert len(lines) == 3
