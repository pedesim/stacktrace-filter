"""Tests for stacktrace_filter.router."""
import pytest
from stacktrace_filter.parser import Traceback, Frame
from stacktrace_filter.router import (
    RouteRule, RouterConfig, RoutedTraceback,
    route, route_all, format_routing_report,
)


def _frame(filename="app/views.py", lineno=10, name="view", line="pass"):
    return Frame(filename=filename, lineno=lineno, name=name, line=line)


def _tb(exc_type="ValueError", exc_message="bad input", frames=None):
    return Traceback(
        frames=frames or [_frame()],
        exc_type=exc_type,
        exc_message=exc_message,
    )


def test_route_default_when_no_rules():
    config = RouterConfig(rules=[], default_destination="catch_all")
    rt = route(_tb(), config)
    assert rt.destination == "catch_all"
    assert rt.rule is None


def test_route_matches_exc_type():
    rule = RouteRule(destination="value_errors", exc_type="ValueError")
    config = RouterConfig(rules=[rule])
    rt = route(_tb(exc_type="ValueError"), config)
    assert rt.destination == "value_errors"
    assert rt.rule is rule


def test_route_no_match_exc_type():
    rule = RouteRule(destination="value_errors", exc_type="TypeError")
    config = RouterConfig(rules=[rule])
    rt = route(_tb(exc_type="ValueError"), config)
    assert rt.destination == "default"


def test_route_matches_exc_message():
    rule = RouteRule(destination="auth", exc_message="permission")
    config = RouterConfig(rules=[rule])
    rt = route(_tb(exc_message="Permission denied"), config)
    assert rt.destination == "auth"


def test_route_matches_filename_contains():
    rule = RouteRule(destination="views", filename_contains="views.py")
    config = RouterConfig(rules=[rule])
    rt = route(_tb(frames=[_frame(filename="app/views.py")]), config)
    assert rt.destination == "views"


def test_route_filename_no_match():
    rule = RouteRule(destination="models", filename_contains="models.py")
    config = RouterConfig(rules=[rule])
    rt = route(_tb(frames=[_frame(filename="app/views.py")]), config)
    assert rt.destination == "default"


def test_route_all_groups_correctly():
    tbs = [
        _tb(exc_type="ValueError"),
        _tb(exc_type="TypeError"),
        _tb(exc_type="ValueError"),
    ]
    rule = RouteRule(destination="value_errors", exc_type="ValueError")
    config = RouterConfig(rules=[rule])
    grouped = route_all(tbs, config)
    assert len(grouped["value_errors"]) == 2
    assert len(grouped["default"]) == 1


def test_format_routing_report():
    tbs = [_tb(exc_type="ValueError"), _tb(exc_type="TypeError")]
    rule = RouteRule(destination="errs", exc_type="ValueError")
    config = RouterConfig(rules=[rule])
    grouped = route_all(tbs, config)
    report = format_routing_report(grouped)
    assert "errs" in report
    assert "ValueError" in report
