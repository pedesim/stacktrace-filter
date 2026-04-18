"""Summarize a parsed traceback into a structured report."""
from dataclasses import dataclass, field
from typing import List, Optional
from .parser import Traceback, Frame, is_stdlib, is_site_package


@dataclass
class FrameSummary:
    filename: str
    lineno: int
    name: str
    category: str  # 'user', 'stdlib', 'site-package'


@dataclass
class TracebackSummary:
    exception_type: str
    exception_msg: str
    frames: List[FrameSummary] = field(default_factory=list)
    user_frame_count: int = 0
    stdlib_frame_count: int = 0
    site_frame_count: int = 0
    deepest_user_frame: Optional[FrameSummary] = None


def _categorize(frame: Frame) -> str:
    if is_stdlib(frame.filename):
        return "stdlib"
    if is_site_package(frame.filename):
        return "site-package"
    return "user"


def summarize(tb: Traceback) -> TracebackSummary:
    """Build a TracebackSummary from a parsed Traceback."""
    summaries = []
    for frame in tb.frames:
        cat = _categorize(frame)
        summaries.append(FrameSummary(
            filename=frame.filename,
            lineno=frame.lineno,
            name=frame.name,
            category=cat,
        ))

    user_frames = [f for f in summaries if f.category == "user"]
    stdlib_frames = [f for f in summaries if f.category == "stdlib"]
    site_frames = [f for f in summaries if f.category == "site-package"]

    return TracebackSummary(
        exception_type=tb.exc_type,
        exception_msg=tb.exc_msg,
        frames=summaries,
        user_frame_count=len(user_frames),
        stdlib_frame_count=len(stdlib_frames),
        site_frame_count=len(site_frames),
        deepest_user_frame=user_frames[-1] if user_frames else None,
    )
