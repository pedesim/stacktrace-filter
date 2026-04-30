"""Tests for stacktrace_filter.correlator."""
from __future__ import annotations

import pytest

from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.correlator import (
    CorrelationEdge,
    CorrelationResult,
    _frame_key,
    _shared_keys,
    correlate,
    format_correlation,
)


def _frame(
    filename: str = "app.py",
    function: str = "fn",
    lineno: int = 10,
    line: str = "pass",
) -> Frame:
    return Frame(filename=filename, function=function, lineno=lineno, line=line)


def _tb(frames, exc_type="ValueError", exc_message="oops") -> Traceback:
    return Traceback(frames=frames, exc_type=exc_type, exc_message=exc_message)


# ---------------------------------------------------------------------------
# _frame_key
# ---------------------------------------------------------------------------

def test_frame_key_returns_tuple():
    f = _frame(filename="a.py", function="foo", lineno=5)
    assert _frame_key(f) == ("a.py", "foo", 5)


# ---------------------------------------------------------------------------
# _shared_keys
# ---------------------------------------------------------------------------

def test_shared_keys_no_overlap():
    a = _tb([_frame("a.py", "f", 1)])
    b = _tb([_frame("b.py", "g", 2)])
    assert _shared_keys(a, b) == frozenset()


def test_shared_keys_full_overlap():
    f = _frame("a.py", "f", 1)
    a = _tb([f])
    b = _tb([f])
    assert len(_shared_keys(a, b)) == 1


# ---------------------------------------------------------------------------
# correlate
# ---------------------------------------------------------------------------

def test_correlate_empty_list():
    result = correlate([])
    assert result.edges == []
    assert result.clusters == []
    assert result.cluster_count == 0


def test_correlate_single_traceback():
    tb = _tb([_frame()])
    result = correlate([tb])
    assert result.edges == []
    assert result.cluster_count == 1
    assert result.clusters == [[0]]


def test_correlate_no_shared_frames():
    a = _tb([_frame("a.py", "f", 1)])
    b = _tb([_frame("b.py", "g", 2)])
    result = correlate([a, b])
    assert result.edges == []
    assert result.cluster_count == 2


def test_correlate_shared_frame_creates_edge():
    shared = _frame("common.py", "helper", 42)
    a = _tb([shared, _frame("a.py", "f", 1)])
    b = _tb([shared, _frame("b.py", "g", 2)])
    result = correlate([a, b])
    assert len(result.edges) == 1
    edge = result.edges[0]
    assert edge.index_a == 0
    assert edge.index_b == 1
    assert edge.shared_frame_count == 1


def test_correlate_cluster_merges_connected():
    shared = _frame("common.py", "helper", 42)
    a = _tb([shared])
    b = _tb([shared])
    c = _tb([shared])
    result = correlate([a, b, c])
    # All three share the same frame → one cluster
    assert result.cluster_count == 1
    assert sorted(result.clusters[0]) == [0, 1, 2]


def test_correlate_min_shared_filters_edge():
    shared1 = _frame("common.py", "h", 1)
    a = _tb([shared1, _frame("a.py", "f", 10)])
    b = _tb([shared1, _frame("b.py", "g", 20)])
    result = correlate([a, b], min_shared=2)
    assert result.edges == []
    assert result.cluster_count == 2


def test_get_cluster_returns_correct_tracebacks():
    shared = _frame("x.py", "x", 1)
    a = _tb([shared])
    b = _tb([shared])
    c = _tb([_frame("y.py", "y", 2)])
    result = correlate([a, b, c])
    cluster_for_0 = result.get_cluster(0)
    assert a in cluster_for_0
    assert b in cluster_for_0
    assert c not in cluster_for_0


# ---------------------------------------------------------------------------
# format_correlation
# ---------------------------------------------------------------------------

def test_format_correlation_contains_summary():
    shared = _frame("c.py", "h", 5)
    a = _tb([shared])
    b = _tb([shared])
    result = correlate([a, b])
    text = format_correlation(result, color=False)
    assert "2 tracebacks" in text
    assert "1 edge" in text
    assert "1 cluster" in text


def test_format_correlation_no_edges():
    result = correlate([_tb([_frame()])])
    text = format_correlation(result, color=False)
    assert "0 edges" in text
