"""Traceback fingerprinting: produce a stable hash for a traceback."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import List, Optional

from .parser import Traceback, Frame


@dataclass
class Fingerprint:
    hex: str
    exc_type: str
    frame_keys: List[str]

    def short(self, length: int = 8) -> str:
        return self.hex[:length]


def _frame_key(frame: Frame) -> str:
    """Stable string key for a single frame."""
    return f"{frame.filename}:{frame.lineno}:{frame.name}"


def _exc_type(tb: Traceback) -> str:
    if tb.exception_line:
        return tb.exception_line.split(":")[0].strip()
    return "UnknownError"


def fingerprint(tb: Traceback, include_line_numbers: bool = True) -> Fingerprint:
    """Return a deterministic Fingerprint for *tb*.

    When *include_line_numbers* is False the hash ignores line numbers,
    making it robust to minor code edits.
    """
    exc = _exc_type(tb)
    keys: List[str] = []
    for frame in tb.frames:
        if include_line_numbers:
            keys.append(_frame_key(frame))
        else:
            keys.append(f"{frame.filename}:{frame.name}")

    raw = exc + "|".join(keys)
    hex_digest = hashlib.sha256(raw.encode()).hexdigest()
    return Fingerprint(hex=hex_digest, exc_type=exc, frame_keys=keys)


def fingerprint_group(tracebacks: List[Traceback], **kwargs) -> List[Fingerprint]:
    """Return a fingerprint for each traceback in *tracebacks*."""
    return [fingerprint(tb, **kwargs) for tb in tracebacks]


def are_similar(a: Traceback, b: Traceback, include_line_numbers: bool = True) -> bool:
    """Return True if *a* and *b* share the same fingerprint."""
    return (
        fingerprint(a, include_line_numbers=include_line_numbers).hex
        == fingerprint(b, include_line_numbers=include_line_numbers).hex
    )
