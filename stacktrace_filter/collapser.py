"""Collapser: merge consecutive non-user frames into a single summary line."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_filter.parser import Frame


@dataclass
class CollapseConfig:
    collapse_stdlib: bool = True
    collapse_site_packages: bool = True
    label: str = "[{count} frame(s) hidden]"


@dataclass
class CollapsedFrame:
    """Represents either a real frame or a collapse-summary placeholder."""
    frame: Optional[Frame]
    is_collapsed: bool = False
    collapsed_count: int = 0
    label: str = ""

    @property
    def is_real(self) -> bool:
        return not self.is_collapsed


@dataclass
class CollapseResult:
    entries: List[CollapsedFrame] = field(default_factory=list)

    @property
    def total_hidden(self) -> int:
        return sum(e.collapsed_count for e in self.entries if e.is_collapsed)

    @property
    def real_count(self) -> int:
        return sum(1 for e in self.entries if e.is_real)


def _should_collapse(frame: Frame, cfg: CollapseConfig) -> bool:
    from stacktrace_filter.parser import is_stdlib, is_site_package
    if cfg.collapse_stdlib and is_stdlib(frame):
        return True
    if cfg.collapse_site_packages and is_site_package(frame):
        return True
    return False


def collapse(frames: List[Frame], cfg: Optional[CollapseConfig] = None) -> CollapseResult:
    """Collapse consecutive non-user frames into summary placeholders."""
    if cfg is None:
        cfg = CollapseConfig()

    result = CollapseResult()
    run: List[Frame] = []

    def flush_run() -> None:
        if not run:
            return
        label = cfg.label.format(count=len(run))
        result.entries.append(
            CollapsedFrame(frame=None, is_collapsed=True,
                           collapsed_count=len(run), label=label)
        )
        run.clear()

    for frame in frames:
        if _should_collapse(frame, cfg):
            run.append(frame)
        else:
            flush_run()
            result.entries.append(CollapsedFrame(frame=frame))

    flush_run()
    return result


def format_collapse_result(result: CollapseResult, color: bool = False) -> str:
    lines: List[str] = []
    for entry in result.entries:
        if entry.is_collapsed:
            msg = entry.label
            if color:
                msg = f"\033[2m{msg}\033[0m"  # dim
            lines.append(f"  {msg}")
        else:
            assert entry.frame is not None
            f = entry.frame
            lines.append(f"  File \"{f.filename}\", line {f.lineno}, in {f.name}")
            if f.line:
                lines.append(f"    {f.line}")
    return "\n".join(lines)
