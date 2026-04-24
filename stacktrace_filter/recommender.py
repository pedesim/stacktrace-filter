"""Recommends fixes or next steps based on traceback analysis."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_filter.parser import Traceback
from stacktrace_filter.pinpointer import pinpoint, PinpointResult


_KNOWN_PATTERNS: List[tuple[str, str, str]] = [
    ("ImportError", "", "Run `pip install <missing-package>` or check your PYTHONPATH."),
    ("ModuleNotFoundError", "", "Run `pip install <missing-package>` or check your PYTHONPATH."),
    ("AttributeError", "", "Verify the object type before attribute access; check for None."),
    ("KeyError", "", "Use `.get()` with a default or guard with `if key in dict`."),
    ("IndexError", "", "Check collection length before indexing, or use try/except."),
    ("TypeError", "", "Inspect argument types; ensure function signatures match call sites."),
    ("ValueError", "", "Validate input data before passing to the function."),
    ("FileNotFoundError", "", "Confirm the file path exists; consider using `pathlib.Path`."),
    ("PermissionError", "", "Check file/directory permissions or run with elevated privileges."),
    ("RecursionError", "", "Add a base case or increase `sys.setrecursionlimit` cautiously."),
    ("MemoryError", "", "Reduce data size, use generators, or process data in chunks."),
    ("TimeoutError", "", "Increase timeout threshold or add retry logic with backoff."),
    ("ConnectionError", "", "Check network connectivity and remote service availability."),
    ("UnicodeDecodeError", "", "Specify the correct encoding (e.g. utf-8) when opening files."),
    ("ZeroDivisionError", "", "Guard divisor with a zero-check before the division."),
    ("NotImplementedError", "", "Implement the abstract method in the concrete subclass."),
    ("StopIteration", "", "Avoid raising StopIteration inside a generator; use `return`."),
    ("OverflowError", "", "Use arbitrary-precision integers or reduce numeric range."),
]

_GENERIC_ADVICE = "Review the highlighted frame and the exception message for details."


@dataclass
class Recommendation:
    exc_type: str
    message: str
    pinpointed_file: Optional[str]
    pinpointed_line: Optional[int]
    advice: str
    generic: bool = False


def _match_advice(exc_type: str, message: str) -> tuple[str, bool]:
    for pattern_type, pattern_msg, advice in _KNOWN_PATTERNS:
        type_match = exc_type == pattern_type
        msg_match = pattern_msg == "" or pattern_msg.lower() in message.lower()
        if type_match and msg_match:
            return advice, False
    return _GENERIC_ADVICE, True


def recommend(tb: Traceback) -> Recommendation:
    """Produce a Recommendation for the given Traceback."""
    exc_type = tb.exc_type or "Exception"
    exc_msg = tb.exc_message or ""
    advice, generic = _match_advice(exc_type, exc_msg)

    pin: PinpointResult = pinpoint(tb)
    pin_file: Optional[str] = None
    pin_line: Optional[int] = None
    if pin.frame is not None:
        pin_file = pin.frame.filename
        pin_line = pin.frame.lineno

    return Recommendation(
        exc_type=exc_type,
        message=exc_msg,
        pinpointed_file=pin_file,
        pinpointed_line=pin_line,
        advice=advice,
        generic=generic,
    )


def format_recommendation(rec: Recommendation, *, color: bool = True) -> str:
    """Render a Recommendation as a human-readable string."""
    lines: List[str] = []
    header = f"[Recommendation] {rec.exc_type}"
    if color:
        header = f"\033[1;33m{header}\033[0m"
    lines.append(header)
    if rec.pinpointed_file:
        loc = f"  Likely fault: {rec.pinpointed_file}:{rec.pinpointed_line}"
        if color:
            loc = f"\033[36m{loc}\033[0m"
        lines.append(loc)
    lines.append(f"  Advice: {rec.advice}")
    return "\n".join(lines)
