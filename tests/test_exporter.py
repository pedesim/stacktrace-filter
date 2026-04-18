"""Tests for stacktrace_filter.exporter."""
import json
import pytest

from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.exporter import (
    frame_to_dict,
    traceback_to_dict,
    export_json,
    export_plain,
    export,
)


def _frame(filename="app.py", lineno=10, name="run", line="do_thing()") -> Frame:
    return Frame(filename=filename, lineno=lineno, name=name, line=line)


def _tb(*frames: Frame) -> Traceback:
    return Traceback(
        frames=list(frames),
        exc_type="ValueError",
        exc_message="bad value",
    )


def test_frame_to_dict():
    f = _frame()
    d = frame_to_dict(f)
    assert d["filename"] == "app.py"
    assert d["lineno"] == 10
    assert d["name"] == "run"
    assert d["line"] == "do_thing()"


def test_traceback_to_dict_structure():
    tb = _tb(_frame(), _frame(filename="other.py", lineno=20))
    d = traceback_to_dict(tb)
    assert d["exception_type"] == "ValueError"
    assert d["exception_message"] == "bad value"
    assert len(d["frames"]) == 2


def test_export_json_valid():
    tb = _tb(_frame())
    result = export_json(tb)
    parsed = json.loads(result)
    assert parsed["exception_type"] == "ValueError"
    assert len(parsed["frames"]) == 1


def test_export_json_indent():
    tb = _tb(_frame())
    result = export_json(tb, indent=4)
    assert "    " in result


def test_export_plain_contains_header():
    tb = _tb(_frame())
    result = export_plain(tb)
    assert result.startswith("Traceback (most recent call last):")


def test_export_plain_contains_exception():
    tb = _tb(_frame())
    result = export_plain(tb)
    assert "ValueError: bad value" in result


def test_export_plain_contains_frame():
    tb = _tb(_frame())
    result = export_plain(tb)
    assert 'File "app.py", line 10, in run' in result
    assert "do_thing()" in result


def test_export_dispatch_json():
    tb = _tb(_frame())
    result = export(tb, fmt="json")
    assert json.loads(result)["exception_type"] == "ValueError"


def test_export_dispatch_plain():
    tb = _tb(_frame())
    result = export(tb, fmt="plain")
    assert "ValueError" in result


def test_export_unknown_format():
    tb = _tb(_frame())
    with pytest.raises(ValueError, match="Unknown export format"):
        export(tb, fmt="xml")
