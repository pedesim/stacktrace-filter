"""Render a TracebackSummary as a human-readable report."""
from .summarizer import TracebackSummary
from .highlighter import highlight_exception_line


DIVIDER = "-" * 60


def render_report(summary: TracebackSummary, *, color: bool = True) -> str:
    """Return a compact report string for the given summary."""
    lines = []
    lines.append(DIVIDER)
    lines.append("Traceback Summary")
    lines.append(DIVIDER)

    exc_line = f"{summary.exception_type}: {summary.exception_msg}"
    lines.append(highlight_exception_line(exc_line) if color else exc_line)

    lines.append("")
    lines.append(
        f"Frames: {len(summary.frames)} total  "
        f"({summary.user_frame_count} user, "
        f"{summary.stdlib_frame_count} stdlib, "
        f"{summary.site_frame_count} site-package)"
    )

    if summary.deepest_user_frame:
        f = summary.deepest_user_frame
        lines.append(f"Deepest user frame: {f.filename}:{f.lineno} in {f.name}")
    else:
        lines.append("Deepest user frame: (none)")

    lines.append(DIVIDER)
    return "\n".join(lines)


def render_frame_table(summary: TracebackSummary) -> str:
    """Return a simple table of all frames with their categories."""
    lines = [f"{'#':<4} {'Category':<14} {'File':<40} {'Line':<6} {'Function'}"]
    lines.append("-" * 80)
    for i, f in enumerate(summary.frames, 1):
        fname = f.filename if len(f.filename) <= 38 else "..." + f.filename[-35:]
        lines.append(f"{i:<4} {f.category:<14} {fname:<40} {f.lineno:<6} {f.name}")
    return "\n".join(lines)
