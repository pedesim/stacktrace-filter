"""Censor specific frame fields based on regex patterns."""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List
from stacktrace_filter.parser import Frame, Traceback

_PLACEHOLDER = "<censored>"


@dataclass
class CensorRule:
    field: str  # 'filename', 'function', 'text'
    pattern: str
    replacement: str = _PLACEHOLDER
    _compiled: re.Pattern = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._compiled = re.compile(self.pattern)

    def apply(self, frame: Frame) -> Frame:
        value = getattr(frame, self.field, None)
        if value is None:
            return frame
        new_value = self._compiled.sub(self.replacement, value)
        return Frame(
            filename=new_value if self.field == "filename" else frame.filename,
            lineno=frame.lineno,
            function=new_value if self.field == "function" else frame.function,
            text=new_value if self.field == "text" else frame.text,
        )


@dataclass
class CensorConfig:
    rules: List[CensorRule] = field(default_factory=list)


@dataclass
class CensorResult:
    traceback: Traceback
    censored_count: int


def censor(tb: Traceback, config: CensorConfig) -> CensorResult:
    """Apply all censor rules to every frame in the traceback."""
    if not config.rules:
        return CensorResult(traceback=tb, censored_count=0)

    censored_count = 0
    new_frames: List[Frame] = []
    for frame in tb.frames:
        current = frame
        for rule in config.rules:
            updated = rule.apply(current)
            if updated is not current:
                censored_count += 1
            current = updated
        new_frames.append(current)

    new_tb = Traceback(
        frames=new_frames,
        exception_type=tb.exception_type,
        exception_message=tb.exception_message,
    )
    return CensorResult(traceback=new_tb, censored_count=censored_count)


def format_censor_result(result: CensorResult, color: bool = False) -> str:
    lines = []
    for frame in result.traceback.frames:
        lines.append(f"  File \"{frame.filename}\", line {frame.lineno}, in {frame.function}")
        if frame.text:
            lines.append(f"    {frame.text}")
    if result.traceback.exception_type:
        lines.append(f"{result.traceback.exception_type}: {result.traceback.exception_message}")
    lines.append(f"# censored fields: {result.censored_count}")
    return "\n".join(lines)
