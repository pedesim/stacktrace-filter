"""Aggregate multiple tracebacks into a summary report."""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import Counter
from typing import List, Dict
from stacktrace_filter.parser import Traceback
from stacktrace_filter.fingerprint import fingerprint
from stacktrace_filter.severity import classify, SeverityResult


@dataclass
class AggregatedEntry:
    fingerprint_short: str
    exc_type: str
    exc_message: str
    count: int
    severity: str
    sample: Traceback


@dataclass
class AggregationReport:
    total: int
    entries: List[AggregatedEntry] = field(default_factory=list)

    @property
    def by_severity(self) -> Dict[str, int]:
        c: Counter = Counter()
        for e in self.entries:
            c[e.severity] += e.count
        return dict(c)


def aggregate(tracebacks: List[Traceback]) -> AggregationReport:
    """Group tracebacks by fingerprint and produce an aggregation report."""
    groups: Dict[str, List[Traceback]] = {}
    for tb in tracebacks:
        fp = fingerprint(tb)
        key = fp.short
        groups.setdefault(key, []).append(tb)

    entries: List[AggregatedEntry] = []
    for short_fp, tbs in groups.items():
        sample = tbs[0]
        sev: SeverityResult = classify(sample)
        exc_type = sample.exc_type or "Unknown"
        exc_message = sample.exc_message or ""
        entries.append(
            AggregatedEntry(
                fingerprint_short=short_fp,
                exc_type=exc_type,
                exc_message=exc_message,
                count=len(tbs),
                severity=sev.level,
                sample=sample,
            )
        )

    entries.sort(key=lambda e: e.count, reverse=True)
    return AggregationReport(total=len(tracebacks), entries=entries)


def format_aggregation(report: AggregationReport, color: bool = True) -> str:
    lines = [f"Aggregation report — {report.total} tracebacks, {len(report.entries)} unique\n"]
    for e in report.entries:
        line = f"  [{e.fingerprint_short}] {e.exc_type}: {e.exc_message[:60]}  x{e.count}  ({e.severity})"
        lines.append(line)
    if report.by_severity:
        lines.append("")
        lines.append("Severity breakdown:")
        for sev, cnt in sorted(report.by_severity.items()):
            lines.append(f"  {sev}: {cnt}")
    return "\n".join(lines)
