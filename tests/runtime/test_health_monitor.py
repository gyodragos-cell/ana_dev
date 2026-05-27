"""ANA MAX v23 health monitor tests."""

from core.health_monitor import ToolHealthMonitor
from core.tool_router import ToolRouter


def test_health_monitor_records_reliability_shape():
    """Health monitor should expose router-friendly feedback."""
    monitor = ToolHealthMonitor()

    monitor.record_tool_result("grep_file", latency_ms=10, output_bytes=100, success=True)
    feedback = monitor.get_tool_feedback("grep_file")

    assert feedback["calls"] == 1
    assert feedback["reliability_score"] > 0
    assert feedback["noisy_tool_score"] >= 0


def test_router_uses_health_monitor_feedback():
    """Router should prefer healthier tools when base scores are similar."""
    monitor = ToolHealthMonitor()
    monitor.record_tool_result("grep_file", latency_ms=10, output_bytes=100, success=True)
    monitor.record_tool_result("web_search", latency_ms=5000, output_bytes=50000, success=False)
    router = ToolRouter(health_monitor=monitor)

    decision = router.select_tool(["web_search", "grep_file"], {"task": "search files"}, {"confidence": 0.8})

    assert decision.selected_tool == "grep_file"


# TODO(v23): add rolling-window health decay and persistence tests.
