"""Validate tracebacks against configurable rules and produce a report."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_filter.parser import Traceback, Frame


@dataclass
class ValidationViolation:
    rule_name: str
    message: str
    frame: Optional[Frame] = None


@dataclass
class ValidationResult:
    traceback: Traceback
    violations: List[ValidationViolation] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.violations) == 0

    @property
    def violation_count(self) -> int:
        return len(self.violations)


@dataclass
class ValidatorConfig:
    max_depth: Optional[int] = None
    require_user_frame: bool = False
    forbidden_filenames: List[str] = field(default_factory=list)
    forbidden_functions: List[str] = field(default_factory=list)


def _check_max_depth(
    tb: Traceback, cfg: ValidatorConfig, violations: List[ValidationViolation]
) -> None:
    if cfg.max_depth is not None and len(tb.frames) > cfg.max_depth:
        violations.append(
            ValidationViolation(
                rule_name="max_depth",
                message=(
                    f"Traceback has {len(tb.frames)} frames, "
                    f"exceeds max_depth={cfg.max_depth}"
                ),
            )
        )


def _check_require_user_frame(
    tb: Traceback, cfg: ValidatorConfig, violations: List[ValidationViolation]
) -> None:
    if not cfg.require_user_frame:
        return
    from stacktrace_filter.parser import is_stdlib, is_site_package

    has_user = any(
        not is_stdlib(f) and not is_site_package(f) for f in tb.frames
    )
    if not has_user:
        violations.append(
            ValidationViolation(
                rule_name="require_user_frame",
                message="Traceback contains no user-code frames",
            )
        )


def _check_forbidden(
    tb: Traceback, cfg: ValidatorConfig, violations: List[ValidationViolation]
) -> None:
    for frame in tb.frames:
        for pattern in cfg.forbidden_filenames:
            if pattern in frame.filename:
                violations.append(
                    ValidationViolation(
                        rule_name="forbidden_filename",
                        message=f"Frame filename '{frame.filename}' matches forbidden pattern '{pattern}'",
                        frame=frame,
                    )
                )
        for pattern in cfg.forbidden_functions:
            if pattern in frame.function:
                violations.append(
                    ValidationViolation(
                        rule_name="forbidden_function",
                        message=f"Frame function '{frame.function}' matches forbidden pattern '{pattern}'",
                        frame=frame,
                    )
                )


def validate(tb: Traceback, cfg: Optional[ValidatorConfig] = None) -> ValidationResult:
    """Run all validation rules against *tb* and return a ValidationResult."""
    if cfg is None:
        cfg = ValidatorConfig()
    violations: List[ValidationViolation] = []
    _check_max_depth(tb, cfg, violations)
    _check_require_user_frame(tb, cfg, violations)
    _check_forbidden(tb, cfg, violations)
    return ValidationResult(traceback=tb, violations=violations)


def format_validation(result: ValidationResult, *, color: bool = True) -> str:
    """Return a human-readable summary of a ValidationResult."""
    if result.is_valid:
        ok = "\033[32mOK\033[0m" if color else "OK"
        return f"Validation {ok}: no violations found."
    lines = []
    err = "\033[31mFAIL\033[0m" if color else "FAIL"
    lines.append(f"Validation {err}: {result.violation_count} violation(s)")
    for v in result.violations:
        loc = f" [{v.frame.filename}:{v.frame.lineno}]" if v.frame else ""
        lines.append(f"  [{v.rule_name}]{loc} {v.message}")
    return "\n".join(lines)
