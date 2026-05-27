"""Tests for model registry v1."""

from core.distributed_memory import DistributedMemory
from core.event_bus import EventBus
from core.model_registry import ModelRegistry


class FakeTransportMulti:
    """In-memory transport with queues per node."""

    def __init__(self):
        """Initialize queues."""
        self.queues = {}

    def register(self, node_id):
        """Register a queue."""
        self.queues[node_id] = []

    def send(self, envelope):
        """Route one envelope."""
        target = envelope.get("target_node")
        targets = self.queues if target == "*" else [target]
        for node_id in targets:
            if node_id in self.queues:
                self.queues[node_id].append(envelope)

    def drain(self, node_id):
        """Drain one queue."""
        messages = list(self.queues[node_id])
        self.queues[node_id].clear()
        return messages


def dispatch_memory(memory, transport, node_id):
    """Dispatch memory messages for one node."""
    for envelope in transport.drain(node_id):
        if str(envelope.get("type", "")).startswith("memory."):
            memory.handle_memory_message(envelope)


def test_register_and_get_model_replicated_across_nodes():
    """Registering on one node should replicate metadata to another node."""
    transport = FakeTransportMulti()
    transport.register("n1")
    transport.register("n2")
    memory1 = DistributedMemory(transport=transport, node_id="n1")
    memory2 = DistributedMemory(transport=transport, node_id="n2")
    registry1 = ModelRegistry(memory1, EventBus())
    registry2 = ModelRegistry(memory2, EventBus())

    registry1.register_model("m1", "1", {"capabilities": ["cpu"], "tags": ["test"], "path": "/m1", "node_id": "n1"})
    dispatch_memory(memory2, transport, "n2")

    model = registry2.get_model("m1", "1")
    assert model is not None
    assert model["name"] == "m1"
    assert model["capabilities"] == ["cpu"]


def test_unregister_removes_model():
    """Unregistering should remove local registry entries."""
    registry = ModelRegistry(DistributedMemory(), EventBus())
    registry.register_model("m1", "1", {"path": "/m1"})
    assert registry.unregister_model("m1", "1") is True
    assert registry.get_model("m1", "1") is None


def test_list_models_returns_all():
    """list_models should return all registered models."""
    registry = ModelRegistry(DistributedMemory(), EventBus())
    registry.register_model("m1", "1", {"path": "/m1"})
    registry.register_model("m2", "1", {"path": "/m2"})
    names = {model["name"] for model in registry.list_models()}
    assert names == {"m1", "m2"}
