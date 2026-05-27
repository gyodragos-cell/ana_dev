from __future__ import annotations

import sys
from pathlib import Path


ANA_MAX_DIR = Path(__file__).resolve().parents[2] / "ANA_MAX"
if str(ANA_MAX_DIR) not in sys.path:
    sys.path.insert(0, str(ANA_MAX_DIR))

from tools.base import Tool, ToolDefinition, ToolResult, ToolStatus, registry  # noqa: E402
from tools.agent_coach_tool import AgentCoachTool  # noqa: E402
from tools.tool_router_tool import ToolRouterTool  # noqa: E402


def test_tool_router_classifies_failures_first() -> None:
    result = ToolRouterTool().execute(
        task="PowerShell command failed twice",
        error="UnicodeEncodeError: character maps to undefined",
        max_tools=4,
    )

    assert result.is_success
    assert result.data["mode"] == "failure"
    assert result.data["recommended_tools"] == [
        "error_radar",
        "agent_coach",
        "ana_memory",
        "debugger",
    ]


def test_tool_router_classifies_ui_tasks() -> None:
    result = ToolRouterTool().execute(task="inspect UI button on desktop", max_tools=3)

    assert result.is_success
    assert result.data["mode"] == "ui_desktop"
    assert result.data["recommended_tools"] == [
        "foreground_ui_snapshot",
        "windows_uia_bridge",
        "desktop_capture",
    ]


def test_tool_router_classifies_runtime_deep_tasks() -> None:
    result = ToolRouterTool().execute(task="Need Frida hook for runtime process behavior", max_tools=2)

    assert result.is_success
    assert result.data["mode"] == "runtime_deep"
    assert result.data["recommended_tools"] == ["tool_healthcheck", "event_stream"]


class _FailingTool(Tool):
    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(name="router_failure_demo", description="demo")

    def execute(self, **kwargs) -> ToolResult:
        return ToolResult(status=ToolStatus.ERROR, error="demo failure")


def test_failed_tool_result_gets_tool_router_auto_guidance() -> None:
    registry.reset()
    registry.register(ToolRouterTool())
    registry.register(_FailingTool())

    result = registry.execute("router_failure_demo")

    assert result.status == ToolStatus.ERROR
    assert result.data["auto_guidance"]["tool_router"]["mode"] == "failure"
    assert "error_radar" in result.data["auto_guidance"]["tool_router"]["recommended_tools"]


def test_failed_tool_result_gets_agent_coach_recommend_auto_guidance() -> None:
    registry.reset()
    registry.register(AgentCoachTool())
    registry.register(ToolRouterTool())
    registry.register(_FailingTool())

    result = registry.execute("router_failure_demo")

    guidance = result.data["auto_guidance"]["agent_coach_recommend"]
    assert guidance["primary_tool"] == "error_radar"
    assert "agent_coach" in guidance["tool_stack"]
    assert "next_action" in guidance
    assert result.data["guidance_summary"]["source"] == "agent_coach_recommend"
    assert result.data["guidance_summary"]["primary_tool"] == "error_radar"
