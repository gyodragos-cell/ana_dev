"""Kernel health tests for ANA MAX OS v1 build."""

from core.cluster_manager import ClusterManager, ClusterNode, NodeState


def test_kernel_health_summary_counts_states():
    """Health summary should count node states."""
    cluster = ClusterManager()
    cluster.nodes["active"] = ClusterNode("active")
    cluster.nodes["suspect"] = ClusterNode("suspect", state=NodeState.SUSPECT, healthy=False)
    cluster.nodes["dead"] = ClusterNode("dead", state=NodeState.DEAD, healthy=False)
    summary = cluster.kernel_health_summary()
    assert summary["nodes"] == 3
    assert summary["states"]["active"] == 1
    assert summary["states"]["suspect"] == 1
    assert summary["states"]["dead"] == 1
    assert summary["healthy"] is False
