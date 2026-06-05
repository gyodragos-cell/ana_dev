"""Tests for live MCP reload freshness checker."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "ana_live_reload_check.py"


def load_script():
    spec = importlib.util.spec_from_file_location("ana_live_reload_check", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_live_reload_check_passes_when_stale_marker_exists(monkeypatch):
    script = load_script()

    monkeypatch.setattr(
        script,
        "call_tool",
        lambda mcp_url, name, arguments, timeout=20: {
            "success": True,
            "message": "Graph map stats loaded.",
            "data": {"schema": "ana.graph_map.v1", "stale": False},
        },
    )

    report = script.check_live_reload("http://127.0.0.1:8766/mcp")

    assert report["status"] == "PASS"
    assert report["has_marker"] is True
    assert "loaded updated" in report["next_action"]


def test_live_reload_check_warns_when_marker_missing(monkeypatch):
    script = load_script()

    monkeypatch.setattr(
        script,
        "call_tool",
        lambda mcp_url, name, arguments, timeout=20: {
            "success": True,
            "message": "Graph map stats loaded.",
            "data": {"schema": "ana.graph_map.v1", "stats": {"nodes": 10}},
        },
    )

    report = script.check_live_reload("http://127.0.0.1:8766/mcp")

    assert report["status"] == "WARN"
    assert report["has_marker"] is False
    assert "Restart/reload" in report["next_action"]
