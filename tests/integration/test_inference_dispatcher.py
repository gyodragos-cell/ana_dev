"""Integration tests for inference dispatcher v1."""

from core.cluster_manager import ClusterManager, ClusterNode
from core.distributed_memory import DistributedMemory
from core.event_bus import EventBus
from core.inference_dispatcher import InferenceDispatcher
from core.model_registry import ModelRegistry
from core.model_router import ModelRouter
from core.placement_manager import PlacementManager


class FakeTransportMulti:
    """In-memory transport with queues per node."""

    def __init__(self):
        """Initialize queues."""
        self.queues = {}

    def register(self, node_id):
        """Register a node queue."""
        self.queues[node_id] = []

    def send(self, envelope):
        """Route one envelope."""
        target = envelope.get("target_node")
        targets = self.queues if target == "*" else [target]
        for node_id in targets:
            if node_id in self.queues:
                self.queues[node_id].append(envelope)

    def drain(self, node_id):
        """Drain one node queue."""
        messages = list(self.queues[node_id])
        self.queues[node_id].clear()
        return messages


def create_node(node_id, transport, placement_nodes):
    """Create a simulated model runtime node."""
    memory = DistributedMemory(transport=transport, node_id=node_id)
    events = EventBus(transport=transport, node_id=node_id)
    registry = ModelRegistry(memory, events)
    registry.register_model("m1", "1", {"path": "/m1", "capabilities": ["cpu"], "node_id": node_id})
    placement = PlacementManager(memory, events)
    placement.set_placement("m1", "1", placement_nodes)
    cluster = ClusterManager(node_id=node_id, transport=transport)
    cluster.nodes["n1"] = ClusterNode("n1", capabilities=["cpu"])
    cluster.nodes["n2"] = ClusterNode("n2", capabilities=["cpu"])
    router = ModelRouter(registry, placement, cluster)
    dispatcher = InferenceDispatcher(router, transport=transport, event_bus=events, node_id=node_id)
    return {"memory": memory, "registry": registry, "placement": placement, "cluster": cluster, "dispatcher": dispatcher}


def dispatch_inference(node, transport, node_id):
    """Dispatch inference messages for one node."""
    for envelope in transport.drain(node_id):
        if envelope.get("type") == "model.infer.request":
            node["dispatcher"].handle_inference_request(envelope)
        elif envelope.get("type") == "model.infer.response":
            node["dispatcher"].handle_inference_response(envelope)


def test_remote_inference_request_and_response():
    """n1 should route inference to n2 and receive the response."""
    transport = FakeTransportMulti()
    transport.register("n1")
    transport.register("n2")
    n1 = create_node("n1", transport, ["n2"])
    n2 = create_node("n2", transport, ["n2"])
    request_id = n1["dispatcher"].submit_inference("m1", {"x": 1}, version="1")
    dispatch_inference(n2, transport, "n2")
    dispatch_inference(n1, transport, "n1")
    result = n1["dispatcher"].get_result(request_id)
    assert result["output"]["echo"]["x"] == 1
    assert result["output"]["model"] == "m1"


def test_local_inference_when_placement_points_to_local_node():
    """Local placement should resolve without transport round trip."""
    transport = FakeTransportMulti()
    transport.register("n1")
    n1 = create_node("n1", transport, ["n1"])
    request_id = n1["dispatcher"].submit_inference("m1", "hello", version="1")
    assert n1["dispatcher"].get_result(request_id)["output"]["echo"] == "hello"


def test_multiple_requests_all_resolved():
    """Multiple remote requests should each receive results."""
    transport = FakeTransportMulti()
    transport.register("n1")
    transport.register("n2")
    n1 = create_node("n1", transport, ["n2"])
    n2 = create_node("n2", transport, ["n2"])
    request_ids = [n1["dispatcher"].submit_inference("m1", {"i": i}, version="1") for i in range(3)]
    dispatch_inference(n2, transport, "n2")
    dispatch_inference(n1, transport, "n1")
    assert [n1["dispatcher"].get_result(request_id)["output"]["echo"]["i"] for request_id in request_ids] == [0, 1, 2]


def test_no_model_or_no_route_graceful_failure():
    """Missing model should produce a stored error result."""
    transport = FakeTransportMulti()
    transport.register("n1")
    n1 = create_node("n1", transport, ["n1"])
    request_id = n1["dispatcher"].submit_inference("missing", {"x": 1}, version="1")
    assert n1["dispatcher"].get_result(request_id)["error"] == "no route"
