"""DevTools and cloud mode v1 tests."""

from core.debug_manager import DebugManager
from core.devtools_manager import DevToolsManager
from core.distributed_memory import DistributedMemory
from core.event_bus import EventBus
from core.federation_manager import FederationManager
from core.fs_sync import FSSync
from core.profiler_manager import ProfilerManager
from core.routing_manager import RoutingManager


def test_devtools_debug_profile_fs_and_memory(tmp_path):
    """DevTools should expose simulated debug, profile, FS, and memory operations."""
    events = EventBus()
    memory = DistributedMemory()
    fs_sync = FSSync(tmp_path)
    fs_sync.write_file("a.txt", "hello")
    debug = DebugManager(events, {"memory": memory, "fs": fs_sync})
    assert debug.set_breakpoint("n1", "memory") is True
    assert debug.inspect_state("n1", "memory")["target"] == "memory"
    profiler = ProfilerManager(events)
    profiler.start_profile("n1", "router")
    assert profiler.collect_profile("n1", "router")["samples"]
    assert profiler.stop_profile("n1", "router")["running"] is False

    devtools = DevToolsManager(events, fs_sync, memory)
    devtools.subscribe_logs("log.entry")
    devtools.emit_log("ready")
    assert devtools.fs_list() == ["a.txt"]
    assert devtools.fs_read("a.txt") == "hello"
    devtools.fs_write("b.txt", "world")
    devtools.memory_set("k", "v")
    assert devtools.memory_get("k") == "v"
    assert "k" in devtools.memory_list()


def test_cloud_federation_and_cross_cluster_routing():
    """Cloud mode should route across simulated cluster domains."""
    local = FederationManager("c1", "eu")
    local.receive_state({"cluster_id": "c2", "domain": "us", "status": "ok"})
    router = RoutingManager(local)
    assert local.heartbeat()["type"] == "federation.heartbeat"
    assert router.route_across_clusters({"domain": "us"})["cluster_id"] == "c2"
    assert router.route_across_clusters({"domain": "eu"})["cluster_id"] == "c1"
