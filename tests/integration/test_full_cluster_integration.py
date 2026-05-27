"""Full ANA MAX OS cluster integration scenario."""

from pathlib import Path

from core.cluster_manager import ClusterManager, NodeState
from core.distributed_memory import DistributedMemory
from core.event_bus import EventBus
from core.fs_sync import FSSync


class FakeTransportMulti:
    """Deterministic in-memory multi-node transport."""

    def __init__(self):
        """Initialize per-node message queues."""
        self.queues = {}

    def register(self, node_id):
        """Register a node queue."""
        self.queues[node_id] = []

    def send(self, envelope):
        """Route an envelope to one node or all registered nodes."""
        target = envelope.get("target_node")
        if target == "*":
            for queue in self.queues.values():
                queue.append(envelope)
        elif target in self.queues:
            self.queues[target].append(envelope)

    def drain(self, node_id):
        """Return and clear queued messages for a node."""
        messages = list(self.queues[node_id])
        self.queues[node_id].clear()
        return messages


def create_node(node_id, transport, tmp_path):
    """Create one simulated ANA MAX OS node."""
    return {
        "id": node_id,
        "cluster": ClusterManager(node_id=node_id, transport=transport),
        "memory": DistributedMemory(node_id=node_id, transport=transport),
        "events": EventBus(node_id=node_id, transport=transport),
        "fs": FSSync(root_path=str(tmp_path / node_id), node_id=node_id, transport=transport),
    }


def dispatch_messages(node, transport):
    """Drain and dispatch all queued messages for a simulated node."""
    for envelope in transport.drain(node["id"]):
        msg_type = envelope.get("type", "")
        if msg_type.startswith("cluster."):
            node["cluster"].handle_cluster_message(envelope)
        elif msg_type.startswith("memory."):
            node["memory"].handle_memory_message(envelope)
        elif msg_type.startswith("event."):
            node["events"].handle_event_message(envelope)
        elif msg_type.startswith("fs."):
            node["fs"].handle_fs_message(envelope)


def file_tree(root_path):
    """Return file contents keyed by relative path."""
    root = Path(root_path)
    return {
        str(path.relative_to(root)).replace("\\", "/"): path.read_text(encoding="utf-8")
        for path in root.rglob("*")
        if path.is_file()
    }


def test_full_cluster_integration_scenario(tmp_path):
    """Exercise cluster, memory, FS, and event bus over FakeTransportMulti."""
    transport = FakeTransportMulti()
    transport.register("n1")
    transport.register("n2")
    n1 = create_node("n1", transport, tmp_path)
    n2 = create_node("n2", transport, tmp_path)

    n1["cluster"].join()
    dispatch_messages(n2, transport)
    assert n2["cluster"].nodes["n1"].state == NodeState.ACTIVE

    n2["cluster"].join()
    dispatch_messages(n1, transport)
    assert n1["cluster"].nodes["n2"].state == NodeState.ACTIVE

    n1["memory"].write("k1", "v1")
    dispatch_messages(n2, transport)
    assert n2["memory"].store["k1"] == "v1"

    n1["fs"].write_file("a.txt", "hello")
    dispatch_messages(n2, transport)
    assert (tmp_path / "n2" / "a.txt").read_text(encoding="utf-8") == "hello"

    received = []
    n2["events"].subscribe("cluster.test", lambda data: received.append(data))
    n1["events"].publish("cluster.test", {"x": 1})
    dispatch_messages(n2, transport)
    assert received == [{"x": 1}]

    n1["cluster"].send_heartbeat()
    dispatch_messages(n2, transport)
    assert n2["cluster"].nodes["n1"].state == NodeState.ACTIVE

    n2["cluster"].check_heartbeats(max_missed=1)
    assert n2["cluster"].nodes["n1"].state == NodeState.SUSPECT

    n1["cluster"].send_heartbeat()
    dispatch_messages(n2, transport)
    assert n2["cluster"].nodes["n1"].state == NodeState.ACTIVE

    n2["memory"].request_full_sync("n1")
    dispatch_messages(n1, transport)
    dispatch_messages(n2, transport)
    assert set(n2["memory"].store.keys()) == set(n1["memory"].store.keys())

    n2["fs"].request_full_fs_sync("n1")
    dispatch_messages(n1, transport)
    dispatch_messages(n2, transport)
    assert file_tree(tmp_path / "n2") == file_tree(tmp_path / "n1")
