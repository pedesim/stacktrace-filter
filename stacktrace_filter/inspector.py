"""Inspector: extract and report key facts about a single traceback."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .parser import Traceback, Frame
from .parser import is_stdlib, is_site_package


@dataclass
class InspectionResult:
    exc_type: str
    exc_message: str
    total_frames: int
    user_frames: int
    stdlib_frames: int
    library_frames: int
    deepest_user_frame: Optional[Frame]
    unique_files: List[str] = field(default_factory=list)
    unique_functions: List[str] = field(default_factory=list)

    @property
    def user_ratio(self) -> float:
        if self.total_frames == 0:
            return 0.0
        return self.user_frames / self.total_frames

    @property
    def has_user_code(self) -> bool:
        return self.user_frames > 0


def _categorize(frame: Frame) -> str:
    if is_stdlib(frame.filename):
        return "stdlib"
    if is_site_package(frame.filename):
        return "library"
    return "user"


def inspect(tb: Traceback) -> InspectionResult:
    """Analyse *tb* and return an :class:`InspectionResult`."""
    user_frames = [f for f in tb.frames if _categorize(f) == "user"]
    stdlib_frames = [f for f in tb.frames if _categorize(f) == "stdlib"]
    library_frames = [f for f in tb.frames if _categorize(f) == "library"]

    deepest_user: Optional[Frame] = user_frames[-1] if user_frames else None

    unique_files = list(dict.fromkeys(f.filename for f in tb.frames))
    unique_functions = list(dict.fromkeys(f.function for f in tb.frames))

    return InspectionResult(
        exc_type=tb.exc_type,
        exc_message=tb.exc_message,
        total_frames=len(tb.frames),
        user_frames=len(user_frames),
        stdlib_frames=len(stdlib_frames),
        library_frames=len(library_frames),
        deepest_user_frame=deepest_user,
        unique_files=unique_files,
        unique_functions=unique_functions,
    )


def format_inspection(result: InspectionResult, *, color: bool = True) -> str:
    """Render an :class:`InspectionResult` as a human-readable string."""
    lines: List[str] = []
    bold = "\033[1m" if color else ""
    reset = "\033[0m" if color else ""

    lines.append(f"{bold}Exception:{reset} {result.exc_type}: {result.exc_message}")
    lines.append(f"{bold}Frames:{reset} {result.total_frames} total "
                 f"({result.user_frames} user, {result.stdlib_frames} stdlib, "
                 f"{result.library_frames} library)")
    lines.append(f"{bold}User ratio:{reset} {result.user_ratio:.0%}")
    if result.deepest_user_frame:
        f = result.deepest_user_frame
        lines.append(f"{bold}Deepest user frame:{reset} {f.filename}:{f.lineno} in {f.function}")
    lines.append(f"{bold}Unique files:{reset} {len(result.unique_files)}")
    lines.append(f"{bold}Unique functions:{reset} {len(result.unique_functions)}")
    return "\n".join(lines)
