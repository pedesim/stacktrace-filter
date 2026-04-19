"""Profile tracebacks by measuring frame frequency across a collection."""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import Counter
from typing import List, Dict, Tuple
from stacktrace_filter.parser import Traceback, Frame


@dataclass
class FrameProfile:
    filename: str
    function: str
    count: int
    pct: float


@dataclass
class ProfileReport:
    total_tracebacks: int
    total_frames: int
    top_frames: List[FrameProfile]
    top_files: List[Tuple[str, int]]
    top_functions: List[Tuple[str, int]]


def _frame_key(f: Frame) -> Tuple[str, str]:
    return (f.filename, f.function)


def profile(tracebacks: List[Traceback], top_n: int = 10) -> ProfileReport:
    frame_counter: Counter = Counter()
    file_counter: Counter = Counter()
    func_counter: Counter = Counter()

    for tb in tracebacks:
        for f in tb.frames:
            frame_counter[_frame_key(f)] += 1
            file_counter[f.filename] += 1
            func_counter[f.function] += 1

    total_frames = sum(frame_counter.values())
    total_tbs = len(tracebacks)

    top_frames = [
        FrameProfile(
            filename=k[0],
            function=k[1],
            count=c,
            pct=round(100.0 * c / total_tbs, 1) if total_tbs else 0.0,
        )
        for k, c in frame_counter.most_common(top_n)
    ]

    return ProfileReport(
        total_tracebacks=total_tbs,
        total_frames=total_frames,
        top_frames=top_frames,
        top_files=file_counter.most_common(top_n),
        top_functions=func_counter.most_common(top_n),
    )


def format_profile(report: ProfileReport) -> str:
    lines = [
        f"Tracebacks : {report.total_tracebacks}",
        f"Total frames: {report.total_frames}",
        "",
        "Top frames:",
    ]
    for fp in report.top_frames:
        lines.append(f"  {fp.pct:5.1f}%  {fp.function}  ({fp.filename})")
    lines.append("")
    lines.append("Top files:")
    for fname, cnt in report.top_files:
        lines.append(f"  {cnt:4d}  {fname}")
    lines.append("")
    lines.append("Top functions:")
    for fn, cnt in report.top_functions:
        lines.append(f"  {cnt:4d}  {fn}")
    return "\n".join(lines)
