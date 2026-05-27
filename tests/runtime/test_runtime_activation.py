"""ANA MAX runtime activation tests."""

from core.ana_runtime import build_demo_runtime
from core.context_builder import ContextBuilder
from core.input_layer import InputLayer


def test_context_builder_collects_real_workspace_state(tmp_path):
    """Context builder should inspect a real workspace path compactly."""
    envelope = InputLayer(tmp_path).normalize({"task": "inspect", "workspace": str(tmp_path)})

    context = ContextBuilder().build_context(envelope).to_dict()

    assert context["workspace_state"]["exists"] is True
    assert context["workspace_state"]["is_dir"] is True
    assert context["confidence"] >= 0.45


def test_demo_runtime_executes_single_cycle(tmp_path):
    """Demo runtime should execute without a live MCP server."""
    runtime = build_demo_runtime(str(tmp_path))

    summary = runtime.run({"task": "inspect workspace", "workspace": str(tmp_path)})
    data = summary.to_dict()

    assert data["success"] is True
    assert data["result"]["latency_ms"] >= 0
    assert runtime.observability.get_health_snapshot()["total_tool_calls"] == 1


# TODO(v23): add real MCP bridge integration tests behind an explicit marker.
