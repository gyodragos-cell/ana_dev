"""Service runtime v2 tests."""

from core.distributed_memory import DistributedMemory
from core.event_bus import EventBus
from core.service_manager import ServiceManager


def test_service_v2_metadata_scaling_summary_and_events():
    """Service manager v2 should track metadata and summaries."""
    memory = DistributedMemory()
    events = EventBus()
    seen = []
    events.subscribe("service.start", lambda event: seen.append(event))
    services = ServiceManager(memory, events, node_id="n1")
    services.configure_service("api", dependencies=["db"], priority=1, annotations={"tier": "frontend"})
    services.scale_service("api", 3)
    services.start_service("api")
    summary = services.service_summary()
    assert summary["count"] == 1
    assert summary["running"] == 1
    assert summary["services"]["api"]["dependencies"] == ["db"]
    assert summary["services"]["api"]["annotations"]["replicas"] == 3
    assert seen
