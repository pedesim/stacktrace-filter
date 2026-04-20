"""Flatten chained tracebacks into a single frame list with source labels."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .parser import Frame, Traceback
from .chain import ChainedTraceback


@dataclass
class LabeledFrame:
    frame: Frame
    chain_index: int
    label: str  # 'cause', 'context', or 'origin'


@dataclass
class FlattenedTraceback:
    frames: List[LabeledFrame]
    exception_lines: List[str]
    chain_labels: List[str]

    @property
    def total_frames(self) -> int:
        return len(self.frames)

    def frames_for_chain(self, index: int) -> List[LabeledFrame]:
        return [f for f in self.frames if f.chain_index == index]


def _chain_label(index: int, total: int, chained: ChainedTraceback) -> str:
    if index == total - 1:
        return "origin"
    tb = chained.tracebacks[index]
    cause = getattr(tb, "cause", None)
    context = getattr(tb, "context", None)
    if cause:
        return "cause"
    if context:
        return "context"
    return f"chain[{index}]"


def flatten(chained: ChainedTraceback) -> FlattenedTraceback:
    """Flatten a ChainedTraceback into a single ordered list of LabeledFrames."""
    all_frames: List[LabeledFrame] = []
    exception_lines: List[str] = []
    chain_labels: List[str] = []

    total = len(chained.tracebacks)
    for idx, tb in enumerate(chained.tracebacks):
        label = _chain_label(idx, total, chained)
        chain_labels.append(label)
        for frame in tb.frames:
            all_frames.append(LabeledFrame(frame=frame, chain_index=idx, label=label))
        if tb.exception_line:
            exception_lines.append(tb.exception_line)

    return FlattenedTraceback(
        frames=all_frames,
        exception_lines=exception_lines,
        chain_labels=chain_labels,
    )


def format_flattened(ft: FlattenedTraceback, color: bool = True) -> str:
    lines: List[str] = []
    current_chain = -1
    for lf in ft.frames:
        if lf.chain_index != current_chain:
            current_chain = lf.chain_index
            label = ft.chain_labels[lf.chain_index]
            header = f"[{label}]" if not color else f"\033[33m[{label}]\033[0m"
            lines.append(header)
        f = lf.frame
        lines.append(f"  File \"{f.filename}\", line {f.lineno}, in {f.name}")
        if f.line:
            lines.append(f"    {f.line}")
    for exc in ft.exception_lines:
        lines.append(exc)
    return "\n".join(lines)
