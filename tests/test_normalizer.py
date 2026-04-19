"""Tests for stacktrace_filter.normalizer."""
import pytest
from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.normalizer import (
    normalize,
    normalize_frame,
    _normalize_message,
    _normalize_filename,
    NormalizedTraceback,
    NormalizedFrame,
)


def _frame(filename='/home/user/project/app.py', lineno=10, name='run', line='  x = 1'):
    return Frame(filename=filename, lineno=lineno, name=name, line=line)


def _tb(frames=None, exc_type='ValueError', exc_message='bad value'):
    return Traceback(frames=frames or [_frame()], exc_type=exc_type, exc_message=exc_message)


def test_normalize_returns_normalized_traceback():
    result = normalize(_tb())
    assert isinstance(result, NormalizedTraceback)


def test_normalize_frame_returns_normalized_frame():
    result = normalize_frame(_frame())
    assert isinstance(result, NormalizedFrame)


def test_normalize_message_strips_memory_address():
    msg = 'object at 0x7f3a1b2c3d4e failed'
    result = _normalize_message(msg)
    assert '0x' not in result
    assert '<addr>' in result


def test_normalize_message_strips_ansi():
    msg = '\x1b[31merror\x1b[0m occurred'
    result = _normalize_message(msg)
    assert '\x1b' not in result
    assert 'error occurred' == result


def test_normalize_filename_site_packages():
    fn = '/usr/lib/python3.11/site-packages/requests/api.py'
    result = _normalize_filename(fn)
    assert result.startswith('site-packages/')


def test_normalize_filename_stdlib():
    fn = '/usr/lib/python3.11/json/decoder.py'
    result = _normalize_filename(fn)
    assert result.startswith('<stdlib>/')


def test_normalize_filename_project_unchanged():
    fn = '/home/user/project/app.py'
    result = _normalize_filename(fn)
    assert result == fn


def test_normalize_frame_line_stripped():
    f = _frame(line='    x = 1   ')
    result = normalize_frame(f)
    assert result.line == 'x = 1'


def test_normalize_exc_type_preserved():
    result = normalize(_tb(exc_type='RuntimeError'))
    assert result.exc_type == 'RuntimeError'


def test_normalize_frame_count():
    frames = [_frame(lineno=i) for i in range(5)]
    result = normalize(_tb(frames=frames))
    assert len(result.frames) == 5


def test_normalize_none_exc_type():
    tb = _tb(exc_type=None, exc_message=None)
    result = normalize(tb)
    assert result.exc_type == ''
    assert result.exc_message == ''
