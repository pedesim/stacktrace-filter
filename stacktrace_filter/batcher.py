"""Batch tracebacks into fixed-size or time-keyed groups."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Iterator
from stacktrace_filter.parser import Traceback


@dataclass
class Batch:
    index: int
    entries: List[Traceback] = field(default_factory=list)

    @property
    def size(self) -> int:
        return len(self.entries)


@dataclass
class BatchResult:
    batches: List[Batch] = field(default_factory=list)

    @property
    def total(self) -> int:
        return sum(b.size for b in self.batches)

    @property
    def batch_count(self) -> int:
        return len(self.batches)


def batch_tracebacks(tracebacks: List[Traceback], batch_size: int) -> BatchResult:
    """Split tracebacks into batches of at most batch_size."""
    if batch_size < 1:
        raise ValueError("batch_size must be >= 1")
    result = BatchResult()
    for i, start in enumerate(range(0, len(tracebacks), batch_size)):
        chunk = tracebacks[start:start + batch_size]
        result.batches.append(Batch(index=i, entries=chunk))
    return result


def iter_batches(tracebacks: List[Traceback], batch_size: int) -> Iterator[Batch]:
    """Yield Batch objects one at a time."""
    for batch in batch_tracebacks(tracebacks, batch_size).batches:
        yield batch


def format_batch_result(result: BatchResult) -> str:
    lines = [
        f"Batches   : {result.batch_count}",
        f"Total     : {result.total}",
    ]
    for b in result.batches:
        lines.append(f"  Batch {b.index}: {b.size} traceback(s)")
    return "\n".join(lines)
