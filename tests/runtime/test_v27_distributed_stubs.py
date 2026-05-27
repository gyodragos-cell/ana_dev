"""Tests for v27 distributed concept stubs."""

from core.cluster_manager_stub import ClusterManagerStub
from core.distributed_memory_stub import DistributedMemoryStub
from core.distributed_orchestrator_stub import DistributedOrchestratorStub
from core.remote_agent_stub import RemoteAgentStub


def test_remote_agent_call_and_failure():
    """Remote agent stub should simulate success and failure."""
    assert RemoteAgentStub().call("node-a", {"task": "x"})["success"] is True
    failing = RemoteAgentStub(lambda target, payload: (_ for _ in ()).throw(RuntimeError("down")))
    assert failing.call("node-a", {})["success"] is False


def test_distributed_memory_read_write_failure():
    """Distributed memory stub should read/write and fail predictably."""
    memory = DistributedMemoryStub()
    assert memory.write("k", "v")["success"] is True
    assert memory.read("k")["value"] == "v"
    assert DistributedMemoryStub(fail=True).write("k", "v")["success"] is False


def test_distributed_orchestrator_and_cluster_no_network():
    """Distributed stubs should work without real network calls."""
    cluster = ClusterManagerStub()
    cluster.join("a")
    cluster.join("b")
    orchestrator = DistributedOrchestratorStub()
    for node in cluster.snapshot()["members"]:
        orchestrator.register_node(node)
    plan = orchestrator.plan_distribution(["t1", "t2", "t3"])
    assert sorted(plan.keys()) == ["a", "b"]
    assert sum(len(tasks) for tasks in plan.values()) == 3
