"""Distributed kernel v23 integration tests."""

from pathlib import Path

from core.cluster_manager import ClusterManager, ClusterNode, NodeState
from core.distributed_memory import DistributedMemory
from core.event_bus import EventBus
from core.fs_sync import FSSync
from core.lock_manager import LockManager
from core.metrics_manager import MetricsManager
from core.recovery_manager import RecoveryManager
from core.service_manager import ServiceManager
from core.task_manager import TaskManager


class FakeTransportMulti:
    """Fake transport with optional partitions."""

    def __init__(self):
        """Initialize queues and blocked links."""
        self.queues = {}
        self.blocked = set()

    def register(self, node_id):
        """Register a node queue."""
        self.queues[node_id] = []

    def disconnect(self, node_a, node_b):
        """Block traffic both ways."""
        self.blocked.add((node_a, node_b))
        self.blocked.add((node_b, node_a))

    def reconnect(self, node_a, node_b):
        """Restore traffic both ways."""
        self.blocked.discard((node_a, node_b))
        self.blocked.discard((node_b, node_a))

    def send(self, envelope):
        """Route an envelope if not partitioned."""
        source = envelope.get("source_node")
        target = envelope.get("target_node")
        targets = list(self.queues) if target == "*" else [target]
        for item in targets:
            if item in self.queues and (source, item) not in self.blocked:
                self.queues[item].append(envelope)

    def drain(self, node_id):
        """Drain queued messages."""
        messages = list(self.queues[node_id])
        self.queues[node_id].clear()
        return messages


def dispatch(node, transport):
    """Dispatch all messages for a node."""
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


def make_node(node_id, transport, tmp_path, mode="eventual"):
    """Build a simulated node."""
    events = EventBus(transport=transport, node_id=node_id)
    memory = DistributedMemory(transport=transport, node_id=node_id, mode=mode)
    cluster = ClusterManager(node_id=node_id, transport=transport, event_bus=events)
    fs_sync = FSSync(tmp_path / node_id, transport=transport, node_id=node_id, mode=mode)
    return {"id": node_id, "events": events, "memory": memory, "cluster": cluster, "fs": fs_sync}


def test_node_health_monitor_and_adaptive_routing():
    """Health monitor should mark suspect/recovered and routing should skip bad nodes."""
    events = EventBus()
    seen = []
    events.subscribe("node.unhealthy", lambda event: seen.append(event))
    events.subscribe("routing.changed", lambda event: seen.append(event))
    cluster = ClusterManager(event_bus=events)
    cluster.nodes["n1"] = ClusterNode("n1", capabilities=["cpu"])
    cluster.nodes["n2"] = ClusterNode("n2", capabilities=["cpu"])
    cluster.mark_unhealthy("n1", reason="missed")
    assert cluster.nodes["n1"].state == NodeState.SUSPECT
    assert cluster.get_best_node("cpu") == "n2"
    cluster.mark_recovered("n1", reason="heartbeat")
    assert cluster.nodes["n1"].state == NodeState.ACTIVE
    assert any(event == {"node_id": "n1", "reason": "missed"} for event in seen)


def test_service_manager_replication_failover_and_restart():
    """Services should replicate, fail over, and emit restart events."""
    memory = DistributedMemory()
    events = EventBus()
    seen = []
    events.subscribe("service.crash", lambda event: seen.append(event))
    cluster = ClusterManager()
    cluster.nodes["n1"] = ClusterNode("n1")
    cluster.nodes["n2"] = ClusterNode("n2")
    services = ServiceManager(memory, events, cluster, node_id="n1")
    started = services.start_service("api", node_id="n1")
    assert started["running"] is True
    assert "service:api" in memory.store
    services.failover_services("n1")
    assert services.services["api"].node_id == "n2"
    services.restart_service("api")
    assert seen


def test_lock_manager_acquire_ttl_and_release():
    """Only one owner should acquire a lock until release or TTL expiry."""
    memory = DistributedMemory()
    events = EventBus()
    locks = LockManager(memory, events, node_id="n1")
    assert locks.acquire("resource", "n1", ttl=30) is True
    assert locks.acquire("resource", "n2", ttl=30) is False
    assert locks.release("resource", "n1") is True
    assert locks.acquire("short", "n1", ttl=-1) is True
    locks.check_expired()
    assert locks.is_locked("short") is False


