"""Tests for stacktrace_filter.aggregator."""
import pytest
from stacktrace_filter.parser import Traceback, Frame
from stacktrace_filter.aggregator import aggregate, format_aggregation, AggregationReport


def _frame(filename="app.py", lineno=10, name="fn", line="pass"):
    return Frame(filename=filename, lineno=lineno, name=name, line=line)


def _tb(exc_type="ValueError", exc_message="bad value", frames=None):
    return Traceback(
        frames=frames or [_frame()],
        exc_type=exc_type,
        exc_message=exc_message,
    )


def test_aggregate_empty():
    report = aggregate([])
    assert report.total == 0
    assert report.entries == []


def test_aggregate_single():
    tb = _tb()
    report = aggregate([tb])
    assert report.total == 1
    assert len(report.entries) == 1
    assert report.entries[0].count == 1
    assert report.entries[0].exc_type == "ValueError"


def test_aggregate_duplicates_counted():
    tb = _tb()
    report = aggregate([tb, tb, tb])
    assert report.total == 3
    assert len(report.entries) == 1
    assert report.entries[0].count == 3


def test_aggregate_two_distinct():
    tb1 = _tb(exc_type="ValueError", frames=[_frame(lineno=1)])
    tb2 = _tb(exc_type="KeyError", frames=[_frame(lineno=99)])
    report = aggregate([tb1, tb2])
    assert report.total == 2
    assert len(report.entries) == 2


def test_aggregate_sorted_by_count():
    tb1 = _tb(exc_type="ValueError", frames=[_frame(lineno=1)])
    tb2 = _tb(exc_type="KeyError", frames=[_frame(lineno=99)])
    report = aggregate([tb1, tb2, tb2, tb2])
    assert report.entries[0].exc_type == "KeyError"
    assert report.entries[0].count == 3


def test_by_severity_keys():
    tb = _tb(exc_type="MemoryError")
    report = aggregate([tb])
    assert isinstance(report.by_severity, dict)
    assert sum(report.by_severity.values()) == 1


def test_format_aggregation_contains_fingerprint():
    tb = _tb()
    report = aggregate([tb])
    output = format_aggregation(report)
    assert "[" in output
    assert "ValueError" in output


def test_format_aggregation_severity_breakdown():
    tb = _tb()
    report = aggregate([tb])
    output = format_aggregation(report)
    assert "Severity breakdown" in output
