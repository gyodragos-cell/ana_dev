"""AI Kernel v2 cognitive runtime tests."""

from core.cognitive_runtime import CognitiveRuntime
from core.distributed_memory import DistributedMemory
from core.pipeline_manager import PipelineManager
from core.vector_memory import VectorMemory


def test_cognitive_runtime_memory_planning_and_workflow():
    """Cognitive runtime should simulate memory consolidation and workflows."""
    memory = DistributedMemory()
    vectors = VectorMemory(memory)
    vectors.store_embedding("past", [1.0, 0.0], {"kind": "episode"})
    runtime = CognitiveRuntime(vectors, memory, PipelineManager())
    runtime.add_episode({"task": "chat", "result": "ok"})
    runtime.add_semantic("tool", "grep")
    consolidated = runtime.consolidate()
    assert consolidated["episode_count"] == 1
    runtime.prune(1)
    plan = runtime.plan("answer")
    assert plan["steps"] == ["retrieve", "route", "execute", "verify"]
    assert runtime.run_workflow("answer")["success"] is True
    assert vectors.query_embedding([1.0, 0.0])[0]["key"] == "past"
