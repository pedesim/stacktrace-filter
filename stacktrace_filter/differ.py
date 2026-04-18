"""Compare two tracebacks and highlight differing frames."""
from dataclasses import dataclass, field
from typing import List, Tuple
from .parser import Traceback, Frame


@dataclass
class DiffResult:
    only_in_left: List[Frame] = field(default_factory=list)
    only_in_right: List[Frame] = field(default_factory=list)
    common: List[Frame] = field(default_factory=list)
    changed: List[Tuple[Frame, Frame]] = field(default_factory=list)


def _frame_key(frame: Frame) -> Tuple[str, int]:
    return (frame.filename, frame.lineno)


def diff_tracebacks(left: Traceback, right: Traceback) -> DiffResult:
    """Compare two tracebacks by frame identity (filename + lineno)."""
    left_map = {_frame_key(f): f for f in left.frames}
    right_map = {_frame_key(f): f for f in right.frames}

    left_keys = set(left_map)
    right_keys = set(right_map)

    result = DiffResult()
    result.only_in_left = [left_map[k] for k in sorted(left_keys - right_keys)]
    result.only_in_right = [right_map[k] for k in sorted(right_keys - left_keys)]

    for key in left_keys & right_keys:
        lf, rf = left_map[key], right_map[key]
        if lf.line.strip() != rf.line.strip():
            result.changed.append((lf, rf))
        else:
            result.common.append(lf)

    return result


def format_diff(result: DiffResult, color: bool = True) -> str:
    RED = "\033[31m" if color else ""
    GREEN = "\033[32m" if color else ""
    YELLOW = "\033[33m" if color else ""
    RESET = "\033[0m" if color else ""

    lines = []
    for f in result.only_in_left:
        lines.append(f"{RED}- {f.filename}:{f.lineno} {f.line.strip()}{RESET}")
    for f in result.only_in_right:
        lines.append(f"{GREEN}+ {f.filename}:{f.lineno} {f.line.strip()}{RESET}")
    for lf, rf in result.changed:
        lines.append(f"{YELLOW}~ {lf.filename}:{lf.lineno}{RESET}")
        lines.append(f"{RED}  - {lf.line.strip()}{RESET}")
        lines.append(f"{GREEN}  + {rf.line.strip()}{RESET}")
    if not lines:
        lines.append("Tracebacks are identical.")
    return "\n".join(lines)
