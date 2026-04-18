"""Optional post-processing plugin interface for the summarizer pipeline."""
from typing import Callable, List
from .summarizer import TracebackSummary

Plugin = Callable[[TracebackSummary], TracebackSummary]

_registry: List[Plugin] = []


def register(fn: Plugin) -> Plugin:
    """Decorator to register a plugin function."""
    _registry.append(fn)
    return fn


def apply_plugins(summary: TracebackSummary) -> TracebackSummary:
    """Apply all registered plugins in order."""
    for plugin in _registry:
        summary = plugin(summary)
    return summary


def clear_plugins() -> None:
    """Remove all registered plugins (useful in tests)."""
    _registry.clear()


# Built-in plugin: cap deepest_user_frame message length
@register
def _truncate_exc_msg(summary: TracebackSummary) -> TracebackSummary:
    max_len = 200
    if len(summary.exception_msg) > max_len:
        summary.exception_msg = summary.exception_msg[:max_len] + "..."
    return summary
