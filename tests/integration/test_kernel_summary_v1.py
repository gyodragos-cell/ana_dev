"""Kernel summary aggregate tests."""

from core.agent_manager import AgentManager
from core.cluster_manager import ClusterManager, ClusterNode
from core.distributed_memory import DistributedMemory
from core.federation_manager import FederationManager
from core.kernel_summary import KernelSummary
from core.metrics_manager import MetricsManager
from core.model_registry import ModelRegistry
from core.pipeline_manager import PipelineManager
from core.vector_memory import VectorMemory


def test_full_kernel_summary_shapes():
    """KernelSummary should aggregate all major areas."""
    cluster = ClusterManager()
    cluster.nodes["n1"] = ClusterNode("n1")
    memory = DistributedMemory()
    models = ModelRegistry(memory)
    models.register_model("m", "1", {"path": "/m"})
    agents = AgentManager(memory)
    agents.register_agent("a", {})
    metrics = MetricsManager()
    metrics.increment("events.sent")
    vectors = VectorMemory(memory)
    vectors.store_embedding("v", [1.0], {})
    federation = FederationManager("c1", "lab")
    summary = KernelSummary(
        cluster=cluster,
        memory=memory,
        models=models,
        agents=agents,
        metrics=metrics,
        vectors=vectors,
        federation=federation,
        pipelines=PipelineManager(),
    ).full()
    assert summary["models"]["count"] == 1
    assert summary["agents"]["count"] == 1
    assert summary["metrics"]["events.sent"] == 1
    assert summary["vectors"]["count"] == 1
