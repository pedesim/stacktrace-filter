"""Cluster tracebacks by structural similarity into named groups."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence

from .parser import Traceback
from .fingerprint import fingerprint, Fingerprint


@dataclass
class Cluster:
    label: str
    members: List[Traceback] = field(default_factory=list)
    representative: Traceback | None = None

    @property
    def size(self) -> int:
        return len(self.members)


@dataclass
class ClusterResult:
    clusters: List[Cluster]

    @property
    def total(self) -> int:
        return sum(c.size for c in self.clusters)

    @property
    def cluster_count(self) -> int:
        return len(self.clusters)

    def get(self, label: str) -> Cluster | None:
        for c in self.clusters:
            if c.label == label:
                return c
        return None


def _fp_prefix(fp: Fingerprint, depth: int) -> str:
    """Return a coarse key based on the first *depth* characters of the short hash."""
    return fp.short[:depth]


def cluster(
    tracebacks: Sequence[Traceback],
    *,
    depth: int = 6,
    label_prefix: str = "cluster",
) -> ClusterResult:
    """Group *tracebacks* by fingerprint prefix similarity.

    Args:
        tracebacks: Sequence of parsed Traceback objects.
        depth: Number of hex characters of the fingerprint to use as the
               bucket key.  Smaller values produce coarser clusters.
        label_prefix: Prefix string for auto-generated cluster labels.

    Returns:
        A :class:`ClusterResult` with one :class:`Cluster` per unique bucket.
    """
    buckets: Dict[str, Cluster] = {}
    for tb in tracebacks:
        fp = fingerprint(tb)
        key = _fp_prefix(fp, depth)
        if key not in buckets:
            label = f"{label_prefix}-{key}"
            buckets[key] = Cluster(label=label, representative=tb)
        buckets[key].members.append(tb)
    return ClusterResult(clusters=list(buckets.values()))


def format_cluster_result(result: ClusterResult, *, color: bool = True) -> str:
    """Render a human-readable summary of *result*."""
    lines: List[str] = [
        f"Clusters: {result.cluster_count}  Total tracebacks: {result.total}",
        "-" * 50,
    ]
    for c in sorted(result.clusters, key=lambda x: -x.size):
        exc = ""
        if c.representative and c.representative.exception_line:
            exc = f"  [{c.representative.exception_line.strip()}]"
        lines.append(f"  {c.label}: {c.size} traceback(s){exc}")
    return "\n".join(lines)
