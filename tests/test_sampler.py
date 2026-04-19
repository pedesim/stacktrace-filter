"""Tests for stacktrace_filter.sampler."""
import pytest

from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.sampler import (
    SamplerConfig,
    SampleResult,
    format_sample_result,
    sample,
)


def _frame(filename="app.py", lineno=10, func="fn", line="pass"):
    return Frame(filename=filename, lineno=lineno, func=func, line=line)


def _tb(exc_type="ValueError", msg="oops", n=2):
    return Traceback(
        frames=[_frame(lineno=i) for i in range(n)],
        exc_type=exc_type,
        exc_message=msg,
    )


def _tbs(count=10):
    return [_tb(msg=f"msg{i}") for i in range(count)]


def test_sample_rate_one_keeps_all():
    tbs = _tbs(10)
    result = sample(tbs, SamplerConfig(rate=1.0))
    assert len(result.kept) == 10
    assert result.dropped == 0
    assert result.total == 10


def test_sample_rate_zero_drops_all():
    tbs = _tbs(10)
    result = sample(tbs, SamplerConfig(rate=0.0))
    assert result.kept == []
    assert result.dropped == 10


def test_sample_default_config_keeps_all():
    tbs = _tbs(5)
    result = sample(tbs)
    assert len(result.kept) == 5


def test_sample_seeded_reproducible():
    tbs = _tbs(100)
    cfg = SamplerConfig(rate=0.5, seed=42)
    r1 = sample(tbs, cfg)
    r2 = sample(tbs, cfg)
    assert [t.exc_message for t in r1.kept] == [t.exc_message for t in r2.kept]


def test_sample_seeded_approximate_rate():
    tbs = _tbs(1000)
    result = sample(tbs, SamplerConfig(rate=0.3, seed=0))
    assert 0.2 <= result.keep_rate <= 0.4


def test_sample_deterministic_reproducible():
    tbs = _tbs(50)
    cfg = SamplerConfig(rate=0.5, deterministic=True)
    r1 = sample(tbs, cfg)
    r2 = sample(tbs, cfg)
    assert len(r1.kept) == len(r2.kept)
    assert [t.exc_message for t in r1.kept] == [t.exc_message for t in r2.kept]


def test_keep_rate_property():
    r = SampleResult(kept=[_tb()], dropped=3)
    assert r.total == 4
    assert r.keep_rate == pytest.approx(0.25)


def test_keep_rate_empty():
    r = SampleResult()
    assert r.keep_rate == 0.0


def test_format_sample_result_contains_counts():
    tbs = _tbs(10)
    result = sample(tbs, SamplerConfig(rate=1.0))
    out = format_sample_result(result)
    assert "10" in out
    assert "kept" in out
    assert "dropped" in out
    assert "%" in out
