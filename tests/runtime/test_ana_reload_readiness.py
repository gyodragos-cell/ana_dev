"""Tests for ANA reload readiness preflight."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "ana_reload_readiness.py"


def load_script():
    script_dir = str(SCRIPT.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location("ana_reload_readiness", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_reload_readiness_recommends_reload_when_marker_missing(monkeypatch):
    readiness = load_script()
    monkeypatch.setattr(readiness, "get_json", lambda url, timeout=10: {
        "status": "online",
        "mcp_ready": True,
        "tools_count": 91,
        "version": "18.0-MAX",
    })
    monkeypatch.setattr(readiness.ana_live_reload_check, "check_live_reload", lambda mcp_url, timeout=20: {
        "status": "WARN",
        "marker": "data.stale",
        "has_marker": False,
    })
    monkeypatch.setattr(readiness.ana_operator_status, "live_tool_surface", lambda mcp_url: {
        "status": "PASS",
        "live_count": 91,
        "manifest_count": 91,
        "extra_live": [],
        "missing_live": [],
    })
    monkeypatch.setattr(readiness.ana_live_behavior_check, "build_report", lambda mcp_url, timeout=20: {
        "status": "PASS",
        "checks": {"session_audit_identity_surface_field": True},
    })
    monkeypatch.setattr(readiness, "port_owner", lambda port=8766: {"ok": True, "stdout": "port"})
    monkeypatch.setattr(readiness, "python_processes", lambda: {"ok": True, "stdout": "python ANA_MAX/main.py"})

    report = readiness.build_report()

    assert report["schema"] == "ana.reload_readiness.v1"
    assert report["reload_needed"] is True
    assert report["reload_reasons"] == ["missing_reload_marker"]
    assert report["mcp"]["tools_count"] == 91
    assert "does not stop" in report["safety"]
    assert "Reload/restart is useful" in report["safe_to_restart_guidance"]


def test_reload_readiness_does_not_recommend_when_marker_present(monkeypatch):
    readiness = load_script()
    monkeypatch.setattr(readiness, "get_json", lambda url, timeout=10: {
        "status": "online",
        "mcp_ready": True,
        "tools_count": 91,
    })
    monkeypatch.setattr(readiness.ana_live_reload_check, "check_live_reload", lambda mcp_url, timeout=20: {
        "status": "PASS",
        "marker": "data.stale",
        "has_marker": True,
    })
    monkeypatch.setattr(readiness.ana_operator_status, "live_tool_surface", lambda mcp_url: {
        "status": "PASS",
        "live_count": 90,
        "manifest_count": 90,
        "extra_live": [],
        "missing_live": [],
    })
    monkeypatch.setattr(readiness.ana_live_behavior_check, "build_report", lambda mcp_url, timeout=20: {
        "status": "PASS",
        "checks": {"session_audit_identity_surface_field": True},
    })
    monkeypatch.setattr(readiness, "port_owner", lambda port=8766: {"ok": True})
    monkeypatch.setattr(readiness, "python_processes", lambda: {"ok": True})

    report = readiness.build_report()

    assert report["reload_needed"] is False
    assert report["reload_reasons"] == []
    assert report["safe_to_restart_guidance"] == "Reload not required by current marker, tool-surface, or behavior checks."


def test_reload_readiness_recommends_reload_when_surface_or_behavior_stale(monkeypatch):
    readiness = load_script()
    monkeypatch.setattr(readiness, "get_json", lambda url, timeout=10: {
        "status": "online",
        "mcp_ready": True,
        "tools_count": 91,
    })
    monkeypatch.setattr(readiness.ana_live_reload_check, "check_live_reload", lambda mcp_url, timeout=20: {
        "status": "PASS",
        "marker": "data.stale",
        "has_marker": True,
    })
    monkeypatch.setattr(readiness.ana_operator_status, "live_tool_surface", lambda mcp_url: {
        "status": "WARN",
        "live_count": 91,
        "manifest_count": 90,
        "extra_live": ["adal_integration"],
        "missing_live": [],
    })
    monkeypatch.setattr(readiness.ana_live_behavior_check, "build_report", lambda mcp_url, timeout=20: {
        "status": "WARN",
        "checks": {"session_audit_identity_surface_field": False},
    })
    monkeypatch.setattr(readiness, "port_owner", lambda port=8766: {"ok": True})
    monkeypatch.setattr(readiness, "python_processes", lambda: {"ok": True})

    report = readiness.build_report()

    assert report["reload_needed"] is True
    assert report["reload_reasons"] == ["live_tool_surface_drift", "live_behavior_stale"]
    assert report["tool_surface"]["extra_live"] == ["adal_integration"]


def test_reload_readiness_recommends_direct_mcp_restart_for_behavior_only(monkeypatch):
    readiness = load_script()
    monkeypatch.setattr(readiness, "get_json", lambda url, timeout=10: {
        "status": "online",
        "mcp_ready": True,
        "tools_count": 90,
    })
    monkeypatch.setattr(readiness.ana_live_reload_check, "check_live_reload", lambda mcp_url, timeout=20: {
        "status": "PASS",
        "marker": "data.stale",
        "has_marker": True,
    })
    monkeypatch.setattr(readiness.ana_operator_status, "live_tool_surface", lambda mcp_url: {
        "status": "PASS",
        "live_count": 90,
        "manifest_count": 90,
        "extra_live": [],
        "missing_live": [],
    })
    monkeypatch.setattr(readiness.ana_live_behavior_check, "build_report", lambda mcp_url, timeout=20: {
        "status": "WARN",
        "checks": {"error_radar_runtime_breakdown": False},
    })
    monkeypatch.setattr(readiness, "port_owner", lambda port=8766: {"ok": True})
    monkeypatch.setattr(readiness, "python_processes", lambda: {"ok": True})

    report = readiness.build_report()

    assert report["reload_reasons"] == ["live_behavior_stale"]
    assert report["safe_to_restart_guidance"].startswith("Restart ANA MCP")
