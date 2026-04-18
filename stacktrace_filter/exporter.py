"""Export tracebacks to structured formats (JSON, plain text)."""
from __future__ import annotations

import json
from typing import Any

from stacktrace_filter.parser import Traceback, Frame


def frame_to_dict(frame: Frame) -> dict[str, Any]:
    return {
        "filename": frame.filename,
        "lineno": frame.lineno,
        "name": frame.name,
        "line": frame.line,
    }


def traceback_to_dict(tb: Traceback) -> dict[str, Any]:
    return {
        "exception_type": tb.exc_type,
        "exception_message": tb.exc_message,
        "frames": [frame_to_dict(f) for f in tb.frames],
    }


def export_json(tb: Traceback, indent: int = 2) -> str:
    """Serialize a Traceback to a JSON string."""
    return json.dumps(traceback_to_dict(tb), indent=indent)


def export_plain(tb: Traceback) -> str:
    """Serialize a Traceback to a plain-text representation."""
    lines: list[str] = ["Traceback (most recent call last):"]
    for f in tb.frames:
        lines.append(f'  File "{f.filename}", line {f.lineno}, in {f.name}')
        if f.line:
            lines.append(f"    {f.line.strip()}")
    lines.append(f"{tb.exc_type}: {tb.exc_message}")
    return "\n".join(lines)


def export(tb: Traceback, fmt: str = "json", **kwargs: Any) -> str:
    """Export traceback in the requested format ('json' or 'plain')."""
    if fmt == "json":
        return export_json(tb, **kwargs)
    if fmt == "plain":
        return export_plain(tb)
    raise ValueError(f"Unknown export format: {fmt!r}")
