"""Assign severity levels to tracebacks based on exception type and content."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
from stacktrace_filter.parser import Traceback

LEVEL_CRITICAL = "CRITICAL"
LEVEL_ERROR = "ERROR"
LEVEL_WARNING = "WARNING"
LEVEL_INFO = "INFO"

_CRITICAL_EXC = {"SystemExit", "MemoryError", "KeyboardInterrupt", "SystemError"}
_WARNING_EXC = {"DeprecationWarning", "UserWarning", "ResourceWarning", "FutureWarning"}


@dataclass
class SeverityResult:
    level: str
    reason: str
    score: int


def _exc_type(tb: Traceback) -> Optional[str]:
    if not tb.exception_line:
        return None
    return tb.exception_line.split(":")[0].strip().split(".")[-1]


def classify(tb: Traceback, critical_keywords: Optional[List[str]] = None) -> SeverityResult:
    """Return a SeverityResult for the given traceback."""
    exc = _exc_type(tb)
    keywords = critical_keywords or []

    if exc in _CRITICAL_EXC:
        return SeverityResult(LEVEL_CRITICAL, f"exception type {exc!r} is critical", 100)

    exc_line = tb.exception_line or ""
    for kw in keywords:
        if kw.lower() in exc_line.lower():
            return SeverityResult(LEVEL_CRITICAL, f"keyword {kw!r} found in exception", 90)

    if exc in _WARNING_EXC:
        return SeverityResult(LEVEL_WARNING, f"exception type {exc!r} is a warning", 30)

    if exc and exc.endswith("Error"):
        return SeverityResult(LEVEL_ERROR, f"exception type {exc!r} is an error", 60)

    if exc and exc.endswith("Exception"):
        return SeverityResult(LEVEL_ERROR, f"exception type {exc!r} is an exception", 50)

    return SeverityResult(LEVEL_INFO, "no specific severity detected", 10)


def format_severity(result: SeverityResult, color: bool = True) -> str:
    _colors = {
        LEVEL_CRITICAL: "\033[1;31m",
        LEVEL_ERROR: "\033[0;31m",
        LEVEL_WARNING: "\033[0;33m",
        LEVEL_INFO: "\033[0;34m",
    }
    reset = "\033[0m"
    label = f"[{result.level}]"
    if color:
        label = f"{_colors.get(result.level, '')}{label}{reset}"
    return f"{label} {result.reason} (score={result.score})"
