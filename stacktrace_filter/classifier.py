"""Classify tracebacks into categories based on origin and pattern."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from stacktrace_filter.parser import Traceback, Frame
from stacktrace_filter.parser import is_stdlib, is_site_package


CATEGORY_USER = "user"
CATEGORY_LIBRARY = "library"
CATEGORY_STDLIB = "stdlib"
CATEGORY_MIXED = "mixed"


@dataclass
class ClassifiedTraceback:
    traceback: Traceback
    category: str
    user_frame_count: int
    stdlib_frame_count: int
    library_frame_count: int
    dominant_file: Optional[str] = None
    tags: List[str] = field(default_factory=list)


def _dominant_file(frames: List[Frame]) -> Optional[str]:
    from collections import Counter
    user_files = [f.filename for f in frames if not is_stdlib(f.filename) and not is_site_package(f.filename)]
    if not user_files:
        return None
    return Counter(user_files).most_common(1)[0][0]


def classify(tb: Traceback) -> ClassifiedTraceback:
    user = sum(1 for f in tb.frames if not is_stdlib(f.filename) and not is_site_package(f.filename))
    stdlib = sum(1 for f in tb.frames if is_stdlib(f.filename))
    library = sum(1 for f in tb.frames if is_site_package(f.filename))

    total = len(tb.frames)
    if total == 0:
        category = CATEGORY_USER
    elif user == total:
        category = CATEGORY_USER
    elif stdlib == total:
        category = CATEGORY_STDLIB
    elif library == total:
        category = CATEGORY_LIBRARY
    else:
        category = CATEGORY_MIXED

    tags: List[str] = []
    exc = tb.exception_line or ""
    if "Error" in exc:
        tags.append("error")
    if "Warning" in exc:
        tags.append("warning")
    if user == 0:
        tags.append("no-user-frames")

    return ClassifiedTraceback(
        traceback=tb,
        category=category,
        user_frame_count=user,
        stdlib_frame_count=stdlib,
        library_frame_count=library,
        dominant_file=_dominant_file(tb.frames),
        tags=tags,
    )


def format_classification(ct: ClassifiedTraceback) -> str:
    lines = [
        f"Category  : {ct.category}",
        f"Frames    : user={ct.user_frame_count} stdlib={ct.stdlib_frame_count} library={ct.library_frame_count}",
    ]
    if ct.dominant_file:
        lines.append(f"Dominant  : {ct.dominant_file}")
    if ct.tags:
        lines.append(f"Tags      : {', '.join(ct.tags)}")
    return "\n".join(lines)
