"""Redact sensitive values from frame locals in tracebacks."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from stacktrace_filter.annotator import AnnotatedFrame

DEFAULT_PATTERNS: List[str] = [
    r"password",
    r"secret",
    r"token",
    r"api[_-]?key",
    r"auth",
    r"credential",
]

REDACTED = "<redacted>"


@dataclass
class RedactorConfig:
    patterns: List[str] = field(default_factory=lambda: list(DEFAULT_PATTERNS))
    placeholder: str = REDACTED
    case_sensitive: bool = False


def _compile_patterns(patterns: List[str], case_sensitive: bool) -> List[re.Pattern]:
    flags = 0 if case_sensitive else re.IGNORECASE
    return [re.compile(p, flags) for p in patterns]


def should_redact(key: str, compiled: List[re.Pattern]) -> bool:
    return any(p.search(key) for p in compiled)


def redact_locals(
    locals_dict: Dict[str, str],
    config: Optional[RedactorConfig] = None,
) -> Dict[str, str]:
    if config is None:
        config = RedactorConfig()
    compiled = _compile_patterns(config.patterns, config.case_sensitive)
    return {
        k: (config.placeholder if should_redact(k, compiled) else v)
        for k, v in locals_dict.items()
    }


def redact_annotated_frames(
    frames: List[AnnotatedFrame],
    config: Optional[RedactorConfig] = None,
) -> List[AnnotatedFrame]:
    result = []
    for af in frames:
        new_locals = redact_locals(af.locals, config)
        result.append(AnnotatedFrame(
            frame=af.frame,
            locals=new_locals,
            note=af.note,
        ))
    return result
