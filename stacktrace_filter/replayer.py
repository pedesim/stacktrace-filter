"""Replay archived tracebacks through the filter pipeline with optional delay."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Iterable, Iterator, List, Optional

from stacktrace_filter.archiver import ArchiveEntry, load_archive
from stacktrace_filter.parser import Traceback


@dataclass
class ReplayConfig:
    delay: float = 0.0          # seconds between emissions
    max_entries: Optional[int] = None
    reverse: bool = False
    filter_label: Optional[str] = None


@dataclass
class ReplayResult:
    entries: List[ArchiveEntry] = field(default_factory=list)
    skipped: int = 0

    @property
    def total(self) -> int:
        return len(self.entries)


def _apply_filter(entries: List[ArchiveEntry], label: Optional[str]) -> tuple[List[ArchiveEntry], int]:
    if label is None:
        return entries, 0
    kept = [e for e in entries if e.label == label]
    return kept, len(entries) - len(kept)


def replay(
    path: str,
    config: Optional[ReplayConfig] = None,
    callback: Optional[Callable[[ArchiveEntry], None]] = None,
) -> ReplayResult:
    """Load archive at *path* and replay entries according to *config*."""
    if config is None:
        config = ReplayConfig()

    entries = load_archive(path)

    entries, skipped = _apply_filter(entries, config.filter_label)

    if config.reverse:
        entries = list(reversed(entries))

    if config.max_entries is not None:
        entries = entries[: config.max_entries]

    result = ReplayResult(skipped=skipped)

    for entry in entries:
        result.entries.append(entry)
        if callback is not None:
            callback(entry)
        if config.delay > 0:
            time.sleep(config.delay)

    return result


def iter_replay(
    path: str,
    config: Optional[ReplayConfig] = None,
) -> Iterator[ArchiveEntry]:
    """Yield entries one at a time (lazy variant of replay)."""
    if config is None:
        config = ReplayConfig()

    entries = load_archive(path)
    entries, _ = _apply_filter(entries, config.filter_label)

    if config.reverse:
        entries = list(reversed(entries))

    if config.max_entries is not None:
        entries = entries[: config.max_entries]

    for entry in entries:
        yield entry
        if config.delay > 0:
            time.sleep(config.delay)
