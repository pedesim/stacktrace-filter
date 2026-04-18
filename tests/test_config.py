"""Tests for FilterConfig."""

import pytest
from stacktrace_filter.config import FilterConfig


def test_defaults():
    cfg = FilterConfig()
    assert cfg.color is True
    assert cfg.show_stdlib is False
    assert cfg.show_site_packages is False
    assert cfg.extra_hidden_paths == []


def test_collapse_message():
    cfg = FilterConfig()
    assert cfg.collapse_message(3) == "  ... 3 frame(s) hidden ..."


def test_collapse_message_custom_label():
    cfg = FilterConfig(collapse_label="[{n} hidden]")
    assert cfg.collapse_message(1) == "[1 hidden]"


def test_should_hide_matches():
    cfg = FilterConfig(extra_hidden_paths=["/vendored/", "/internal/"])
    assert cfg.should_hide("/opt/app/vendored/lib.py") is True
    assert cfg.should_hide("/opt/app/internal/util.py") is True
    assert cfg.should_hide("/opt/app/mycode.py") is False


def test_should_hide_empty():
    cfg = FilterConfig()
    assert cfg.should_hide("/any/path.py") is False


def test_max_source_width_default():
    cfg = FilterConfig()
    assert cfg.max_source_width == 120
