"""Tests for annotator, locals_parser, and annotation_formatter."""
import pytest

from stacktrace_filter.parser import Frame
from stacktrace_filter.annotator import (
    AnnotatedFrame,
    annotate_frames,
    attach_note,
    render_annotated_frame,
)
from stacktrace_filter.locals_parser import extract_frame_locals
from stacktrace_filter.annotation_formatter import (
    format_annotated_traceback,
    format_locals_table,
)


def _frame(name='fn', lineno=10, filename='app.py', line='x = 1'):
    return Frame(filename=filename, lineno=lineno, name=name, line=line)


def test_annotate_frames_empty_locals():
    frames = [_frame(), _frame('bar', 20)]
    result = annotate_frames(frames)
    assert len(result) == 2
    assert all(not af.has_locals for af in result)


def test_annotate_frames_with_locals():
    frames = [_frame(), _frame('bar', 20)]
    lmap = {1: {'x': '42'}, 2: {'y': '"hello"'}}
    result = annotate_frames(frames, lmap)
    assert result[0].locals_snapshot == {'x': '42'}
    assert result[1].locals_snapshot == {'y': '"hello"'}


def test_attach_note():
    af = AnnotatedFrame(frame=_frame())
    af2 = attach_note(af, 'suspicious value')
    assert af2.note == 'suspicious value'
    assert af.note is None  # original unchanged


def test_render_annotated_frame_basic():
    af = AnnotatedFrame(frame=_frame(), locals_snapshot={'x': '1'})
    rendered = render_annotated_frame(af)
    assert 'app.py' in rendered
    assert 'x = 1' in rendered  # source line
    assert 'x = 1' in rendered  # locals (key same as line here)


def test_render_annotated_frame_note_color():
    af = AnnotatedFrame(frame=_frame(), note='check this')
    rendered = render_annotated_frame(af, color=True)
    assert 'check this' in rendered
    assert '\033[33m' in rendered


def test_extract_frame_locals_empty():
    assert extract_frame_locals('') == {}


def test_extract_frame_locals_basic():
    text = (
        'Traceback (most recent call last):\n'
        '  File "app.py", line 5, in run\n'
        '    do_thing()\n'
        '    x = 10\n'
        '    y = "hello"\n'
    )
    result = extract_frame_locals(text)
    assert result.get(1, {}).get('x') == '10'
    assert result.get(1, {}).get('y') == '"hello"'


def test_format_annotated_traceback_contains_header():
    frames = annotate_frames([_frame()])
    out = format_annotated_traceback(frames, exception_line='ValueError: bad')
    assert 'Annotated Traceback' in out
    assert 'ValueError: bad' in out


def test_format_locals_table_alignment():
    snap = {'short': '1', 'longer_key': '2'}
    table = format_locals_table(snap)
    lines = table.splitlines()
    assert len(lines) == 2
    # values should be aligned — find '=' positions
    eq_positions = [l.index('=') for l in lines]
    assert eq_positions[0] == eq_positions[1]
