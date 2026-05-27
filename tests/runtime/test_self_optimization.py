"""Self-optimization routing feedback tests."""

from core.self_optimization import SelfOptimizationEngine
from core.tool_router import ToolRouter


def test_repeated_failures_lower_score():
    """Optimization should penalize repeated failures."""
    optimizer = SelfOptimizationEngine()
    optimizer.compute_snapshot(
        {
            "bad_tool": {
                "success_rate": 0.0,
                "failure_rate": 1.0,
                "avg_latency_ms": 3000,
                "noisy_tool_score": 0.8,
            }
        }
    )

    feedback = optimizer.get_tool_feedback("bad_tool")

    assert feedback["score_penalty"] > feedback["score_boost"]


def test_success_low_latency_gets_boost():
    """Optimization should boost successful low-latency tools."""
    optimizer = SelfOptimizationEngine()
    optimizer.compute_snapshot(
        {
            "good_tool": {
                "success_rate": 1.0,
                "failure_rate": 0.0,
                "avg_latency_ms": 10,
                "noisy_tool_score": 0.0,
            }
        }
    )

    feedback = optimizer.get_tool_feedback("good_tool")

    assert feedback["score_boost"] > 0
    assert feedback["reliability_score"] > 0.8


def test_noisy_tools_are_penalized_in_router():
    """Router should prefer quieter tools when optimizer feedback is available."""
    optimizer = SelfOptimizationEngine()
    optimizer.compute_snapshot(
        {
            "web_search": {"success_rate": 1.0, "failure_rate": 0.0, "avg_latency_ms": 10, "noisy_tool_score": 1.0},
            "grep_file": {"success_rate": 1.0, "failure_rate": 0.0, "avg_latency_ms": 10, "noisy_tool_score": 0.0},
        }
    )
    router = ToolRouter(health_monitor=optimizer)

    decision = router.select_tool(["web_search", "grep_file"], {"task": "search files"}, {"confidence": 0.8})

    assert decision.selected_tool == "grep_file"
