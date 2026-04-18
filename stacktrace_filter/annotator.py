"""Annotate frames with local variable snapshots from tracebacks."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .parser import Frame


@dataclass
class AnnotatedFrame:
    frame: Frame
    locals_snapshot: Dict[str, str] = field(default_factory=dict)
    note: Optional[str] = None

    @property
    def has_locals(self) -> bool:
        return bool(self.locals_snapshot)


def annotate_frames(
    frames: List[Frame],
    locals_map: Optional[Dict[int, Dict[str, str]]] = None,
) -> List[AnnotatedFrame]:
    """Wrap frames with optional locals snapshots keyed by 1-based frame index."""
    locals_map = locals_map or {}
    result = []
    for idx, frame in enumerate(frames, start=1):
        snapshot = locals_map.get(idx, {})
        result.append(AnnotatedFrame(frame=frame, locals_snapshot=snapshot))
    return result


def attach_note(annotated: AnnotatedFrame, note: str) -> AnnotatedFrame:
    """Return a copy of the annotated frame with a note attached."""
    return AnnotatedFrame(
        frame=annotated.frame,
        locals_snapshot=dict(annotated.locals_snapshot),
        note=note,
    )


def render_annotated_frame(af: AnnotatedFrame, color: bool = False) -> str:
    """Render an annotated frame as a string, including locals and notes."""
    lines = []
    loc = af.frame
    lines.append(f'  File "{loc.filename}", line {loc.lineno}, in {loc.name}')
    if loc.line:
        lines.append(f'    {loc.line}')
    if af.locals_snapshot:
        lines.append('    # locals:')
        for k, v in af.locals_snapshot.items():
            lines.append(f'      {k} = {v}')
    if af.note:
        prefix = '\033[33m' if color else ''
        suffix = '\033[0m' if color else ''
        lines.append(f'    {prefix}# note: {af.note}{suffix}')
    return '\n'.join(lines)
