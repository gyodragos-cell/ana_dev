"""Tests for cluster membership over the transport protocol."""

from core.cluster_manager import ClusterManager, ClusterNode, NodeState


class FakeTransport:
    """In-memory transport for isolated cluster tests."""

    def __init__(self) -> None:
        """Initialize sent envelope storage."""
        self.sent = []

    def send(self, envelope):
        """Record a sent envelope."""
        self.sent.append(envelope)


def test_join_sends_cluster_join_message():
    """join() should announce this node over transport."""
    transport = FakeTransport()
    manager = ClusterManager(node_id="n1", transport=transport)
    manager.join()
    assert len(transport.sent) == 1
    assert transport.sent[0]["type"] == "cluster.join"
    assert transport.sent[0]["payload"]["node_id"] == "n1"


def test_leave_sends_cluster_leave_message():
    """leave() should announce this node leaving over transport."""
    transport = FakeTransport()
    manager = ClusterManager(node_id="n1", transport=transport)
    manager.join()
    manager.leave(reason="shutdown")
    assert transport.sent[-1]["type"] == "cluster.leave"
    assert transport.sent[-1]["payload"]["node_id"] == "n1"
    assert transport.sent[-1]["payload"]["reason"] == "shutdown"


def test_handle_join_registers_node():
    """Incoming join envelopes should register and activate nodes."""
    manager = ClusterManager(node_id="n0")
    manager.handle_cluster_message(
        {
            "version": 1,
            "type": "cluster.join",
            "source_node": "n2",
            "target_node": "*",
            "timestamp": "now",
            "payload": {"node_id": "n2", "address": "127.0.0.1", "port": 0, "capabilities": []},
        }
    )
    assert "n2" in manager.nodes
    assert manager.nodes["n2"].state == NodeState.ACTIVE


def test_handle_heartbeat_uses_existing_heartbeat_logic():
    """Incoming heartbeat envelopes should reactivate suspect nodes."""
    manager = ClusterManager(node_id="n0")
    manager.nodes["n2"] = ClusterNode("n2", state=NodeState.SUSPECT)
    manager.handle_cluster_message(
        {
            "version": 1,
            "type": "cluster.heartbeat",
            "source_node": "n2",
            "target_node": "*",
            "timestamp": "now",
            "payload": {"node_id": "n2"},
        }
    )
    assert manager.nodes["n2"].state == NodeState.ACTIVE


def test_check_heartbeats_marks_suspect_and_dead():
    """Missed heartbeats should move ACTIVE to SUSPECT, then DEAD."""
    manager = ClusterManager(node_id="n0")
    manager.nodes["n2"] = ClusterNode("n2", state=NodeState.ACTIVE)
    manager.check_heartbeats(max_missed=1)
    assert manager.nodes["n2"].state == NodeState.SUSPECT
    manager.check_heartbeats(max_missed=1)
    assert manager.nodes["n2"].state == NodeState.DEAD
