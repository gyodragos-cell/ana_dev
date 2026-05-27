"""ANA MAX AI Kernel v1 vector and pipeline tests."""

from core.cluster_manager import ClusterManager, ClusterNode
from core.distributed_memory import DistributedMemory
from core.inference_dispatcher import InferenceDispatcher
from core.model_registry import ModelRegistry
from core.model_router import ModelRouter
from core.pipeline_manager import PipelineManager
from core.placement_manager import PlacementManager
from core.vector_memory import VectorMemory


def test_vector_memory_and_model_aware_routing():
    """Vector memory should store/query and support routing locality metadata."""
    memory = DistributedMemory()
    vectors = VectorMemory(memory, node_id="n1")
    vectors.store_embedding("doc1", [1.0, 0.0], {"node_id": "n1"})
    vectors.store_embedding("doc2", [0.0, 1.0], {"node_id": "n2"})
    assert vectors.query_embedding([1.0, 0.0], top_k=1)[0]["key"] == "doc1"
    assert "vector:doc1" in memory.store


def test_agentic_model_pipeline_simulated():
    """Pipeline manager should chain fake model and agentic steps."""
    memory = DistributedMemory()
    registry = ModelRegistry(memory)
    registry.register_model("m1", "1", "/m1", ["cpu"])
    registry.register_model("m2", "1", "/m2", ["cpu"])
    cluster = ClusterManager()
    cluster.nodes["n1"] = ClusterNode("n1", capabilities=["cpu"])
    placement = PlacementManager(memory)
    placement.set_placement("m1", "1", ["n1"])
    placement.set_placement("m2", "1", ["n1"])
    dispatcher = InferenceDispatcher(ModelRouter(registry, placement, cluster))
    pipeline = PipelineManager(dispatcher)
    result = pipeline.run_model_pipeline(["m1", "m2"], "input")
    assert result["success"] is True
    agentic = pipeline.run_agentic_pipeline([lambda x: f"{x}-a", lambda x: f"{x}-b"], "start")
    assert agentic["output"] == "start-a-b"
