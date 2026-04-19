"""Tests for stacktrace_filter.throttler."""
import pytest
from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.throttler import Throttler, ThrottlerConfig, throttle


def _frame(fn: str = "app.py") -> Frame:
    return Frame(filename=fn, lineno=1, name="fn", source="pass")


def _tb(exc: str = "ValueError", msg: str = "bad") -> Traceback:
    return Traceback(frames=[_frame()], exception_type=exc, exception_message=msg)


def test_first_occurrence_allowed():
    t = Throttler()
    r = t.check(_tb(), now=0.0)
    assert r.allowed is True
    assert r.count_in_window == 1


def test_within_limit_allowed():
    cfg = ThrottlerConfig(max_per_window=3, window_seconds=60.0)
    t = Throttler(cfg)
    for i in range(3):
        r = t.check(_tb(), now=float(i))
        assert r.allowed is True


def test_exceeds_limit_blocked():
    cfg = ThrottlerConfig(max_per_window=2, window_seconds=60.0)
    t = Throttler(cfg)
    t.check(_tb(), now=0.0)
    t.check(_tb(), now=1.0)
    r = t.check(_tb(), now=2.0)
    assert r.allowed is False
    assert r.count_in_window == 2


def test_window_expiry_resets_count():
    cfg = ThrottlerConfig(max_per_window=1, window_seconds=10.0)
    t = Throttler(cfg)
    t.check(_tb(), now=0.0)
    r = t.check(_tb(), now=11.0)  # old entry expired
    assert r.allowed is True


def test_different_fingerprints_independent():
    cfg = ThrottlerConfig(max_per_window=1, window_seconds=60.0)
    t = Throttler(cfg)
    r1 = t.check(_tb(exc="ValueError"), now=0.0)
    r2 = t.check(_tb(exc="KeyError"), now=0.0)
    assert r1.allowed is True
    assert r2.allowed is True


def test_filter_returns_only_allowed():
    cfg = ThrottlerConfig(max_per_window=1, window_seconds=60.0)
    tbs = [_tb(), _tb(), _tb()]
    kept = Throttler(cfg).filter(tbs, now=0.0)
    assert len(kept) == 1


def test_reset_clears_state():
    cfg = ThrottlerConfig(max_per_window=1, window_seconds=60.0)
    t = Throttler(cfg)
    t.check(_tb(), now=0.0)
    t.reset()
    r = t.check(_tb(), now=1.0)
    assert r.allowed is True


def test_throttle_convenience():
    cfg = ThrottlerConfig(max_per_window=2, window_seconds=60.0)
    tbs = [_tb()] * 5
    kept = throttle(tbs, cfg)
    assert len(kept) == 2


def test_result_carries_fingerprint():
    t = Throttler()
    r = t.check(_tb(), now=0.0)
    assert isinstance(r.fingerprint, str) and len(r.fingerprint) > 0
