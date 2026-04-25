"""Tests for stacktrace_filter.resolver."""
from __future__ import annotations

import os

import pytest

from stacktrace_filter.parser import Frame
from stacktrace_filter.resolver import (
    ResolverConfig,
    ResolvedFrame,
    _try_resolve,
    resolve_frame,
    resolve_frames,
    format_resolved_frame,
)


def _frame(filename: str, lineno: int = 1, function: str = "fn", line: str = "pass") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, line=line)


# ---------------------------------------------------------------------------
# _try_resolve
# ---------------------------------------------------------------------------

def test_try_resolve_matches_root(tmp_path):
    target = tmp_path / "src" / "app.py"
    target.parent.mkdir(parents=True)
    target.touch()
    result = _try_resolve(str(target), [str(tmp_path)])
    assert result == os.path.join("src", "app.py")


def test_try_resolve_no_match_returns_none(tmp_path):
    other = tmp_path / "elsewhere" / "x.py"
    result = _try_resolve(str(other), ["/totally/different/root"])
    assert result is None


def test_try_resolve_picks_shortest(tmp_path):
    deep = tmp_path / "a" / "b"
    shallow = tmp_path / "a"
    target = tmp_path / "a" / "b" / "c.py"
    result = _try_resolve(str(target), [str(deep), str(shallow)])
    # relative to deep root is just "c.py" (shorter)
    assert result == "c.py"


# ---------------------------------------------------------------------------
# resolve_frame
# ---------------------------------------------------------------------------

def test_resolve_frame_was_resolved(tmp_path):
    f = _frame(str(tmp_path / "myapp" / "views.py"))
    cfg = ResolverConfig(roots=[str(tmp_path)])
    rf = resolve_frame(f, cfg)
    assert rf.was_resolved is True
    assert rf.resolved_filename == os.path.join("myapp", "views.py")


def test_resolve_frame_not_resolved_keeps_original(tmp_path):
    f = _frame("/some/other/place.py")
    cfg = ResolverConfig(roots=[str(tmp_path)])
    rf = resolve_frame(f, cfg)
    assert rf.was_resolved is False
    assert rf.resolved_filename == "/some/other/place.py"


def test_resolve_frame_fallback_basename():
    f = _frame("/deep/nested/path/module.py")
    cfg = ResolverConfig(roots=[], fallback_basename=True)
    rf = resolve_frame(f, cfg)
    assert rf.was_resolved is False
    assert rf.resolved_filename == "module.py"


def test_resolve_frame_passthrough_properties(tmp_path):
    f = _frame(str(tmp_path / "x.py"), lineno=42, function="do_thing", line="return 1")
    cfg = ResolverConfig(roots=[str(tmp_path)])
    rf = resolve_frame(f, cfg)
    assert rf.lineno == 42
    assert rf.function == "do_thing"
    assert rf.line == "return 1"


# ---------------------------------------------------------------------------
# resolve_frames
# ---------------------------------------------------------------------------

def test_resolve_frames_returns_list(tmp_path):
    frames = [_frame(str(tmp_path / "a.py")), _frame("/other/b.py")]
    cfg = ResolverConfig(roots=[str(tmp_path)])
    result = resolve_frames(frames, cfg)
    assert len(result) == 2
    assert result[0].was_resolved is True
    assert result[1].was_resolved is False


# ---------------------------------------------------------------------------
# format_resolved_frame
# ---------------------------------------------------------------------------

def test_format_resolved_frame_marker_when_resolved(tmp_path):
    f = _frame(str(tmp_path / "app.py"), lineno=10)
    cfg = ResolverConfig(roots=[str(tmp_path)])
    rf = resolve_frame(f, cfg)
    line = format_resolved_frame(rf)
    assert "[*]" in line
    assert "app.py" in line
    assert "line 10" in line


def test_format_resolved_frame_space_when_not_resolved():
    f = _frame("/other/module.py", lineno=5)
    cfg = ResolverConfig(roots=[])
    rf = resolve_frame(f, cfg)
    line = format_resolved_frame(rf)
    assert "[ ]" in line
