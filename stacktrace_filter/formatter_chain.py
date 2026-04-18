"""Formatting support for chained tracebacks."""
from typing import List
from stacktrace_filter.chain import ChainedTraceback, CHAINED_CAUSE_HEADER
from stacktrace_filter.formatter import format_traceback
from stacktrace_filter.config import FilterConfig


_CAUSE_COLOR = "\033[35m"   # magenta
_RESET = "\033[0m"


def _format_link(header: str, color: bool) -> str:
    line = f"\n{header}\n"
    if color:
        line = f"\n{_CAUSE_COLOR}{header}{_RESET}\n"
    return line


def format_chained(
    chain: ChainedTraceback,
    config: FilterConfig,
    color: bool = True,
) -> str:
    """Render a ChainedTraceback to a single string."""
    parts: List[str] = []

    for i, tb in enumerate(chain.tracebacks):
        if i > 0 and (i - 1) < len(chain.links):
            parts.append(_format_link(chain.links[i - 1], color=color))
        parts.append(format_traceback(tb, config=config, color=color))

    return "".join(parts)


def count_chained(chain: ChainedTraceback) -> int:
    """Return number of tracebacks in the chain."""
    return len(chain.tracebacks)


def has_cause(chain: ChainedTraceback) -> bool:
    """Return True if any link is a direct cause (raise X from Y)."""
    return any(link == CHAINED_CAUSE_HEADER for link in chain.links)
