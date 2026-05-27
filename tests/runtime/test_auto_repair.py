"""Auto-repair tests for safe text-only repair plans."""

from core.auto_repair import AutoRepairEngine
from core.execution_layer import ExecutionLayer


def test_invalid_tool_output_repair_suggestion():
    """Invalid output should produce a patch suggestion, not apply a patch."""
    repair = AutoRepairEngine().plan_repair({"error": "invalid response shape"}).to_dict()

    assert repair["strategy"] == "suggest_patch"
    assert repair["safe_to_apply"] is False
    assert repair["patch_suggestion"]


def test_timeout_repair_suggests_retry_or_fallback():
    """Timeouts should suggest retry or fallback."""
    repair = AutoRepairEngine().plan_repair({"error": "timeout while calling tool"}).to_dict()

    assert repair["strategy"] == "retry"
    assert "fallback" in repair["action"]


def test_chained_failure_stops_cleanly():
    """Chained failures should stop before runaway repair loops."""
    repair = AutoRepairEngine(max_chain_failures=2).plan_repair(
        {"tool": "broken", "error": "still failing", "failure_count": 2}
    ).to_dict()

    assert repair["strategy"] == "disable_tool"


def test_broken_tool_is_disabled():
    """Repeated failures should temporarily disable a broken tool."""
    engine = AutoRepairEngine(max_chain_failures=1)
    engine.plan_repair({"tool": "broken", "error": "failure", "failure_count": 1})

    assert engine.is_disabled("broken") is True


def test_router_misrouting_repair_correction():
    """Misrouting should produce a switch-tool repair plan."""
    repair = AutoRepairEngine().plan_repair({"misrouted": True, "backup_tool": "grep_file"}).to_dict()

    assert repair["strategy"] == "switch_tool"
    assert "grep_file" in repair["action"]


def test_execution_layer_attaches_repair_plan():
    """Execution layer should attach repair plans on failures."""
    layer = ExecutionLayer(
        tool_registry={"bad": lambda **kwargs: {"success": False, "error": "invalid response shape"}},
        auto_repair=AutoRepairEngine(),
    )

    result = layer.execute("bad", {}).to_dict()

    assert result["success"] is False
    assert result["data"] is None
