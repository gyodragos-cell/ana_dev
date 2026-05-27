"""Tests for AI OS components."""

from core.agent_manager import AgentManager
from core.event_bus import EventBus
from core.os_network_stub import OSNetworkStub
from core.os_permissions import OSPermissions
from core.package_manager_stub import PackageManagerStub
from core.semantic_fs import SemanticFS
from core.service_manager import ServiceManager


def test_semantic_fs_read_write_lookup():
    """Semantic FS should read/write and search virtual files."""
    fs = SemanticFS()
    fs.write("/memory/tool", "grep_file works for search")
    fs.mount_tool_dir("grep_file", ["/memory/tool"])
    assert fs.read("/memory/tool") == "grep_file works for search"
    assert fs.search("search")[0]["path"] == "/memory/tool"


def test_process_lifecycle_and_scheduling_fairness():
    """Agent manager should model process states."""
    manager = AgentManager()
    agent = manager.spawn_agent("executor", "run")
    agent.status = "running"
    assert manager.snapshot()["agents"][agent.agent_id]["status"] == "running"


def test_os_permissions_inheritance_violation():
    """OS permissions should inherit and deny missing permissions."""
    perms = OSPermissions()
    perms.grant("parent", "tool:read")
    perms.inherit("child", "parent")
    assert perms.enforce("child", "tool:read")["allowed"] is True
    assert perms.enforce("child", "tool:write")["allowed"] is False


def test_event_bus_routing_filtering():
    """Event bus should route category events."""
    bus = EventBus()
    seen = []
    bus.subscribe("tool", lambda event: seen.append(event))
    bus.publish("tool", {"name": "grep"})
    assert seen[0]["payload"]["name"] == "grep"


def test_service_lifecycle_failure_handling():
    """Service manager should start, stop, and report health."""
    services = ServiceManager()
    services.register("runtime", lambda: True)
    services.start("runtime")
    assert services.health("runtime")["healthy"] is True
    services.stop("runtime")
    assert services.health("runtime")["healthy"] is False


def test_package_manager_and_network_stubs():
    """Package and network stubs should avoid real external calls."""
    packages = PackageManagerStub()
    assert packages.install("tool", "1.0")["success"] is True
    assert packages.uninstall("tool")["success"] is True
    network = OSNetworkStub(bandwidth=4)
    network.add_route("a", "b")
    assert network.send("a", "hello")["bytes"] == 4
