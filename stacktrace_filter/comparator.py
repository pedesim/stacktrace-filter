"""Compare two tracebacks and produce a similarity score."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List
from stacktrace_filter.parser import Traceback, Frame


@dataclass
class ComparisonResult:
    left: Traceback
    right: Traceback
    frame_similarity: float  # 0.0 – 1.0
    exc_type_match: bool
    exc_message_match: bool
    overall_score: float


def _frame_key(f: Frame) -> str:
    return f"{f.filename}:{f.lineno}:{f.name}"


def _frame_similarity(left: List[Frame], right: List[Frame]) -> float:
    if not left and not right:
        return 1.0
    left_keys = set(_frame_key(f) for f in left)
    right_keys = set(_frame_key(f) for f in right)
    intersection = left_keys & right_keys
    union = left_keys | right_keys
    return len(intersection) / len(union) if union else 0.0


def compare(left: Traceback, right: Traceback) -> ComparisonResult:
    frame_sim = _frame_similarity(left.frames, right.frames)
    exc_type_match = left.exc_type == right.exc_type
    exc_message_match = left.exc_message == right.exc_message

    score = frame_sim * 0.6
    if exc_type_match:
        score += 0.3
    if exc_message_match:
        score += 0.1

    return ComparisonResult(
        left=left,
        right=right,
        frame_similarity=frame_sim,
        exc_type_match=exc_type_match,
        exc_message_match=exc_message_match,
        overall_score=round(score, 4),
    )


def format_comparison(result: ComparisonResult, color: bool = True) -> str:
    lines = []
    _g = "\033[32m" if color else ""
    _r = "\033[31m" if color else ""
    _reset = "\033[0m" if color else ""

    def tick(val: bool) -> str:
        return f"{_g}✔{_reset}" if val else f"{_r}✘{_reset}"

    lines.append(f"exc_type match : {tick(result.exc_type_match)}")
    lines.append(f"exc_msg  match : {tick(result.exc_message_match)}")
    lines.append(f"frame similarity: {result.frame_similarity:.2%}")
    lines.append(f"overall score   : {result.overall_score:.4f}")
    return "\n".join(lines)
