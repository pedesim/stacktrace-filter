"""Baseline comparison: capture a reference traceback set and detect regressions."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .fingerprint import Fingerprint, fingerprint
from .parser import Traceback


@dataclass
class BaselineEntry:
    fp: str
    short: str
    exc_type: str
    exc_message: str
    frame_count: int


@dataclass
class BaselineReport:
    new: List[Fingerprint] = field(default_factory=list)
    resolved: List[str] = field(default_factory=list)
    persisted: List[str] = field(default_factory=list)

    @property
    def regression_count(self) -> int:
        return len(self.new)

    @property
    def resolved_count(self) -> int:
        return len(self.resolved)


def _entry_from_tb(tb: Traceback) -> BaselineEntry:
    fp = fingerprint(tb)
    return BaselineEntry(
        fp=fp.full,
        short=fp.short,
        exc_type=tb.exc_type or "",
        exc_message=tb.exc_message or "",
        frame_count=len(tb.frames),
    )


def save_baseline(tracebacks: List[Traceback], path: Path) -> None:
    entries = [_entry_from_tb(tb) for tb in tracebacks]
    data = [
        {
            "fp": e.fp,
            "short": e.short,
            "exc_type": e.exc_type,
            "exc_message": e.exc_message,
            "frame_count": e.frame_count,
        }
        for e in entries
    ]
    path.write_text(json.dumps(data, indent=2))


def load_baseline(path: Path) -> Dict[str, BaselineEntry]:
    raw = json.loads(path.read_text())
    return {
        item["fp"]: BaselineEntry(**item)
        for item in raw
    }


def compare_to_baseline(
    tracebacks: List[Traceback],
    baseline: Dict[str, BaselineEntry],
) -> BaselineReport:
    current_fps = {fingerprint(tb).full for tb in tracebacks}
    baseline_fps = set(baseline.keys())

    new_fps = current_fps - baseline_fps
    resolved_fps = baseline_fps - current_fps
    persisted_fps = current_fps & baseline_fps

    new_fingerprints = [fingerprint(tb) for tb in tracebacks if fingerprint(tb).full in new_fps]

    return BaselineReport(
        new=new_fingerprints,
        resolved=sorted(resolved_fps),
        persisted=sorted(persisted_fps),
    )
