"""Archive tracebacks to newline-delimited JSON for later analysis."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator

from stacktrace_filter.exporter import traceback_to_dict
from stacktrace_filter.parser import Traceback


@dataclass
class ArchiveEntry:
    traceback: Traceback
    timestamp: float = field(default_factory=time.time)
    label: str = ""


def entry_to_dict(entry: ArchiveEntry) -> dict:
    return {
        "timestamp": entry.timestamp,
        "label": entry.label,
        "traceback": traceback_to_dict(entry.traceback),
    }


def append_entry(path: Path, entry: ArchiveEntry) -> None:
    """Append a single entry to an NDJSON archive file."""
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry_to_dict(entry)) + "\n")


def load_archive(path: Path) -> Iterator[ArchiveEntry]:
    """Yield ArchiveEntry objects from an NDJSON archive file."""
    from stacktrace_filter.parser import Frame, Traceback as TB

    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            tb_raw = raw["traceback"]
            frames = [
                Frame(
                    filename=f["filename"],
                    lineno=f["lineno"],
                    function=f["function"],
                    source=f.get("source", ""),
                )
                for f in tb_raw.get("frames", [])
            ]
            tb = TB(frames=frames, exception=tb_raw.get("exception", ""))
            yield ArchiveEntry(
                traceback=tb,
                timestamp=raw.get("timestamp", 0.0),
                label=raw.get("label", ""),
            )


def archive_many(path: Path, entries: Iterable[ArchiveEntry]) -> int:
    """Append multiple entries; return count written."""
    count = 0
    for entry in entries:
        append_entry(path, entry)
        count += 1
    return count
