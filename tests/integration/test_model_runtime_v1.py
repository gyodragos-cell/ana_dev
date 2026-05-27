"""Model runtime v1 integration tests."""

from core.cluster_manager import ClusterManager, ClusterNode
from core.distributed_memory import DistributedMemory
from core.event_bus import EventBus
from core.inference_dispatcher import InferenceDispatcher
from core.metrics_manager import MetricsManager
from core.model_loader import ModelLoader
from core.model_registry import ModelRegistry
from core.model_router import ModelRouter
from core.placement_manager import PlacementManager
from core.recovery_manager import RecoveryManager


class FakeTransport:
    """Single queue fake transport."""

    def __init__(self):
        """Initialize sent envelopes."""
        self.sent = []

    def send(self, envelope):
        """Record one envelope."""
        self.sent.append(envelope)


def test_model_registry_loader_placement_routing_and_inference():
    """Model runtime should register, place, route, dispatch, and measure."""
    memory = DistributedMemory()
    events = EventBus()
    metrics = MetricsManager(events)
    registry = ModelRegistry(memory, events)
    registry.register_model("tiny", "1", "/models/tiny", ["cpu", "llm"], ["hot"])
    registry.register_model("tiny", "2", "/models/tiny2", ["gpu", "llm"], ["canary"])
    registry.set_canary_weights("tiny", {"1": 90, "2": 10})
    assert registry.get_model("tiny", "1")["capabilities"] == ["cpu", "llm"]
    assert registry.choose_version("tiny", bucket=95) == "2"
    assert "model:tiny:1" in memory.store
    assert registry.unregister_model("tiny", "2") is True

    loader = ModelLoader("n1")
    handle = loader.load_model("tiny", "1")
    assert loader.load_model("tiny", "1") is handle
    assert loader.warmup_model("tiny", "1").warmed is True
    assert loader.unload_model(handle) is True

    cluster = ClusterManager()
    cluster.nodes["n1"] = ClusterNode("n1", capabilities=["cpu"])
    cluster.nodes["n2"] = ClusterNode("n2", capabilities=["gpu"], healthy=False)
    placement = PlacementManager(memory, events)
    placement.set_placement("tiny", "1", ["n1"])
    router = ModelRouter(registry, placement, cluster)
    route = router.route_inference("tiny", "1", "cpu", session_id="s1")
    assert route["node_id"] == "n1"
    assert router.route_inference("tiny", "1", "cpu", session_id="s1")["sticky"] is True

    transport = FakeTransport()
    dispatcher = InferenceDispatcher(router, transport, events, metrics, node_id="origin")
    request_id = dispatcher.submit_inference("tiny", "hello", version="1", capability="cpu")
    assert transport.sent[-1]["type"] == "model.infer.request"
    dispatcher.handle_inference_response({"payload": {"request_id": request_id, "output": "ok"}})
    assert dispatcher.responses[request_id] == "ok"
    assert dispatcher.submit_batch("tiny", ["a", "b"])
    dispatcher.cancel_inference(request_id)
    dispatcher.check_timeout("missing")
    assert metrics.snapshot()["model.tiny.requests"] >= 3


def test_model_recovery_restores_placement_snapshot():
    """Recovery manager should accept model placement snapshots as memory state."""
    memory = DistributedMemory()
    placement = PlacementManager(memory)
    placement.set_placement("tiny", "1", ["n1"])
    fresh = DistributedMemory()
    result = RecoveryManager(fresh).restore({"memory": memory.snapshot()})
    assert result["success"] is True
    assert "placement:tiny:1" in fresh.store