def test_task_manager_submit_retry_cancel():
    """Task manager should route, retry failed tasks, and cancel."""
    cluster = ClusterManager()
    cluster.nodes["worker"] = ClusterNode("worker", capabilities=["job"])
    memory = DistributedMemory()
    events = EventBus()
    tasks = TaskManager(cluster, memory, events)
    record = tasks.submit({"capability": "job"})
    assert record.node_id == "worker"
    failed = tasks.execute(record.task_id, handler=lambda payload: (_ for _ in ()).throw(RuntimeError("boom")))
    assert failed["status"] == "failed"
    retried = tasks.retry(record.task_id)
    assert retried["status"] == "completed"
    cancelled = tasks.cancel(record.task_id)
    assert cancelled["status"] == "cancelled"


def test_join_sync_leave_cleanup_partition_and_modes(tmp_path):
    """Sync, cleanup, partition divergence, heal, and consistency modes should work."""
    transport = FakeTransportMulti()
    transport.register("n1")
    transport.register("n2")
    n1 = make_node("n1", transport, tmp_path)
    n2 = make_node("n2", transport, tmp_path)
    n1["memory"].write("shared", "one")
    n1["fs"].write_file("a.txt", "one")
    dispatch(n2, transport)
    assert n2["memory"].read("shared")["value"] == "one"
    assert (tmp_path / "n2" / "a.txt").exists()

    transport.disconnect("n1", "n2")
    n1["memory"].write("split", "left")
    n2["memory"].write("split", "right")
    assert n1["memory"].read("split")["value"] == "left"
    assert n2["memory"].read("split")["value"] == "right"

    transport.reconnect("n1", "n2")
    n2["memory"].request_full_sync("n1")
    dispatch(n1, transport)
    dispatch(n2, transport)
    assert "shared" in n2["memory"].store

    assert n2["memory"].remove_node("n1") is True
    n2["fs"].cleanup_node("n1")
    strong = DistributedMemory(transport=transport, node_id="strong", mode="strong_local")
    strong.write("local", "only")
    assert transport.drain("n1") == []


def test_full_system_v2_three_nodes(tmp_path):
    """Run a compact 3-node system scenario with core v23 primitives."""
    transport = FakeTransportMulti()
    for node_id in ("n1", "n2", "n3"):
        transport.register(node_id)
    nodes = {node_id: make_node(node_id, transport, tmp_path) for node_id in ("n1", "n2", "n3")}
    for node in nodes.values():
        for peer in ("n1", "n2", "n3"):
            node["cluster"].nodes[peer] = ClusterNode(peer)

    services = ServiceManager(nodes["n1"]["memory"], nodes["n1"]["events"], nodes["n1"]["cluster"], node_id="n1")
    locks = LockManager(nodes["n1"]["memory"], nodes["n1"]["events"], node_id="n1")
    tasks = TaskManager(nodes["n1"]["cluster"], nodes["n1"]["memory"], nodes["n1"]["events"])
    services.start_service("api", node_id="n1")
    assert locks.acquire("deploy", "n1")
    task = tasks.submit({"name": "build"})
    assert tasks.execute(task.task_id)["success"] is True
    nodes["n1"]["fs"].write_file("state.txt", "ok")
    dispatch(nodes["n2"], transport)
    assert nodes["n2"]["memory"].read("service:api")["success"] is True


def test_observability_logs_debug_and_recovery(tmp_path):
    """Metrics, logs, debug events, snapshots, and recovery should be available."""
    events = EventBus()
    received = []
    events.subscribe("log.entry", lambda event: received.append(event))
    events.subscribe("debug.inspect", lambda event: received.append(event))
    metrics = MetricsManager(events)
    assert metrics.increment("events.sent") == 1
    events.publish("log.entry", {"message": "hello"})
    events.publish("debug.inspect", {"target": "memory"})
    assert {"message": "hello"} in received
    assert {"target": "memory"} in received

    memory = DistributedMemory()
    services = ServiceManager(memory)
    locks = LockManager(memory)
    services.start_service("api", node_id="n1")
    locks.acquire("k", "n1")
    snapshot = {"memory": memory.snapshot(), "services": services.snapshot(), "locks": locks.snapshot()}
    fresh_memory = DistributedMemory()
    fresh_services = ServiceManager(fresh_memory)
    fresh_locks = LockManager(fresh_memory)
    result = RecoveryManager(fresh_memory, None, fresh_services, fresh_locks).restore(snapshot)
    assert result["success"] is True
    assert "api" in fresh_services.services
