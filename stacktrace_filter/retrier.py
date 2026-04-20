"""Retry-policy advisor: given a traceback, suggest whether it is safe to retry."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_filter.parser import Traceback

# Exception types that are generally considered transient / safe to retry
_RETRYABLE_TYPES: frozenset[str] = frozenset(
    {
        "ConnectionError",
        "TimeoutError",
        "ConnectionResetError",
        "ConnectionRefusedError",
        "BrokenPipeError",
        "OSError",
        "IOError",
        "socket.timeout",
        "requests.exceptions.Timeout",
        "requests.exceptions.ConnectionError",
        "urllib3.exceptions.ReadTimeoutError",
        "http.client.RemoteDisconnected",
    }
)

# Exception types that are never safe to retry
_FATAL_TYPES: frozenset[str] = frozenset(
    {
        "SystemExit",
        "KeyboardInterrupt",
        "MemoryError",
        "RecursionError",
    }
)


@dataclass
class RetryAdvice:
    exc_type: str
    retryable: bool
    fatal: bool
    reason: str
    suggested_delay_s: float = 1.0
    matched_rule: Optional[str] = None


@dataclass
class RetrierConfig:
    extra_retryable: List[str] = field(default_factory=list)
    extra_fatal: List[str] = field(default_factory=list)
    default_delay_s: float = 1.0


def _exc_type(tb: Traceback) -> str:
    parts = tb.exception_line.split(":", 1)
    return parts[0].strip()


def advise(tb: Traceback, config: Optional[RetrierConfig] = None) -> RetryAdvice:
    """Return a RetryAdvice for the given traceback."""
    cfg = config or RetrierConfig()
    etype = _exc_type(tb)

    fatal_set = _FATAL_TYPES | frozenset(cfg.extra_fatal)
    retryable_set = _RETRYABLE_TYPES | frozenset(cfg.extra_retryable)

    if etype in fatal_set:
        return RetryAdvice(
            exc_type=etype,
            retryable=False,
            fatal=True,
            reason=f"{etype!r} is a fatal exception type; do not retry.",
            suggested_delay_s=0.0,
            matched_rule="fatal_list",
        )

    if etype in retryable_set:
        return RetryAdvice(
            exc_type=etype,
            retryable=True,
            fatal=False,
            reason=f"{etype!r} is a known transient exception; retry is safe.",
            suggested_delay_s=cfg.default_delay_s,
            matched_rule="retryable_list",
        )

    return RetryAdvice(
        exc_type=etype,
        retryable=False,
        fatal=False,
        reason=f"{etype!r} is not recognised as retryable; manual review recommended.",
        suggested_delay_s=0.0,
        matched_rule=None,
    )


def format_advice(advice: RetryAdvice) -> str:
    verdict = "RETRYABLE" if advice.retryable else ("FATAL" if advice.fatal else "UNKNOWN")
    lines = [
        f"Exception : {advice.exc_type}",
        f"Verdict   : {verdict}",
        f"Reason    : {advice.reason}",
    ]
    if advice.retryable:
        lines.append(f"Delay (s) : {advice.suggested_delay_s}")
    return "\n".join(lines)
