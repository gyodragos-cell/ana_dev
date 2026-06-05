from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


ANA_MAX_DIR = Path(__file__).resolve().parents[2] / "ANA_MAX"
if str(ANA_MAX_DIR) not in sys.path:
    sys.path.insert(0, str(ANA_MAX_DIR))

from tools.base import Tool, ToolDefinition, ToolResult, ToolStatus, registry  # noqa: E402
from tools.agent_coach_tool import AgentCoachTool  # noqa: E402
from tools.tool_router_tool import ToolRouterTool  # noqa: E402


@pytest.fixture(autouse=True)
def restore_registry_state():
    tools = dict(registry._tools)
    categories = {key: list(value) for key, value in registry._categories.items()}
    yield
    registry._tools = tools
    registry._categories = categories


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
        "code_context_pack",
        "foreground_ui_snapshot",
        "windows_uia_bridge",
    ]


def test_tool_router_classifies_runtime_deep_tasks() -> None:
    result = ToolRouterTool().execute(task="Need Frida hook for runtime process behavior", max_tools=2)

    assert result.is_success
    assert result.data["mode"] == "runtime_deep"
    assert result.data["recommended_tools"] == ["tool_healthcheck", "event_stream"]


def test_tool_router_includes_graph_context_for_code_changes() -> None:
    result = ToolRouterTool().execute(task="implement a code fix and run tests", max_tools=4)

    assert result.is_success
    assert result.data["mode"] == "code_change"
    assert result.data["recommended_tools"][0] == "code_context_pack"
    assert "graph_context_pack" in result.data["recommended_tools"]
    assert result.data["tool_profiles"]["code_context_pack"] == ["core"]


def test_tool_router_filters_inactive_profile_tools(monkeypatch, tmp_path: Path) -> None:
    manifest = tmp_path / "permission_manifest.json"
    manifest.write_text(
        json.dumps({
            "global_settings": {"active_profiles": ["core"]},
            "tools": {
                "foreground_ui_snapshot": {"profile": "windows", "allowed": True},
                "windows_uia_bridge": {"profile": "windows", "allowed": True},
                "code_context_pack": {"profile": "core", "allowed": True},
                "desktop_capture": {"profile": "windows", "allowed": True},
                "ocr_tool": {"profile": "windows", "allowed": True},
                "window_manager": {"profile": "windows", "allowed": True},
                "uia_click": {"profile": "windows", "allowed": True},
                "uia_type": {"profile": "windows", "allowed": True},
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr("tools.tool_router_tool.PERMISSION_MANIFEST", manifest)

    result = ToolRouterTool().execute(task="inspect UI button on desktop", max_tools=4)

    assert result.is_success
    assert result.data["recommended_tools"] == ["code_context_pack"]
    assert result.data["filtered_by_profile"][0]["tool"] == "foreground_ui_snapshot"
    assert result.data["filtered_by_profile"][0]["reason"] == "inactive_profile"


def test_tool_router_profile_status_reports_manifest_profiles(monkeypatch, tmp_path: Path) -> None:
    manifest = tmp_path / "permission_manifest.json"
    manifest.write_text(
        json.dumps({
            "global_settings": {"active_profiles": ["core"]},
            "tools": {
                "code_context_pack": {"profile": "core", "allowed": True},
                "desktop_control": {"profile": "windows", "allowed": True},
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr("tools.tool_router_tool.PERMISSION_MANIFEST", manifest)

    result = ToolRouterTool().execute(mode="profile_status")

    assert result.is_success
    assert result.data["schema"] == "ana.tool_router.profile_status.v1"
    assert result.data["active_profiles"] == ["core"]
    assert result.data["tools_total"] == 2
    assert result.data["profile_counts"] == {"core": 1, "windows": 1}
    assert result.data["inactive_tools"] == [{"tool": "desktop_control", "profiles": ["windows"]}]
    assert result.data["unprofiled_count"] == 0


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
