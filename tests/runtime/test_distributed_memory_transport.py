"""Tests for distributed memory transport sync."""

from core.distributed_memory import DistributedMemory


class FakeTransport:
    """In-memory transport for memory sync tests."""

    def __init__(self):
        """Initialize sent envelope storage."""
        self.sent = []

    def send(self, envelope):
        """Record one envelope."""
        self.sent.append(envelope)


def test_write_broadcasts_when_transport_set():
    """Local write should broadcast a memory.write message."""
    transport = FakeTransport()
    memory = DistributedMemory(transport=transport, node_id="n1")
    memory.write("k1", "v1")
    assert len(transport.sent) == 1
    assert transport.sent[0]["type"] == "memory.write"
    assert transport.sent[0]["payload"]["key"] == "k1"


def test_write_no_transport_no_error():
    """Local write should keep old behavior when transport is absent."""
    memory = DistributedMemory()
    result = memory.write("k1", "v1")
    assert result["success"] is True


def test_handle_remote_write_stores_value():
    """Incoming remote writes should store source values."""
    memory = DistributedMemory(node_id="n0")
    envelope = {
        "version": 1,
        "type": "memory.write",
        "source_node": "n2",
        "target_node": "n0",
        "timestamp": "2025-01-01T00:00:00Z",
        "payload": {"key": "x", "value": "y"},
    }
    memory.handle_memory_message(envelope)
    assert memory.store.get("x") == "y"


def test_pull_request_returns_known_keys():
    """Pull request should return known keys to the source node."""
    transport = FakeTransport()
    memory = DistributedMemory(transport=transport, node_id="n0")
    memory.store["k"] = "v"
    envelope = {
        "version": 1,
        "type": "memory.pull_request",
        "source_node": "n2",
        "target_node": "n0",
        "timestamp": "2025-01-01T00:00:00Z",
        "payload": {"node_id": "n2", "keys": None},
    }
    memory.handle_memory_message(envelope)
    assert len(transport.sent) == 1
    assert transport.sent[0]["type"] == "memory.pull_response"


def test_full_sync_sends_pull_request():
    """Full sync should send a memory.pull_request envelope."""
    transport = FakeTransport()
    memory = DistributedMemory(transport=transport, node_id="n1")
    memory.request_full_sync("n0")
    assert len(transport.sent) == 1
    assert transport.sent[0]["type"] == "memory.pull_request"
    assert transport.sent[0]["target_node"] == "n0"


def test_conflict_uses_resolve_conflict():
    """Remote write conflicts should use the conflict hook."""

    class TestDM(DistributedMemory):
        """DistributedMemory with observable conflict calls."""

        def __init__(self):
            """Initialize conflict tracking."""
            super().__init__(node_id="n0")
            self.conflicts = []

        def resolve_conflict(self, local, remote):  # noqa: D102
            self.conflicts.append((local, remote))
            return remote

    memory = TestDM()
    memory.store["k"] = "old"
    envelope = {
        "version": 1,
        "type": "memory.write",
        "source_node": "n2",
        "target_node": "n0",
        "timestamp": "2025-01-01T00:00:00Z",
        "payload": {"key": "k", "value": "new"},
    }
    memory.handle_memory_message(envelope)
    assert memory.store["k"] == "new"
    assert memory.conflicts == [("old", "new")]
