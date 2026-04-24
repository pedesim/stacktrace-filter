"""Tests for stacktrace_filter.collapser."""
import pytest
from stacktrace_filter.parser import Frame
from stacktrace_filter.collapser import (
    CollapseConfig,
    CollapseResult,
    CollapsedFrame,
    collapse,
    format_collapse_result,
)


def _frame(filename: str, name: str = "fn", lineno: int = 1, line: str = "pass") -> Frame:
    return Frame(filename=filename, name=name, lineno=lineno, line=line)


def _user(name: str = "fn") -> Frame:
    return _frame("/home/user/project/app.py", name=name)


def _stdlib(name: str = "fn") -> Frame:
    return _frame("/usr/lib/python3.11/os.py", name=name)


def _lib(name: str = "fn") -> Frame:
    return _frame("/usr/lib/python3.11/site-packages/requests/api.py", name=name)


# --- collapse() ---

def test_collapse_empty_list():
    result = collapse([])
    assert isinstance(result, CollapseResult)
    assert result.entries == []
    assert result.total_hidden == 0
    assert result.real_count == 0


def test_collapse_all_user_frames_kept():
    frames = [_user("a"), _user("b"), _user("c")]
    result = collapse(frames)
    assert result.real_count == 3
    assert result.total_hidden == 0
    assert all(e.is_real for e in result.entries)


def test_collapse_stdlib_frames_hidden():
    frames = [_stdlib("a"), _stdlib("b")]
    result = collapse(frames)
    assert result.total_hidden == 2
    assert result.real_count == 0
    assert len(result.entries) == 1
    assert result.entries[0].is_collapsed


def test_collapse_site_package_frames_hidden():
    frames = [_lib("a"), _lib("b"), _lib("c")]
    result = collapse(frames)
    assert result.total_hidden == 3
    assert len(result.entries) == 1


def test_collapse_mixed_frames():
    frames = [_user("entry"), _stdlib("x"), _stdlib("y"), _user("inner")]
    result = collapse(frames)
    # user, collapsed(2), user
    assert result.real_count == 2
    assert result.total_hidden == 2
    assert len(result.entries) == 3
    assert result.entries[0].is_real
    assert result.entries[1].is_collapsed
    assert result.entries[1].collapsed_count == 2
    assert result.entries[2].is_real


def test_collapse_label_format():
    cfg = CollapseConfig(label="--- {count} hidden ---")
    frames = [_stdlib("a"), _stdlib("b")]
    result = collapse(frames, cfg)
    assert result.entries[0].label == "--- 2 hidden ---"


def test_collapse_stdlib_disabled():
    cfg = CollapseConfig(collapse_stdlib=False)
    frames = [_stdlib("a"), _stdlib("b")]
    result = collapse(frames, cfg)
    assert result.real_count == 2
    assert result.total_hidden == 0


def test_collapse_site_packages_disabled():
    cfg = CollapseConfig(collapse_site_packages=False)
    frames = [_lib("a"), _lib("b")]
    result = collapse(frames, cfg)
    assert result.real_count == 2
    assert result.total_hidden == 0


# --- format_collapse_result() ---

def test_format_shows_real_frame_filename():
    frames = [_user("my_func")]
    result = collapse(frames)
    output = format_collapse_result(result)
    assert "app.py" in output
    assert "my_func" in output


def test_format_shows_collapsed_label():
    frames = [_stdlib("a"), _stdlib("b")]
    result = collapse(frames)
    output = format_collapse_result(result)
    assert "2 frame(s) hidden" in output


def test_format_color_adds_ansi():
    frames = [_stdlib("a")]
    result = collapse(frames)
    output = format_collapse_result(result, color=True)
    assert "\033[" in output


def test_format_no_color_no_ansi():
    frames = [_stdlib("a")]
    result = collapse(frames)
    output = format_collapse_result(result, color=False)
    assert "\033[" not in output
