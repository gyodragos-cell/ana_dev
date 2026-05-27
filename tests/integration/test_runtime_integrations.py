"""Integration-style tests for ANA MAX v24 dev runtime paths."""

from core.agent_manager import AgentManager
from core.auto_repair import AutoRepairEngine
from core.execution_layer import ExecutionLayer
from core.mcp_client import MCPClient, MCPServerConfig, ToolEndpoint
from core.memory_manager import MemoryManager
from core.orchestrator import Orchestrator
from core.self_optimization import SelfOptimizationEngine
from core.tool_router import ToolRouter


def test_mcp_integration_success_path():
    """Execution layer should reach fake MCP through the MCP client."""
    client = MCPClient(
        {"lab": MCPServerConfig("lab", endpoint="mock://lab", enabled=True)},
        transport=lambda endpoint, payload, timeout: {"result": {"success": True, "data": {"tool": payload["params"]["name"]}}},
    )
    layer = ExecutionLayer(
        mcp_client=client,
        tool_catalog={"mcp_echo": ToolEndpoint("mcp_echo", tool_type="mcp", server_id="lab")},
    )

    assert layer.execute("mcp_echo", {}).to_dict()["data"]["tool"] == "mcp_echo"


def test_chained_failures_disable_tool():
    """Auto-repair should disable tools after repeated failures."""
    repair = AutoRepairEngine(max_chain_failures=1)
    repair.plan_repair({"tool": "broken_tool", "failure_count": 1})

    assert repair.is_disabled("broken_tool")


def test_misrouting_and_fallback_chain_memory():
    """Router should record scenario corrections in memory."""
    router = ToolRouter()
    router.record_routing_result("bad_tool", False, scenario="misrouting")
    router.record_routing_result("grep_file", True, scenario="misrouting")

    score = router.score_tool("grep_file", {"task": "search", "scenario": "misrouting"}, {"confidence": 0.7})

    assert score.scenario_fit > 0


def test_noisy_tool_detection_affects_router():
    """Optimization feedback should steer router away from noisy tools."""
    optimizer = SelfOptimizationEngine()
    optimizer.compute_snapshot(
        {
            "noisy": {"success_rate": 0.8, "failure_rate": 0.2, "avg_latency_ms": 100, "noisy_tool_score": 1.0},
            "quiet": {"success_rate": 1.0, "failure_rate": 0.0, "avg_latency_ms": 10, "noisy_tool_score": 0.0},
        }
    )
    router = ToolRouter(health_monitor=optimizer)

    assert router.select_tool(["noisy", "quiet"], {"task": "inspect"}, {"confidence": 0.8}).selected_tool == "quiet"


def test_memory_influences_context_for_routing():
    """Memory manager should return semantic hits for router context."""
    memory = MemoryManager()
    memory.save_semantic("grep_file", "best for file search")

    context = memory.inject_context("use grep_file for file search")

    assert context["semantic_hits"]


def test_orchestrator_parallel_execution():
    """Orchestrator should run queued tasks in parallel."""
    orchestrator = Orchestrator({"echo": lambda payload: payload["value"]}, max_workers=2)
    orchestrator.add_task("echo", {"value": 1})
    orchestrator.add_task("echo", {"value": 2})

    results = orchestrator.run_parallel()

    assert sorted(item["result"] for item in results) == [1, 2]
