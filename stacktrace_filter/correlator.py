"""Correlate tracebacks by shared frames to find common root causes."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Sequence, Tuple

from stacktrace_filter.parser import Frame, Traceback


def _frame_key(f: Frame) -> Tuple[str, str, int]:
    return (f.filename, f.function, f.lineno)


def _shared_keys(
    a: Traceback, b: Traceback
) -> FrozenSet[Tuple[str, str, int]]:
    keys_a = frozenset(_frame_key(f) for f in a.frames)
    keys_b = frozenset(_frame_key(f) for f in b.frames)
    return keys_a & keys_b


@dataclass
class CorrelationEdge:
    index_a: int
    index_b: int
    shared_frame_count: int
    shared_frames: List[Tuple[str, str, int]]


@dataclass
class CorrelationResult:
    tracebacks: List[Traceback]
    edges: List[CorrelationEdge]
    clusters: List[List[int]]  # groups of traceback indices

    @property
    def cluster_count(self) -> int:
        return len(self.clusters)

    def get_cluster(self, index: int) -> List[Traceback]:
        """Return tracebacks in the cluster containing *index*."""
        for cluster in self.clusters:
            if index in cluster:
                return [self.tracebacks[i] for i in cluster]
        return [self.tracebacks[index]]


def _union_find(n: int, pairs: List[Tuple[int, int]]) -> List[List[int]]:
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in pairs:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    groups: Dict[int, List[int]] = {}
    for i in range(n):
        root = find(i)
        groups.setdefault(root, []).append(i)
    return list(groups.values())


def correlate(
    tracebacks: Sequence[Traceback],
    min_shared: int = 1,
) -> CorrelationResult:
    """Build a correlation graph over *tracebacks*.

    Two tracebacks are connected when they share at least *min_shared* frames.
    Returns a :class:`CorrelationResult` with edges and union-find clusters.
    """
    tbs = list(tracebacks)
    edges: List[CorrelationEdge] = []
    connected_pairs: List[Tuple[int, int]] = []

    for i in range(len(tbs)):
        for j in range(i + 1, len(tbs)):
            shared = _shared_keys(tbs[i], tbs[j])
            if len(shared) >= min_shared:
                edges.append(
                    CorrelationEdge(
                        index_a=i,
                        index_b=j,
                        shared_frame_count=len(shared),
                        shared_frames=sorted(shared),
                    )
                )
                connected_pairs.append((i, j))

    clusters = _union_find(len(tbs), connected_pairs)
    return CorrelationResult(tracebacks=tbs, edges=edges, clusters=clusters)


def format_correlation(result: CorrelationResult, *, color: bool = True) -> str:
    lines: List[str] = []
    lines.append(
        f"Correlation: {len(result.tracebacks)} tracebacks, "
        f"{len(result.edges)} edges, "
        f"{result.cluster_count} cluster(s)"
    )
    for idx, cluster in enumerate(result.clusters):
        label = f"  Cluster {idx + 1}: tracebacks {cluster}"
        lines.append(label)
    for edge in result.edges:
        lines.append(
            f"  [{edge.index_a}] <-> [{edge.index_b}]  "
            f"shared={edge.shared_frame_count}"
        )
    return "\n".join(lines)
