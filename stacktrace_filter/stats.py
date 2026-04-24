"""Compute statistics over a parsed traceback for summary reporting."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import List

from .parser import Traceback, is_stdlib, is_site_package


@dataclass
class TracebackStats:
    total_frames: int = 0
    user_frames: int = 0
    stdlib_frames: int = 0
    site_package_frames: int = 0
    unique_files: int = 0
    top_files: List[tuple] = field(default_factory=list)  # (path, count)
    exception_type: str = ""
    exception_msg: str = ""

    @property
    def user_frame_ratio(self) -> float:
        """Fraction of frames that are user code (0.0 if no frames)."""
        if self.total_frames == 0:
            return 0.0
        return self.user_frames / self.total_frames


def compute_stats(tb: Traceback, top_n: int = 5) -> TracebackStats:
    """Return a TracebackStats for the given Traceback."""
    file_counter: Counter = Counter()
    user = stdlib = site = 0

    for frame in tb.frames:
        path = frame.path
        file_counter[path] += 1
        if is_stdlib(path):
            stdlib += 1
        elif is_site_package(path):
            site += 1
        else:
            user += 1

    total = len(tb.frames)
    return TracebackStats(
        total_frames=total,
        user_frames=user,
        stdlib_frames=stdlib,
        site_package_frames=site,
        unique_files=len(file_counter),
        top_files=file_counter.most_common(top_n),
        exception_type=tb.exc_type,
        exception_msg=tb.exc_msg,
    )


def format_stats(stats: TracebackStats) -> str:
    """Render stats as a human-readable string."""
    lines = [
        f"Exception : {stats.exception_type}: {stats.exception_msg}",
        f"Frames    : {stats.total_frames} total "
        f"({stats.user_frames} user, {stats.stdlib_frames} stdlib, "
        f"{stats.site_package_frames} site-packages)",
        f"Files     : {stats.unique_files} unique",
    ]
    if stats.top_files:
        lines.append("Top files :")
        for path, count in stats.top_files:
            lines.append(f"  {count:3d}x  {path}")
    return "\n".join(lines)
