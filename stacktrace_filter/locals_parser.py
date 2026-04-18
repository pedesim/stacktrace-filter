"""Parse local variable blocks that some tracebacks include."""
from __future__ import annotations

import re
from typing import Dict, List, Tuple

# Matches lines like:   varname = value
_LOCAL_RE = re.compile(r'^\s{4,}(\w+)\s*=\s*(.+)$')
_FRAME_RE = re.compile(r'^\s*File "(.+)", line (\d+), in (\w+)')


def parse_locals_block(lines: List[str]) -> Dict[int, Dict[str, str]]:
    """Parse a traceback text (as lines) and extract locals per frame index.

    Returns a dict mapping 1-based frame index to {varname: value}.
    """
    result: Dict[int, Dict[str, str]] = {}
    frame_idx = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        if _FRAME_RE.match(line):
            frame_idx += 1
            result.setdefault(frame_idx, {})
            i += 1
            # skip source line
            if i < len(lines) and not _FRAME_RE.match(lines[i]):
                i += 1
            # collect locals
            while i < len(lines):
                m = _LOCAL_RE.match(lines[i])
                if m:
                    result[frame_idx][m.group(1)] = m.group(2).strip()
                    i += 1
                else:
                    break
        else:
            i += 1
    return result


def extract_frame_locals(text: str) -> Dict[int, Dict[str, str]]:
    """Convenience wrapper accepting a full traceback string."""
    return parse_locals_block(text.splitlines())
