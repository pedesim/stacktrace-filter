"""Tests for stacktrace_filter.batcher."""
import pytest
from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.batcher import (
    Batch, BatchResult, batch_tracebacks, iter_batches, format_batch_result,
)


def _tb(exc="ValueError", msg="oops") -> Traceback:
    f = Frame(filename="app.py", lineno=1, function="run", source_line="x()")
    return Traceback(frames=[f], exception_type=exc, exception_message=msg)


def test_batch_empty_list():
    result = batch_tracebacks([], batch_size=5)
    assert result.batch_count == 0
    assert result.total == 0


def test_batch_single_item():
    result = batch_tracebacks([_tb()], batch_size=5)
    assert result.batch_count == 1
    assert result.total == 1


def test_batch_exact_multiple():
    tbs = [_tb() for _ in range(6)]
    result = batch_tracebacks(tbs, batch_size=3)
    assert result.batch_count == 2
    assert all(b.size == 3 for b in result.batches)


def test_batch_remainder():
    tbs = [_tb() for _ in range(7)]
    result = batch_tracebacks(tbs, batch_size=3)
    assert result.batch_count == 3
    assert result.batches[-1].size == 1


def test_batch_index_values():
    tbs = [_tb() for _ in range(4)]
    result = batch_tracebacks(tbs, batch_size=2)
    assert [b.index for b in result.batches] == [0, 1]


def test_batch_invalid_size():
    with pytest.raises(ValueError):
        batch_tracebacks([_tb()], batch_size=0)


def test_iter_batches_yields_all():
    tbs = [_tb() for _ in range(5)]
    batches = list(iter_batches(tbs, batch_size=2))
    assert len(batches) == 3
    assert sum(b.size for b in batches) == 5


def test_format_batch_result_contains_counts():
    tbs = [_tb() for _ in range(3)]
    result = batch_tracebacks(tbs, batch_size=2)
    output = format_batch_result(result)
    assert "Batches" in output
    assert "Total" in output
    assert "2" in output
