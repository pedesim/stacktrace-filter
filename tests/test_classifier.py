"""Tests for stacktrace_filter.classifier."""
import pytest
from stacktrace_filter.parser import Traceback, Frame
from stacktrace_filter.classifier import (
    classify, format_classification,
    CATEGORY_USER, CATEGORY_STDLIB, CATEGORY_LIBRARY, CATEGORY_MIXED,
)


def _frame(filename: str, lineno: int = 1, name: str = "fn") -> Frame:
    return Frame(filename=filename, lineno=lineno, name=name, source_line="pass")


def _tb(frames, exc="RuntimeError: boom") -> Traceback:
    return Traceback(frames=frames, exception_line=exc)


def test_classify_all_user_frames():
    tb = _tb([_frame("app/main.py"), _frame("app/utils.py")])
    ct = classify(tb)
    assert ct.category == CATEGORY_USER
    assert ct.user_frame_count == 2
    assert ct.stdlib_frame_count == 0
    assert ct.library_frame_count == 0


def test_classify_all_stdlib_frames():
    tb = _tb([_frame("/usr/lib/python3.11/os.py"), _frame("/usr/lib/python3.11/io.py")])
    ct = classify(tb)
    assert ct.category == CATEGORY_STDLIB
    assert ct.stdlib_frame_count == 2


def test_classify_all_library_frames():
    tb = _tb([_frame("/usr/lib/python3/dist-packages/requests/api.py")])
    ct = classify(tb)
    assert ct.category == CATEGORY_LIBRARY
    assert ct.library_frame_count == 1


def test_classify_mixed_frames():
    tb = _tb([
        _frame("app/main.py"),
        _frame("/usr/lib/python3.11/os.py"),
    ])
    ct = classify(tb)
    assert ct.category == CATEGORY_MIXED
    assert ct.user_frame_count == 1
    assert ct.stdlib_frame_count == 1


def test_classify_empty_frames():
    tb = _tb([])
    ct = classify(tb)
    assert ct.category == CATEGORY_USER
    assert ct.user_frame_count == 0


def test_classify_tags_error():
    tb = _tb([_frame("app/main.py")], exc="ValueError: bad input")
    ct = classify(tb)
    assert "error" in ct.tags


def test_classify_tags_warning():
    tb = _tb([_frame("app/main.py")], exc="DeprecationWarning: old api")
    ct = classify(tb)
    assert "warning" in ct.tags


def test_classify_tags_no_user_frames():
    tb = _tb([_frame("/usr/lib/python3.11/os.py")])
    ct = classify(tb)
    assert "no-user-frames" in ct.tags


def test_dominant_file_most_common():
    tb = _tb([
        _frame("app/main.py"),
        _frame("app/main.py"),
        _frame("app/utils.py"),
    ])
    ct = classify(tb)
    assert ct.dominant_file == "app/main.py"


def test_format_classification_contains_category():
    tb = _tb([_frame("app/main.py")])
    ct = classify(tb)
    output = format_classification(ct)
    assert "user" in output
    assert "Frames" in output
