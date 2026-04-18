"""Tests for stacktrace_filter.watchdog."""
from __future__ import annotations

import textwrap
from stacktrace_filter.watchdog import _extract_tracebacks, _collect_block


SIMPLE_TB = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app.py", line 10, in run
        do_thing()
      File "lib.py", line 5, in do_thing
        raise ValueError("oops")
    ValueError: oops
""")


def test_extract_single_traceback():
    blocks = _extract_tracebacks(SIMPLE_TB)
    assert len(blocks) == 1
    assert "ValueError: oops" in blocks[0]


def test_extract_no_traceback():
    text = "INFO starting server\nINFO ready\n"
    assert _extract_tracebacks(text) == []


def test_extract_multiple_tracebacks():
    double = SIMPLE_TB + "\nsome log line\n" + SIMPLE_TB
    blocks = _extract_tracebacks(double)
    assert len(blocks) == 2


def test_extract_preserves_exception_line():
    blocks = _extract_tracebacks(SIMPLE_TB)
    assert blocks[0].strip().endswith("ValueError: oops")


def test_collect_block_returns_next_index():
    lines = SIMPLE_TB.splitlines(keepends=True)
    # find the header
    start = next(i for i, l in enumerate(lines) if "Traceback" in l)
    block, nxt = _collect_block(lines, start)
    assert nxt > start
    assert any("ValueError" in l for l in block)


def test_extract_traceback_with_surrounding_text():
    text = "INFO ok\n" + SIMPLE_TB + "INFO done\n"
    blocks = _extract_tracebacks(text)
    assert len(blocks) == 1


def test_watch_calls_output(tmp_path):
    """watch() should call output for each traceback found in new content."""
    import threading
    from stacktrace_filter.watchdog import watch

    log_file = tmp_path / "app.log"
    log_file.write_text("")  # create empty

    collected: list[str] = []

    def _stop_after_one(text: str) -> None:
        collected.append(text)
        raise KeyboardInterrupt  # stop the watch loop

    def _writer():
        import time
        time.sleep(0.2)
        log_file.write_text(SIMPLE_TB)

    t = threading.Thread(target=_writer, daemon=True)
    t.start()

    try:
        watch(log_file, poll_interval=0.05, output=_stop_after_one, color=False)
    except KeyboardInterrupt:
        pass

    assert len(collected) == 1
    assert "ValueError" in collected[0]
