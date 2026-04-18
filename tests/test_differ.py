import pytest
from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.differ import diff_tracebacks, format_diff, DiffResult


def _frame(filename, lineno, line="pass", func="fn"):
    return Frame(filename=filename, lineno=lineno, func=func, line=line)


def _tb(*frames):
    return Traceback(frames=list(frames), exc_type="E", exc_msg="m")


def test_identical_tracebacks():
    f = _frame("a.py", 1)
    result = diff_tracebacks(_tb(f), _tb(f))
    assert result.common == [f]
    assert result.only_in_left == []
    assert result.only_in_right == []
    assert result.changed == []


def test_only_in_left():
    f1 = _frame("a.py", 1)
    f2 = _frame("b.py", 2)
    result = diff_tracebacks(_tb(f1, f2), _tb(f1))
    assert len(result.only_in_left) == 1
    assert result.only_in_left[0].filename == "b.py"


def test_only_in_right():
    f1 = _frame("a.py", 1)
    f2 = _frame("c.py", 3)
    result = diff_tracebacks(_tb(f1), _tb(f1, f2))
    assert len(result.only_in_right) == 1
    assert result.only_in_right[0].filename == "c.py"


def test_changed_frame():
    f_left = _frame("a.py", 5, line="x = 1")
    f_right = _frame("a.py", 5, line="x = 2")
    result = diff_tracebacks(_tb(f_left), _tb(f_right))
    assert len(result.changed) == 1
    lf, rf = result.changed[0]
    assert lf.line == "x = 1"
    assert rf.line == "x = 2"


def test_format_diff_identical_no_color():
    f = _frame("a.py", 1)
    result = diff_tracebacks(_tb(f), _tb(f))
    out = format_diff(result, color=False)
    assert "identical" in out.lower()


def test_format_diff_shows_removed(capsys):
    f1 = _frame("a.py", 1)
    f2 = _frame("b.py", 2)
    result = diff_tracebacks(_tb(f1, f2), _tb(f1))
    out = format_diff(result, color=False)
    assert "b.py" in out
    assert out.startswith("-")


def test_format_diff_shows_added():
    f1 = _frame("a.py", 1)
    f2 = _frame("d.py", 4)
    result = diff_tracebacks(_tb(f1), _tb(f1, f2))
    out = format_diff(result, color=False)
    assert "+" in out
    assert "d.py" in out
