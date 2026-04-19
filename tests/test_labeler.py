"""Tests for stacktrace_filter.labeler."""
from __future__ import annotations
import pytest
from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.labeler import (
    LabelRule, LabelerConfig, LabeledTraceback,
    apply_labels, label_all, format_labeled,
)


def _frame(filename="app/views.py", lineno=10, name="view", line="pass"):
    return Frame(filename=filename, lineno=lineno, name=name, line=line)


def _tb(exc_type="ValueError", exc_message="bad input", frames=None):
    return Traceback(
        frames=frames or [_frame()],
        exc_type=exc_type,
        exc_message=exc_message,
    )


def test_apply_labels_no_rules_uses_default():
    config = LabelerConfig(rules=[], default_label="unlabeled")
    lt = apply_labels(_tb(), config)
    assert lt.labels == ["unlabeled"]


def test_apply_labels_exc_type_match():
    rule = LabelRule(label="value-error", exc_type="ValueError")
    config = LabelerConfig(rules=[rule])
    lt = apply_labels(_tb(exc_type="ValueError"), config)
    assert "value-error" in lt.labels


def test_apply_labels_exc_type_no_match():
    rule = LabelRule(label="type-error", exc_type="TypeError")
    config = LabelerConfig(rules=[rule])
    lt = apply_labels(_tb(exc_type="ValueError"), config)
    assert lt.labels == ["unlabeled"]


def test_apply_labels_message_contains():
    rule = LabelRule(label="bad-input", message_contains="bad")
    config = LabelerConfig(rules=[rule])
    lt = apply_labels(_tb(exc_message="bad input"), config)
    assert "bad-input" in lt.labels


def test_apply_labels_filename_contains():
    rule = LabelRule(label="views", filename_contains="views")
    config = LabelerConfig(rules=[rule])
    lt = apply_labels(_tb(frames=[_frame(filename="app/views.py")]), config)
    assert "views" in lt.labels


def test_apply_labels_filename_no_match():
    rule = LabelRule(label="models", filename_contains="models")
    config = LabelerConfig(rules=[rule])
    lt = apply_labels(_tb(frames=[_frame(filename="app/views.py")]), config)
    assert lt.labels == ["unlabeled"]


def test_multiple_rules_multiple_labels():
    rules = [
        LabelRule(label="value-error", exc_type="ValueError"),
        LabelRule(label="bad-input", message_contains="bad"),
    ]
    config = LabelerConfig(rules=rules)
    lt = apply_labels(_tb(), config)
    assert set(lt.labels) == {"value-error", "bad-input"}


def test_primary_label_returns_first():
    lt = LabeledTraceback(traceback=_tb(), labels=["first", "second"])
    assert lt.primary_label() == "first"


def test_primary_label_empty():
    lt = LabeledTraceback(traceback=_tb(), labels=[])
    assert lt.primary_label() is None


def test_label_all_returns_one_per_tb():
    tbs = [_tb(), _tb(exc_type="TypeError")]
    config = LabelerConfig(rules=[])
    result = label_all(tbs, config)
    assert len(result) == 2


def test_format_labeled_includes_label_and_exc():
    lt = LabeledTraceback(traceback=_tb(), labels=["my-label"])
    out = format_labeled(lt)
    assert "my-label" in out
    assert "ValueError" in out
