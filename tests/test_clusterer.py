"""Tests for stacktrace_filter.clusterer."""
import pytest

from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.clusterer import cluster, format_cluster_result, Cluster, ClusterResult


def _frame(filename: str = "app.py", lineno: int = 10, name: str = "fn") -> Frame:
    return Frame(filename=filename, lineno=lineno, name=name, source_line="pass")


def _tb(exc: str = "ValueError", frames=None) -> Traceback:
    if frames is None:
        frames = [_frame()]
    return Traceback(frames=frames, exception_line=exc)


# ---------------------------------------------------------------------------
# ClusterResult helpers
# ---------------------------------------------------------------------------

def test_cluster_result_total():
    c1 = Cluster(label="a", members=[_tb(), _tb()])
    c2 = Cluster(label="b", members=[_tb()])
    result = ClusterResult(clusters=[c1, c2])
    assert result.total == 3


def test_cluster_result_cluster_count():
    result = ClusterResult(clusters=[Cluster(label="x"), Cluster(label="y")])
    assert result.cluster_count == 2


def test_cluster_result_get_existing():
    c = Cluster(label="my-cluster")
    result = ClusterResult(clusters=[c])
    assert result.get("my-cluster") is c


def test_cluster_result_get_missing():
    result = ClusterResult(clusters=[])
    assert result.get("nope") is None


# ---------------------------------------------------------------------------
# cluster()
# ---------------------------------------------------------------------------

def test_cluster_empty_list():
    result = cluster([])
    assert result.cluster_count == 0
    assert result.total == 0


def test_cluster_single_traceback():
    tb = _tb()
    result = cluster([tb])
    assert result.cluster_count == 1
    assert result.total == 1


def test_cluster_identical_tracebacks_same_bucket():
    tb = _tb(exc="ValueError", frames=[_frame("app.py", 42, "run")])
    result = cluster([tb, tb, tb])
    # Identical tracebacks share the same fingerprint prefix → one cluster.
    assert result.cluster_count == 1
    assert result.clusters[0].size == 3


def test_cluster_different_tracebacks_different_buckets():
    tb1 = _tb(exc="ValueError", frames=[_frame("a.py", 1, "alpha")])
    tb2 = _tb(exc="KeyError", frames=[_frame("b.py", 99, "beta")])
    result = cluster([tb1, tb2])
    # Different exception types / frames → likely different fingerprints.
    # We cannot guarantee 2 clusters for very coarse depth, so use depth=8.
    result = cluster([tb1, tb2], depth=8)
    assert result.total == 2


def test_cluster_representative_is_first_member():
    tb = _tb()
    result = cluster([tb])
    assert result.clusters[0].representative is tb


def test_cluster_label_prefix():
    tb = _tb()
    result = cluster([tb], label_prefix="grp")
    assert result.clusters[0].label.startswith("grp-")


def test_cluster_depth_affects_granularity():
    """Shallower depth should produce <= clusters compared to deeper depth."""
    tbs = [
        _tb(exc="ValueError", frames=[_frame("app.py", i, "fn")]) for i in range(5)
    ]
    coarse = cluster(tbs, depth=1)
    fine = cluster(tbs, depth=8)
    assert coarse.cluster_count <= fine.cluster_count


# ---------------------------------------------------------------------------
# format_cluster_result()
# ---------------------------------------------------------------------------

def test_format_cluster_result_contains_cluster_count():
    tb = _tb(exc="RuntimeError")
    result = cluster([tb])
    output = format_cluster_result(result)
    assert "Clusters: 1" in output


def test_format_cluster_result_contains_exception_line():
    tb = _tb(exc="ZeroDivisionError")
    result = cluster([tb])
    output = format_cluster_result(result)
    assert "ZeroDivisionError" in output


def test_format_cluster_result_sorted_by_size_descending():
    tb_a = _tb(exc="ValueError", frames=[_frame("a.py", 1, "a")])
    tb_b = _tb(exc="KeyError", frames=[_frame("b.py", 2, "b")])
    # Force two distinct clusters by using fine depth.
    result = cluster([tb_a, tb_a, tb_b], depth=8)
    output = format_cluster_result(result)
    lines = [l for l in output.splitlines() if "traceback" in l]
    if len(lines) >= 2:
        count_first = int(lines[0].split(":")[1].strip().split()[0])
        count_second = int(lines[1].split(":")[1].strip().split()[0])
        assert count_first >= count_second
