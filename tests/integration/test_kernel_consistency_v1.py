"""Kernel consistency tests for ANA MAX OS v1 build."""

from core.cluster_manager import ClusterManager, ClusterNode
from core.distributed_memory import DistributedMemory
from core.fs_sync import FSSync
from core.kernel_summary import KernelSummary


def test_kernel_consistency_modes_and_metadata(tmp_path):
    """Kernel summaries should expose consistency and node metadata."""
    cluster = ClusterManager(cluster_id="c1", domain="lab")
    cluster.nodes["n1"] = ClusterNode("n1", capabilities=["cpu"])
    cluster.set_node_labels("n1", ["lab", "cpu"])
    cluster.set_node_annotations("n1", {"zone": "z1"})
    memory = DistributedMemory(mode="hybrid")
    fs_sync = FSSync(tmp_path, mode="strong_local")
    summary = KernelSummary(cluster=cluster, memory=memory, fs=fs_sync)
    assert summary.consistency() == {"memory": "hybrid", "fs": "strong_local"}
    assert summary.health()["kernel_version"] == "ANA MAX AI Kernel v1"
    assert cluster.node_labels["n1"] == ["lab", "cpu"]
