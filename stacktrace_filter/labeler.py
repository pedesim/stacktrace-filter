"""Assign human-readable labels to tracebacks based on configurable rules."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from stacktrace_filter.parser import Traceback


@dataclass
class LabelRule:
    label: str
    exc_type: Optional[str] = None
    filename_contains: Optional[str] = None
    message_contains: Optional[str] = None

    def matches(self, tb: Traceback) -> bool:
        if self.exc_type and self.exc_type not in (tb.exc_type or ""):
            return False
        if self.message_contains and self.message_contains not in (tb.exc_message or ""):
            return False
        if self.filename_contains:
            if not any(self.filename_contains in f.filename for f in tb.frames):
                return False
        return True


@dataclass
class LabeledTraceback:
    traceback: Traceback
    labels: List[str] = field(default_factory=list)

    def primary_label(self) -> Optional[str]:
        return self.labels[0] if self.labels else None


@dataclass
class LabelerConfig:
    rules: List[LabelRule] = field(default_factory=list)
    default_label: str = "unlabeled"


def apply_labels(tb: Traceback, config: LabelerConfig) -> LabeledTraceback:
    """Apply all matching rules; fall back to default_label if none match."""
    matched = [rule.label for rule in config.rules if rule.matches(tb)]
    if not matched:
        matched = [config.default_label]
    return LabeledTraceback(traceback=tb, labels=matched)


def label_all(tracebacks: List[Traceback], config: LabelerConfig) -> List[LabeledTraceback]:
    return [apply_labels(tb, config) for tb in tracebacks]


def format_labeled(lt: LabeledTraceback) -> str:
    labels_str = ", ".join(lt.labels)
    exc = lt.traceback.exc_type or "UnknownError"
    msg = lt.traceback.exc_message or ""
    return f"[{labels_str}] {exc}: {msg}"
