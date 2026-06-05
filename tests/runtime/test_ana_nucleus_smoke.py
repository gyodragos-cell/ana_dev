"""Tests for ANA nucleus smoke check."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "ana_nucleus_smoke.py"


def load_script():
    script_dir = str(SCRIPT.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location("ana_nucleus_smoke", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_run_smoke_passes_with_required_nucleus_tools(monkeypatch):
    script = load_script()

    def fake_json_request(url, payload=None, timeout=30):
        assert payload is None
        return {"status": "online", "mcp_ready": True, "tools_count": 90}

    def fake_rpc(mcp_url, method, params=None, timeout=30):
        assert method == "tools/list"
        tools = [
            "tool_router",
            "agent_coach",
            "code_context_pack",
            "graph_context_pack",
            "tool_healthcheck",
            "error_radar",
            "session_audit",
        ]
        return {"result": {"tools": [{"name": name} for name in tools]}}

    def fake_call_tool(mcp_url, name, arguments=None, timeout=30):
        payloads = {
            "tool_router": {
                "success": True,
                "message": "route ok",
                "data": {"recommended_tools": ["code_context_pack"], "mode": "recommend"},
            },
            "agent_coach": {
                "success": True,
                "message": "coach ok",
                "data": {"primary_tool": "code_context_pack", "severity": "info"},
            },
            "code_context_pack": {
                "success": True,
                "message": "context ok",
                "data": {
                    "code_map": {"results": [{"path": "x.py"}]},
                    "graph_map": {"results": [{"id": "x.py"}]},
                    "compressed_state": {"evidence": ["code_map", "graph_map"]},
                },
            },
            "graph_context_pack": {
                "success": True,
                "message": "graph ok",
                "data": {"stats": {"nodes": 3, "edges": 2}, "updated_at": "2026-06-01T00:00:00Z"},
            },
            "tool_healthcheck": {
                "success": True,
                "message": "health ok",
                "data": {"ok": True, "failed": 0},
            },
            "error_radar": {
                "success": True,
                "message": "radar ok",
                "data": {"count": 0, "findings": []},
            },
            "session_audit": {
                "success": True,
                "message": "Gata cu 92% incredere.",
                "data": {"trust": {"score": 92, "signals": {"context_found": 1}}},
            },
        }
        return payloads[name]

    monkeypatch.setattr(script, "json_request", fake_json_request)
    monkeypatch.setattr(script, "rpc", fake_rpc)
    monkeypatch.setattr(script, "call_tool", fake_call_tool)
    monkeypatch.setattr(script.ana_operator_status, "context_maps_status", lambda: {
        "status": "PASS",
        "code_map": {"status": "PASS", "summaries": 10},
        "graph_map": {"status": "PASS", "nodes": 20, "edges": 30},
    })

    report = script.run_smoke("http://127.0.0.1:8766/mcp")

    assert report["schema"] == "ana.nucleus_smoke.v1"
    assert report["status"] == "PASS"
    assert report["summary"] == {"pass": 10, "warn": 0, "fail": 0, "total": 10}
    assert [step["name"] for step in report["steps"]] == [
        "health",
        "tools_list",
        "tool_router",
        "agent_coach",
        "code_context_pack",
        "graph_context_pack",
        "tool_healthcheck",
        "error_radar",
        "session_audit",
        "context_maps",
    ]
    assert report["steps"][-1]["data"]["message"].startswith("code:PASS")


def test_run_smoke_warns_when_context_maps_are_stale(monkeypatch):
    script = load_script()

    monkeypatch.setattr(script, "json_request", lambda url, payload=None, timeout=30: {
        "status": "online",
        "mcp_ready": True,
        "tools_count": 90,
    })
    monkeypatch.setattr(script, "rpc", lambda mcp_url, method, params=None, timeout=30: {
        "result": {
            "tools": [
                {"name": "tool_router"},
                {"name": "agent_coach"},
                {"name": "code_context_pack"},
                {"name": "graph_context_pack"},
                {"name": "tool_healthcheck"},
                {"name": "error_radar"},
                {"name": "session_audit"},
            ]
        },
    })
    monkeypatch.setattr(script, "call_tool", lambda mcp_url, name, arguments=None, timeout=30: {
        "success": True,
        "message": f"{name} ok",
        "data": {
            "recommended_tools": ["code_context_pack"],
            "primary_tool": "code_context_pack",
            "code_map": {"results": [1]},
            "graph_map": {"results": [1], "stats": {"nodes": 3, "edges": 2}},
            "compressed_state": {"evidence": ["code_map"]},
            "stats": {"nodes": 3, "edges": 2},
            "failed": 0,
            "trust": {"score": 92},
        },
    })
    monkeypatch.setattr(script.ana_operator_status, "context_maps_status", lambda: {
        "status": "WARN",
        "code_map": {"status": "STALE", "summaries": 10, "stale_source": "ANA_MAX/tools/example.py"},
        "graph_map": {"status": "PASS", "nodes": 20, "edges": 30},
    })

    report = script.run_smoke("http://127.0.0.1:8766/mcp")

    assert report["status"] == "WARN"
    assert report["summary"] == {"pass": 9, "warn": 1, "fail": 0, "total": 10}
    context_step = next(step for step in report["steps"] if step["name"] == "context_maps")
    assert context_step["status"] == "WARN"
    assert context_step["optional"] is True
    assert context_step["data"]["code_status"] == "STALE"


def test_run_smoke_fails_when_required_tool_missing(monkeypatch):
    script = load_script()

    monkeypatch.setattr(script, "json_request", lambda url, payload=None, timeout=30: {
        "status": "online",
        "mcp_ready": True,
        "tools_count": 6,
    })
    monkeypatch.setattr(script, "rpc", lambda mcp_url, method, params=None, timeout=30: {
        "result": {"tools": [{"name": "tool_router"}]},
    })
    monkeypatch.setattr(script, "call_tool", lambda *args, **kwargs: {"success": False})
    monkeypatch.setattr(script.ana_operator_status, "context_maps_status", lambda: {
        "status": "PASS",
        "code_map": {"status": "PASS", "summaries": 10},
        "graph_map": {"status": "PASS", "nodes": 20, "edges": 30},
    })

    report = script.run_smoke("http://127.0.0.1:8766/mcp")

    assert report["status"] == "FAIL"
    assert report["steps"][1]["name"] == "tools_list"
    assert report["steps"][1]["data"]["missing_required"] == [
        "agent_coach",
        "code_context_pack",
        "graph_context_pack",
        "tool_healthcheck",
        "error_radar",
        "session_audit",
    ]
