"""Helpers for reading traceback text from various sources."""

from __future__ import annotations

import io
import sys
from pathlib import Path
from typing import Union


TextSource = Union[str, Path, io.TextIOBase, None]


def read_source(source: TextSource = None) -> str:
    """Read traceback text from *source*.

    Parameters
    ----------
    source:
        - ``None`` or ``"-"``  → read from *stdin*
        - :class:`pathlib.Path` or a plain string path → read from file
        - an open :class:`io.TextIOBase` stream → read from stream
    """
    if source is None or source == "-":
        return sys.stdin.read()

    if isinstance(source, (str, Path)):
        return Path(source).read_text(encoding="utf-8", errors="replace")

    if isinstance(source, io.IOBase):
        return source.read()

    raise TypeError(f"Unsupported source type: {type(source)!r}")


def detect_encoding(raw: bytes) -> str:
    """Best-effort detection of a traceback file's encoding."""
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            raw.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
    return "utf-8"


def read_bytes_source(path: Path) -> str:
    """Read *path* as bytes and decode with :func:`detect_encoding`."""
    raw = path.read_bytes()
    enc = detect_encoding(raw)
    return raw.decode(enc, errors="replace")
