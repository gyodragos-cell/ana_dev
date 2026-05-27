"""Integration tests for ANA MAX AI OS kernel components."""

from core.cluster_manager import ClusterManager
from core.dashboard_api import DashboardAPI
from core.distributed_memory import DistributedMemory
from core.distributed_runtime import DistributedRuntime
from core.event_bus import EventBus
from core.os_permissions import OSPermissions
from core.remote_execution import RemoteExecution
from core.security_model import SecurityModel
from core.semantic_fs import SemanticFS
from core.service_manager import ServiceManager


def test_remote_execution_timeout_and_local_fallback():
    """Remote execution should normalize timeout-like failures and fallback."""
    remote = RemoteExecution(
        transport=lambda node, tool, args: {"success": False, "error": "timeout"},
        local_fallback=lambda tool, args: {"success": True, "tool": tool, "local": True},
        retries=1,
    )
    result = remote.call("node-a", "grep_file", {"q": "needle"})
    assert result["success"] is True
    assert result["fallback_used"] is True
    assert result["attempts"] == 2


def test_distributed_memory_cross_node_replication():
    """Distributed memory should read/write across simulated nodes."""
    memory = DistributedMemory()
    assert memory.write("state", "ready", version=2, node_id="node-a")["success"] is True
    assert memory.replicate("node-a", "node-b", "state")["success"] is True
    assert memory.read("state", node_id="node-b")["value"] == "ready"


def test_cluster_runtime_routes_task_to_healthy_node():
    """Distributed runtime should route tasks through cluster and remote execution."""
    cluster = ClusterManager()
    remote = RemoteExecution(transport=lambda node, tool, args: {"success": True, "node": node, "tool": tool, "args": dict(args)})
    runtime = DistributedRuntime(cluster_manager=cluster, remote_execution=remote)
    runtime.register_node("node-a", "executor")
    result = runtime.route_task("grep_file", {"pattern": "class"})
    assert result["success"] is True
    assert result["routed_node"] == "node-a"


def test_event_bus_filtering_and_fanout():
    """Event bus should fan out wildcard subscribers and filter history."""
    bus = EventBus()
    seen = []
    bus.subscribe("*", lambda event: seen.append(event))
    bus.publish("cluster", {"node": "node-a"})
    assert seen[0]["category"] == "cluster"
    assert bus.filter_events("cluster", "node")[0]["payload"]["node"] == "node-a"


def test_semantic_fs_tags_permissions_security_and_services():
    """Core OS primitives should cooperate without real filesystem writes."""
    fs = SemanticFS()
    fs.write("/tools/grep", "grep_file compact search", tags=["tool", "search"])
    assert fs.search_by_tag("search")[0]["path"] == "/tools/grep"

    permissions = OSPermissions()
    permissions.grant("agent-a", "tool:grep_file")
    assert permissions.enforce("agent-a", "tool:grep_file")["allowed"] is True

    security = SecurityModel({"node-a"}, {"node-a": {"tool:grep_file"}}, denied_tools={"desktop_control"})
    assert security.enforce_tool("node-a", "grep_file")["allowed"] is True
    assert security.enforce_tool("node-a", "desktop_control")["allowed"] is False

    services = ServiceManager()
    services.register("dashboard", lambda: True)
    assert services.restart("dashboard")["restart_count"] == 1
    assert services.health("dashboard")["healthy"] is True


def test_dashboard_api_safe_snapshot():
    """Dashboard API should expose compact safe snapshots."""
    cluster = ClusterManager()
    cluster.join("node-a")
    services = ServiceManager()
    services.register("runtime")
    api = DashboardAPI({"cluster": cluster, "services": services})
    snapshot = api.snapshot()
    assert snapshot["nodes"]["nodes"]["node-a"]["healthy"] is True
    assert "runtime" in snapshot["services"]["services"]
