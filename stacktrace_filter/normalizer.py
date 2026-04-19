"""Normalize tracebacks for consistent comparison and storage."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from .parser import Traceback, Frame

_MEMORY_ADDR = re.compile(r'0x[0-9a-fA-F]+')
_ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')
_ABS_PATH = re.compile(r'^/.+/site-packages/')


@dataclass
class NormalizedFrame:
    filename: str
    lineno: int
    name: str
    line: str


@dataclass
class NormalizedTraceback:
    frames: List[NormalizedFrame]
    exc_type: str
    exc_message: str


def _strip_ansi(text: str) -> str:
    return _ANSI_ESCAPE.sub('', text)


def _normalize_message(msg: str) -> str:
    msg = _strip_ansi(msg)
    msg = _MEMORY_ADDR.sub('<addr>', msg)
    return msg.strip()


def _normalize_filename(filename: str) -> str:
    filename = _ABS_PATH.sub('site-packages/', filename)
    filename = re.sub(r'^/.+/lib/python[^/]+/', '<stdlib>/', filename)
    return filename


def _normalize_line(line: str) -> str:
    if line is None:
        return ''
    return _strip_ansi(line).strip()


def normalize_frame(frame: Frame) -> NormalizedFrame:
    return NormalizedFrame(
        filename=_normalize_filename(frame.filename),
        lineno=frame.lineno,
        name=frame.name,
        line=_normalize_line(frame.line),
    )


def normalize(tb: Traceback) -> NormalizedTraceback:
    return NormalizedTraceback(
        frames=[normalize_frame(f) for f in tb.frames],
        exc_type=tb.exc_type or '',
        exc_message=_normalize_message(tb.exc_message or ''),
    )
