"""Agent runtime v1 integration tests."""

from core.agent_manager import AgentManager
from core.cluster_manager import ClusterManager, ClusterNode
from core.distributed_memory import DistributedMemory
from core.event_bus import EventBus
from core.fs_sync import FSSync
from core.task_manager import TaskManager


def test_agent_registry_messaging_lifecycle_and_persistence(tmp_path):
    """Agent runtime should register, message, persist, and integrate with tasks/FS/memory."""
    memory = DistributedMemory()
    events = EventBus()
    cluster = ClusterManager()
    cluster.nodes["n1"] = ClusterNode("n1")
    tasks = TaskManager(cluster, memory, events)
    fs_sync = FSSync(tmp_path)
    agents = AgentManager(memory, events, cluster, fs_sync, tasks)

    agents.register_agent("planner", {"role": "planner"})
    started = agents.start_agent("planner")
    assert started["state"] == "running"
    message = agents.route_message("planner", "hello", sender="operator")
    assert message["content"] == "hello"
    agents.agent_write_memory("planner", "note", "remember")
    agents.agent_write_file("planner", "agent.txt", "ok")
    task = agents.submit_agent_task("planner", {"name": "do"})
    assert task.node_id == "n1"
    assert "agent:planner" in memory.store
    assert (tmp_path / "agent.txt").exists()
    assert agents.stop_agent("planner")["state"] == "stopped"
    assert agents.restart_agent("planner")["state"] == "running"
    assert agents.unregister_agent("planner") is True
