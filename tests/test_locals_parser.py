"""Focused tests for locals_parser module."""
from stacktrace_filter.locals_parser import parse_locals_block, extract_frame_locals


TRACEBACK_TWO_FRAMES = [
    'Traceback (most recent call last):',
    '  File "a.py", line 3, in outer',
    '    inner()',
    '    arg = 99',
    '  File "b.py", line 7, in inner',
    '    raise ValueError()',
    '    val = "oops"',
    'ValueError: something',
]


def test_parse_two_frames_keys():
    result = parse_locals_block(TRACEBACK_TWO_FRAMES)
    assert 1 in result
    assert 2 in result


def test_parse_first_frame_locals():
    result = parse_locals_block(TRACEBACK_TWO_FRAMES)
    assert result[1].get('arg') == '99'


def test_parse_second_frame_locals():
    result = parse_locals_block(TRACEBACK_TWO_FRAMES)
    assert result[2].get('val') == '"oops"'


def test_no_locals_frames():
    lines = [
        '  File "x.py", line 1, in f',
        '    pass',
        '  File "y.py", line 2, in g',
        '    pass',
    ]
    result = parse_locals_block(lines)
    assert result[1] == {}
    assert result[2] == {}


def test_extract_frame_locals_multiline():
    text = '\n'.join(TRACEBACK_TWO_FRAMES)
    result = extract_frame_locals(text)
    assert result[1]['arg'] == '99'
    assert result[2]['val'] == '"oops"'
