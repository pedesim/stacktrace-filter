"""resolver.py – map raw frame filenames to project-relative paths.

Given a list of root directories, a Resolver rewrites absolute or
site-package-relative filenames to short, human-readable paths such as
``src/myapp/utils.py`` instead of ``/home/user/project/src/myapp/utils.py``.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from stacktrace_filter.parser import Frame


@dataclass
class ResolverConfig:
    roots: List[str] = field(default_factory=list)
    fallback_basename: bool = False

    def __post_init__(self) -> None:
        # Normalise every root to an absolute, trailing-slash-free path.
        self.roots = [os.path.normpath(os.path.abspath(r)) for r in self.roots]


@dataclass
class ResolvedFrame:
    original: Frame
    resolved_filename: str
    was_resolved: bool

    # Convenience pass-throughs so callers can treat this like a Frame.
    @property
    def lineno(self) -> int:
        return self.original.lineno

    @property
    def function(self) -> str:
        return self.original.function

    @property
    def line(self) -> str:
        return self.original.line


def _try_resolve(filename: str, roots: Sequence[str]) -> Optional[str]:
    """Return the shortest relative path under any root, or None."""
    norm = os.path.normpath(os.path.abspath(filename))
    best: Optional[str] = None
    for root in roots:
        if norm.startswith(root + os.sep):
            rel = os.path.relpath(norm, root)
            if best is None or len(rel) < len(best):
                best = rel
    return best


def resolve_frame(frame: Frame, config: ResolverConfig) -> ResolvedFrame:
    """Resolve a single frame's filename according to *config*."""
    resolved = _try_resolve(frame.filename, config.roots)
    if resolved is not None:
        return ResolvedFrame(original=frame, resolved_filename=resolved, was_resolved=True)
    if config.fallback_basename:
        return ResolvedFrame(
            original=frame,
            resolved_filename=os.path.basename(frame.filename),
            was_resolved=False,
        )
    return ResolvedFrame(original=frame, resolved_filename=frame.filename, was_resolved=False)


def resolve_frames(frames: Sequence[Frame], config: ResolverConfig) -> List[ResolvedFrame]:
    """Resolve every frame in *frames*."""
    return [resolve_frame(f, config) for f in frames]


def format_resolved_frame(rf: ResolvedFrame) -> str:
    marker = "*" if rf.was_resolved else " "
    return f"  [{marker}] File \"{rf.resolved_filename}\", line {rf.lineno}, in {rf.function}"
