"""Deduplication of repeated frames in tracebacks."""
from dataclasses import dataclass, field
from typing import List, Tuple
from stacktrace_filter.parser import Frame


@dataclass
class DeduplicatedGroup:
    frame: Frame
    count: int = 1


def deduplicate_frames(frames: List[Frame]) -> List[DeduplicatedGroup]:
    """Collapse consecutive identical frames into groups with a repeat count."""
    if not frames:
        return []

    groups: List[DeduplicatedGroup] = []
    current = DeduplicatedGroup(frame=frames[0], count=1)

    for frame in frames[1:]:
        if _frames_equal(frame, current.frame):
            current.count += 1
        else:
            groups.append(current)
            current = DeduplicatedGroup(frame=frame, count=1)

    groups.append(current)
    return groups


def _frames_equal(a: Frame, b: Frame) -> bool:
    return a.filename == b.filename and a.lineno == b.lineno and a.name == b.name


def render_dedup_groups(groups: List[DeduplicatedGroup], color: bool = True) -> List[str]:
    """Render deduplicated groups to lines, annotating repeated frames."""
    from stacktrace_filter.formatter import format_frame
    lines = []
    for group in groups:
        line = format_frame(group.frame, color=color)
        if group.count > 1:
            suffix = f"  [repeated {group.count}x]"
            if color:
                suffix = f"\033[33m{suffix}\033[0m"
            line = line.rstrip() + suffix
        lines.append(line)
    return lines
