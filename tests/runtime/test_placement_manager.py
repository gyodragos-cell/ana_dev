"""Tests for model placement manager."""

from core.distributed_memory import DistributedMemory
from core.event_bus import EventBus
from core.placement_manager import PlacementManager


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


def test_set_and_get_placement_replicated():
    """Placement should replicate through distributed memory."""
    transport = FakeTransportMulti()
    transport.register("n1")
    transport.register("n2")
    memory1 = DistributedMemory(transport=transport, node_id="n1")
    memory2 = DistributedMemory(transport=transport, node_id="n2")
    placement1 = PlacementManager(memory1, EventBus())
    placement2 = PlacementManager(memory2, EventBus())
    placement1.set_placement("m1", "1", ["n1", "n2"])
    dispatch_memory(memory2, transport, "n2")
    assert placement2.get_placement("m1", "1")["nodes"] == ["n1", "n2"]


def test_list_placements_returns_all():
    """list_placements should return known placements."""
    placement = PlacementManager(DistributedMemory(), EventBus())
    placement.set_placement("m1", "1", "all")
    placement.set_placement("m2", "1", ["n2"])
    assert len(placement.list_placements()) == 2
