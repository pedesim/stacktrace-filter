"""Parse raw Python tracebacks into structured frames."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

_FRAME_RE = re.compile(r'^  File "(?P<path>.+)", line (?P<lineno>\d+), in (?P<func>.+)$')
_CODE_RE = re.compile(r'^    (?P<code>.+)$')
_EXC_RE = re.compile(r'^(?P<exc>[A-Za-z][\w.]*(?:Error|Exception|Warning|KeyboardInterrupt|SystemExit|StopIteration)[:\w ]*).*$')


@dataclass
class Frame:
    path: str
    lineno: int
    func: str
    code: Optional[str] = None

    @property
    def is_stdlib(self) -> bool:
        return '/lib/python' in self.path or 'site-packages' in self.path

    @property
    def is_site_package(self) -> bool:
        return 'site-packages' in self.path


@dataclass
class Traceback:
    frames: List[Frame] = field(default_factory=list)
    exception: Optional[str] = None
    message: Optional[str] = None


def parse(text: str) -> Traceback:
    """Parse a traceback string into a Traceback object."""
    tb = Traceback()
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        frame_match = _FRAME_RE.match(line)
        if frame_match:
            frame = Frame(
                path=frame_match.group('path'),
                lineno=int(frame_match.group('lineno')),
                func=frame_match.group('func'),
            )
            if i + 1 < len(lines):
                code_match = _CODE_RE.match(lines[i + 1])
                if code_match:
                    frame.code = code_match.group('code')
                    i += 1
            tb.frames.append(frame)
        else:
            exc_match = _EXC_RE.match(line)
            if exc_match:
                parts = line.split(':', 1)
                tb.exception = parts[0].strip()
                tb.message = parts[1].strip() if len(parts) > 1 else None
        i += 1
    return tb
