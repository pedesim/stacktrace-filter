"""Tests for the plugin registry."""
import pytest
from stacktrace_filter.summarizer import TracebackSummary
from stacktrace_filter import plugin as plug


def _make_summary(**kwargs):
    defaults = dict(
        exception_type="ValueError",
        exception_msg="bad",
        frames=[],
        user_frame_count=0,
        stdlib_frame_count=0,
        site_frame_count=0,
        deepest_user_frame=None,
    )
    defaults.update(kwargs)
    return TracebackSummary(**defaults)


def setup_function():
    plug.clear_plugins()


def test_register_and_apply():
    calls = []

    @plug.register
    def my_plugin(s):
        calls.append(True)
        return s

    s = _make_summary()
    plug.apply_plugins(s)
    assert calls == [True]


def test_plugin_mutates_summary():
    @plug.register
    def upcaser(s):
        s.exception_type = s.exception_type.upper()
        return s

    s = _make_summary(exception_type="runtimeerror")
    result = plug.apply_plugins(s)
    assert result.exception_type == "RUNTIMEERROR"


def test_clear_plugins():
    @plug.register
    def noop(s):
        return s

    plug.clear_plugins()
    s = _make_summary()
    result = plug.apply_plugins(s)
    assert result is s


def test_truncate_exc_msg_builtin():
    # Re-register built-in plugin manually after clear
    from stacktrace_filter.plugin import _truncate_exc_msg
    plug.register(_truncate_exc_msg)
    long_msg = "x" * 300
    s = _make_summary(exception_msg=long_msg)
    result = plug.apply_plugins(s)
    assert len(result.exception_msg) <= 203  # 200 + '...'
    assert result.exception_msg.endswith("...")
