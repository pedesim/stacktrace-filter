"""Snapshot: capture and compare traceback sets at two points in time."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional

from .parser import Traceback
from .exporter import traceback_to_dict


@dataclass
class Snapshot:
    label: str
    timestamp: float
    tracebacks: List[Traceback]
    metadata: dict = field(default_factory=dict)


def take_snapshot(tracebacks: List[Traceback], label: str = "", **meta) -> Snapshot:
    """Capture a snapshot of the current traceback list."""
    return Snapshot(
        label=label or f"snapshot-{int(time.time())}",
        timestamp=time.time(),
        tracebacks=list(tracebacks),
        metadata=meta,
    )


@dataclass
class SnapshotDiff:
    added: List[Traceback]
    removed: List[Traceback]
    unchanged_count: int
    elapsed: float


def _tb_key(tb: Traceback) -> tuple:
    return (tb.exc_type, tb.exc_message, tuple((f.filename, f.lineno) for f in tb.frames))


def diff_snapshots(before: Snapshot, after: Snapshot) -> SnapshotDiff:
    """Return tracebacks added/removed between two snapshots."""
    before_keys = {_tb_key(tb): tb for tb in before.tracebacks}
    after_keys = {_tb_key(tb): tb for tb in after.tracebacks}

    added = [after_keys[k] for k in after_keys if k not in before_keys]
    removed = [before_keys[k] for k in before_keys if k not in after_keys]
    unchanged = len([k for k in after_keys if k in before_keys])

    return SnapshotDiff(
        added=added,
        removed=removed,
        unchanged_count=unchanged,
        elapsed=after.timestamp - before.timestamp,
    )


def format_snapshot_diff(diff: SnapshotDiff, color: bool = True) -> str:
    """Render a human-readable summary of a snapshot diff."""
    green = "\033[32m" if color else ""
    red = "\033[31m" if color else ""
    reset = "\033[0m" if color else ""

    lines = [
        f"Snapshot diff (elapsed: {diff.elapsed:.2f}s)",
        f"  {green}+{len(diff.added)} added{reset}",
        f"  {red}-{len(diff.removed)} removed{reset}",
        f"  {diff.unchanged_count} unchanged",
    ]
    for tb in diff.added:
        lines.append(f"  {green}+ {tb.exc_type}: {tb.exc_message}{reset}")
    for tb in diff.removed:
        lines.append(f"  {red}- {tb.exc_type}: {tb.exc_message}{reset}")
    return "\n".join(lines)
