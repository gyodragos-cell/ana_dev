"""Adaptive router v23 tests."""

from core.self_optimization import SelfOptimizationEngine
from core.tool_router import ToolRouter


def test_adaptive_routing_improves_over_time():
    """Recorded success patterns should influence scenario fit."""
    router = ToolRouter()
    for _ in range(3):
        router.select_tool(["grep_file", "web_search"], {"task": "search files"}, {"confidence": 0.8})
        router.record_routing_result("grep_file", True, scenario="file_search")

    score = router.score_tool("grep_file", {"task": "search files", "scenario": "file_search"}, {"confidence": 0.8})

    assert score.scenario_fit == 1.0


def test_noisy_tools_penalized_by_optimizer():
    """Optimizer feedback should reduce noisy tool scores."""
    optimizer = SelfOptimizationEngine()
    optimizer.compute_snapshot(
        {
            "noisy": {"success_rate": 1.0, "failure_rate": 0.0, "avg_latency_ms": 50, "noisy_tool_score": 1.0},
            "quiet": {"success_rate": 1.0, "failure_rate": 0.0, "avg_latency_ms": 50, "noisy_tool_score": 0.0},
        }
    )
    router = ToolRouter(health_monitor=optimizer)

    noisy = router.score_tool("noisy", {"task": "read"}, {"confidence": 0.8})
    quiet = router.score_tool("quiet", {"task": "read"}, {"confidence": 0.8})

    assert quiet.total > noisy.total


def test_reliable_tools_are_boosted():
    """Reliable tools should score higher than failing tools."""
    optimizer = SelfOptimizationEngine()
    optimizer.compute_snapshot(
        {
            "stable": {"success_rate": 1.0, "failure_rate": 0.0, "avg_latency_ms": 10, "noisy_tool_score": 0.0},
            "failing": {"success_rate": 0.0, "failure_rate": 1.0, "avg_latency_ms": 10, "noisy_tool_score": 0.2},
        }
    )
    router = ToolRouter(health_monitor=optimizer)

    stable = router.score_tool("stable", {"task": "run"}, {"confidence": 0.8})
    failing = router.score_tool("failing", {"task": "run"}, {"confidence": 0.8})

    assert stable.total > failing.total
