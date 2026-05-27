"""Tests for v27 distributed runtime components."""

from core.cluster_manager import ClusterManager
from core.distributed_memory import DistributedMemory, MemoryValue
from core.distributed_runtime import DistributedRuntime
from core.observability import Observability
from core.orchestrator import Orchestrator
from core.remote_execution import RemoteExecution
from core.scenario_simulator import ScenarioSimulator
from core.security_model import SecurityModel


def test_distributed_node_registration_message_failure():
    """Distributed runtime should register nodes and normalize failures."""
    runtime = DistributedRuntime()
    runtime.register_node("a", "planner")
    runtime.register_node("b", "executor")
    assert runtime.send_message("a", "b", "task", {"x": 1})["success"] is True
    failing = DistributedRuntime(lambda target, payload: (_ for _ in ()).throw(RuntimeError("down")))
    failing.register_node("a", "planner")
    failing.register_node("b", "executor")
    assert failing.send_message("a", "b", "task")["success"] is False


def test_remote_execution_success_failure_fallback():
    """Remote execution should retry/fallback."""
    ok = RemoteExecution()
    assert ok.call("node", "tool", {"x": 1})["success"] is True
    fallback = RemoteExecution(lambda n, t, a: {"success": False, "error": "nope"}, local_fallback=lambda t, a: {"success": True, "local": t})
    assert fallback.call("node", "tool")["local"] == "tool"


def test_distributed_memory_conflict_resolution():
    """Distributed memory should read/write and resolve conflicts."""
    memory = DistributedMemory()
    assert memory.write("k", "old", 1)["success"] is True
    assert memory.write("k", "older", 0)["success"] is False
    winner = memory.resolve_conflict("k", MemoryValue("left", 1), MemoryValue("right", 2))
    assert winner.value == "right"


def test_cluster_join_leave_failover():
    """Cluster manager should choose failover nodes."""
    cluster = ClusterManager()
    cluster.join("a")
    cluster.join("b")
    assert cluster.failover("a") == "b"
    assert cluster.leave("b") is True


def test_distributed_orchestrator_scheduling_dependencies():
    """Orchestrator should schedule across nodes."""
    orchestrator = Orchestrator()
    plan = orchestrator.schedule_across_nodes(["t1", "t2", "t3"], ["a", "b"])
    assert plan["a"] == ["t1", "t3"]


def test_security_model_permission_and_invalid_node():
    """Security model should reject invalid nodes and permissions."""
    security = SecurityModel({"node-a"}, {"node-a": {"execute"}})
    assert security.enforce("node-a", "execute")["allowed"] is True
    assert security.enforce("node-b", "execute")["allowed"] is False


def test_distributed_observability_and_scenarios():
    """Observability should aggregate node metrics and scenarios."""
    obs = Observability()
    obs.record_node_metrics("a", {"healthy": True})
    obs.record_node_metrics("b", {"healthy": False})
    assert obs.get_cluster_health()["status"] == "degraded"
    result = ScenarioSimulator().run_scenario("node_crash", {"task": "recover"}).to_dict()
    assert "node_failover" in result["notes"][0]
