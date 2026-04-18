"""Tests for chained exception parsing."""
import textwrap
import pytest
from stacktrace_filter.chain import (
    split_chained,
    parse_chained,
    CHAINED_CAUSE_HEADER,
    CHAINED_CONTEXT_HEADER,
    ChainedTraceback,
)


SIMPLE_TB = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app.py", line 5, in run
        risky()
    ValueError: something went wrong
""")

SECOND_TB = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app.py", line 12, in main
        run()
    RuntimeError: wrapped error
""")


def test_split_single():
    parts = split_chained(SIMPLE_TB)
    assert len(parts) == 1
    assert parts[0][0] is None


def test_split_chained_cause():
    text = SIMPLE_TB + "\n" + CHAINED_CAUSE_HEADER + "\n\n" + SECOND_TB
    parts = split_chained(text)
    assert len(parts) == 2
    assert parts[0][0] is None
    assert parts[1][0] == CHAINED_CAUSE_HEADER


def test_split_chained_context():
    text = SIMPLE_TB + "\n" + CHAINED_CONTEXT_HEADER + "\n\n" + SECOND_TB
    parts = split_chained(text)
    assert len(parts) == 2
    assert parts[1][0] == CHAINED_CONTEXT_HEADER


def test_parse_chained_single():
    chain = parse_chained(SIMPLE_TB)
    assert isinstance(chain, ChainedTraceback)
    assert len(chain.tracebacks) == 1
    assert len(chain.links) == 0


def test_parse_chained_two():
    text = SIMPLE_TB + "\n" + CHAINED_CAUSE_HEADER + "\n\n" + SECOND_TB
    chain = parse_chained(text)
    assert len(chain.tracebacks) == 2
    assert len(chain.links) == 1
    assert chain.links[0] == CHAINED_CAUSE_HEADER


def test_parse_chained_exception_types():
    text = SIMPLE_TB + "\n" + CHAINED_CAUSE_HEADER + "\n\n" + SECOND_TB
    chain = parse_chained(text)
    assert chain.tracebacks[0].exc_type == "ValueError"
    assert chain.tracebacks[1].exc_type == "RuntimeError"
