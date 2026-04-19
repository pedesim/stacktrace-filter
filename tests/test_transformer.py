"""Tests for stacktrace_filter.transformer and transformer_cli."""
from __future__ import annotations
import pytest
from unittest.mock import patch
from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.transformer import (
    TransformPipeline, drop_frames, limit_frames, relabel_frames, transform,
)


def _frame(filename="app/main.py", lineno=10, function="run", source="x()"):
    return Frame(filename=filename, lineno=lineno, function=function, source=source)


def _tb(*frames, exception="Error: boom"):
    return Traceback(frames=list(frames), exception=exception)


def test_drop_frames_removes_matching():
    tb = _tb(_frame("lib/stdlib.py"), _frame("app/main.py"))
    fn = drop_frames(lambda f: "stdlib" in f.filename)
    result = fn(tb)
    assert len(result.frames) == 1
    assert result.frames[0].filename == "app/main.py"


def test_drop_frames_keeps_all_when_none_match():
    tb = _tb(_frame(), _frame())
    fn = drop_frames(lambda f: False)
    assert len(fn(tb).frames) == 2


def test_limit_frames_last():
    tb = _tb(*[_frame(lineno=i) for i in range(5)])
    fn = limit_frames(3, keep="last")
    result = fn(tb)
    assert len(result.frames) == 3
    assert result.frames[0].lineno == 2


def test_limit_frames_first():
    tb = _tb(*[_frame(lineno=i) for i in range(5)])
    fn = limit_frames(3, keep="first")
    result = fn(tb)
    assert len(result.frames) == 3
    assert result.frames[-1].lineno == 2


def test_limit_frames_no_op_when_under_limit():
    tb = _tb(_frame(), _frame())
    fn = limit_frames(10)
    assert len(fn(tb).frames) == 2


def test_relabel_frames_rewrites_filename():
    tb = _tb(_frame(filename="/old/path.py"))
    fn = relabel_frames({"/old/path.py": "/new/path.py"})
    assert fn(tb).frames[0].filename == "/new/path.py"


def test_relabel_frames_leaves_unknown():
    tb = _tb(_frame(filename="other.py"))
    fn = relabel_frames({"/old/path.py": "/new/path.py"})
    assert fn(tb).frames[0].filename == "other.py"


def test_pipeline_applies_steps_in_order():
    tb = _tb(*[_frame(lineno=i) for i in range(6)])
    pipeline = (
        TransformPipeline()
        .add(drop_frames(lambda f: f.lineno == 0))
        .add(limit_frames(3))
    )
    result = pipeline.run(tb)
    assert len(result.frames) == 3


def test_transform_result_frame_delta():
    tb = _tb(_frame(), _frame(), _frame())
    pipeline = TransformPipeline().add(limit_frames(1))
    res = transform(tb, pipeline)
    assert res.frame_delta == -2
    assert res.steps_applied == 1


def test_transform_result_original_unchanged():
    tb = _tb(_frame(), _frame())
    pipeline = TransformPipeline().add(drop_frames(lambda f: True))
    res = transform(tb, pipeline)
    assert len(res.original.frames) == 2
    assert len(res.transformed.frames) == 0
