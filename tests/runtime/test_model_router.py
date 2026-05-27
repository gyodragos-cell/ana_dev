"""Tests for model router v1."""

from core.cluster_manager import ClusterManager, ClusterNode, NodeState
from core.distributed_memory import DistributedMemory
from core.model_registry import ModelRegistry
from core.model_router import ModelRouter
from core.placement_manager import PlacementManager


def make_router():
    """Create a router with two active nodes."""
    memory = DistributedMemory()
    registry = ModelRegistry(memory)
    registry.register_model("m1", "1", {"path": "/m1", "capabilities": ["cpu"]})
    placement = PlacementManager(memory)
    cluster = ClusterManager()
    cluster.nodes["n1"] = ClusterNode("n1", capabilities=["cpu"])
    cluster.nodes["n2"] = ClusterNode("n2", capabilities=["cpu"])
    return ModelRouter(registry, placement, cluster), placement, cluster


def test_route_prefers_nodes_with_placement():
    """Router should prefer placed nodes."""
    router, placement, _cluster = make_router()
    placement.set_placement("m1", "1", ["n2"])
    assert router.route("m1", "1") == "n2"


def test_route_skips_suspect_and_dead_nodes():
    """Router should skip SUSPECT and DEAD nodes."""
    router, placement, cluster = make_router()
    placement.set_placement("m1", "1", ["n1", "n2"])
    cluster.nodes["n1"].state = NodeState.SUSPECT
    assert router.route("m1", "1") == "n2"
    cluster.nodes["n2"].state = NodeState.DEAD
    assert router.route("m1", "1") is None


def test_route_fallbacks_to_cluster_best_node_when_no_placement():
    """Router should fallback to cluster best node without placement."""
    router, _placement, _cluster = make_router()
    assert router.route("m1", "1", capability="cpu") == "n1"


def test_round_robin_between_multiple_nodes():
    """Router should round-robin across multiple placed nodes."""
    router, placement, _cluster = make_router()
    placement.set_placement("m1", "1", ["n1", "n2"])
    assert [router.route("m1", "1"), router.route("m1", "1"), router.route("m1", "1")] == ["n1", "n2", "n1"]
