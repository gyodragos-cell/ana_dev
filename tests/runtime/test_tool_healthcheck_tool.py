"""Tests for the ANA tool healthcheck wrapper."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ANA_MAX_DIR = ROOT / "ANA_MAX"
if str(ANA_MAX_DIR) not in sys.path:
    sys.path.insert(0, str(ANA_MAX_DIR))

from tools.base import ToolResult, ToolStatus
from tools.tool_healthcheck import ToolHealthcheckTool, registry


def test_tool_healthcheck_safe_scope_summarizes_results(monkeypatch):
    executed: list[tuple[str, dict]] = []

    monkeypatch.setattr(registry, "list_tools", lambda: ["demo"])

    def fake_execute(name: str, **kwargs):
        executed.append((name, kwargs))
        return ToolResult(status=ToolStatus.SUCCESS, message=f"{name} ok")

    monkeypatch.setattr(registry, "execute", fake_execute)

    result = ToolHealthcheckTool().execute(scope="safe")

    assert result.status == ToolStatus.SUCCESS
    assert result.data["scope"] == "safe"
    assert result.data["ok"] == 7
    assert result.data["failed"] == 0
    assert "web_search" in result.data["dependencies"]
    assert [name for name, _ in executed] == [
        "file_operations",
        "system_control",
        "smart_search",
        "workspace_situational_awareness",
        "project_navigator",
        "error_radar",
        "tool_router",
    ]


def test_tool_healthcheck_counts_failed_checks(monkeypatch):
    monkeypatch.setattr(registry, "list_tools", lambda: ["demo"])

    def fake_execute(name: str, **kwargs):
        if name == "error_radar":
            return ToolResult(status=ToolStatus.ERROR, error="boom")
        return ToolResult(status=ToolStatus.SUCCESS, message=f"{name} ok")

    monkeypatch.setattr(registry, "execute", fake_execute)

    result = ToolHealthcheckTool().execute(scope="safe")

    assert result.status == ToolStatus.SUCCESS
    assert result.data["ok"] == 6
    assert result.data["failed"] == 1
    failed = [item for item in result.data["results"] if not item["success"]]
    assert failed == [
        {
            "tool": "error_radar",
            "success": False,
            "seconds": failed[0]["seconds"],
            "message": "",
            "error": "boom",
        }
    ]


def test_tool_healthcheck_reports_web_search_dependency(monkeypatch):
    monkeypatch.setattr(registry, "list_tools", lambda: ["demo"])
    monkeypatch.setattr(
        registry,
        "execute",
        lambda name, **kwargs: ToolResult(status=ToolStatus.SUCCESS, message=f"{name} ok"),
    )

    def fake_find_spec(name: str):
        if name in {"ddgs", "duckduckgo_search"}:
            return None
        return object()

    monkeypatch.setattr("tools.tool_healthcheck.importlib.util.find_spec", fake_find_spec)

    result = ToolHealthcheckTool().execute(scope="safe")

    web_dep = result.data["dependencies"]["web_search"]
    assert web_dep["ok"] is False
    assert web_dep["packages_any_of"] == ["ddgs", "duckduckgo-search"]
    assert web_dep["fix"] == "pip install ddgs"
    assert result.data["ok"] == 7
    assert result.data["failed"] == 0
