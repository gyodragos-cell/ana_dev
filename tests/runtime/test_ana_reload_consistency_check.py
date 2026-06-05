"""Tests for ANA reload diagnostic consistency checks."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "ana_reload_consistency_check.py"


def load_script():
    script_dir = str(SCRIPT.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location("ana_reload_consistency_check", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_reload_consistency_passes_when_all_pass(monkeypatch):
    script = load_script()
    monkeypatch.setattr(script.ana_reload_readiness, "build_report", lambda mcp_url: {
        "mcp": {"mcp_ready": True},
        "reload_needed": False,
        "reload_reasons": [],
        "tool_surface": {"status": "PASS", "live_count": 90, "manifest_count": 90, "extra_live": [], "missing_live": []},
        "live_behavior": {"status": "PASS", "checks": {"one": True}},
    })
    monkeypatch.setattr(script.ana_operator_status, "build_status", lambda mcp_url: {
        "reload_readiness": {"status": "PASS", "reasons": []},
    })
    monkeypatch.setattr(script.ana_lab_state_summary, "build_summary", lambda mcp_url: {
        "reload_readiness": {"status": "PASS", "reasons": []},
    })
    monkeypatch.setattr(script.ana_post_reload_verify, "build_report", lambda mcp_url, timeout=30: {
        "status": "PASS",
        "next_action": "Continue.",
    })

    report = script.build_report()

    assert report["status"] == "PASS"
    assert report["aligned"] is True
    assert set(report["verdicts"].values()) == {"PASS"}
    assert report["next_action"].startswith("Reload diagnostics agree")


def test_reload_consistency_passes_aligned_warn(monkeypatch):
    script = load_script()
    monkeypatch.setattr(script.ana_reload_readiness, "build_report", lambda mcp_url: {
        "mcp": {"mcp_ready": True},
        "reload_needed": True,
        "reload_reasons": ["live_tool_surface_drift"],
        "safe_to_restart_guidance": "Restart ANA MCP.",
        "tool_surface": {"status": "WARN", "live_count": 91, "manifest_count": 90, "extra_live": ["adal_integration"], "missing_live": []},
        "live_behavior": {"status": "PASS", "checks": {"one": True}},
    })
    monkeypatch.setattr(script.ana_operator_status, "build_status", lambda mcp_url: {
        "reload_readiness": {"status": "WARN", "reasons": ["live_tool_surface_drift"]},
    })
    monkeypatch.setattr(script.ana_lab_state_summary, "build_summary", lambda mcp_url: {
        "reload_readiness": {"status": "WARN", "reasons": ["live_tool_surface_drift"]},
    })
    monkeypatch.setattr(script.ana_post_reload_verify, "build_report", lambda mcp_url, timeout=30: {
        "status": "WARN",
        "next_action": "Restart ANA MCP.",
    })

    report = script.build_report()

    assert report["status"] == "PASS"
    assert report["aligned"] is True
    assert set(report["verdicts"].values()) == {"WARN"}
    assert report["signals"]["reload_reasons"] == ["live_tool_surface_drift"]
    assert report["next_action"] == "Restart ANA MCP."


def test_reload_consistency_warns_when_diagnostics_disagree(monkeypatch):
    script = load_script()
    monkeypatch.setattr(script.ana_reload_readiness, "build_report", lambda mcp_url: {
        "mcp": {"mcp_ready": True},
        "reload_needed": True,
        "reload_reasons": ["live_behavior_stale"],
        "tool_surface": {"status": "PASS", "live_count": 90, "manifest_count": 90, "extra_live": [], "missing_live": []},
        "live_behavior": {"status": "WARN", "checks": {"one": False}},
    })
    monkeypatch.setattr(script.ana_operator_status, "build_status", lambda mcp_url: {
        "reload_readiness": {"status": "PASS", "reasons": []},
    })
    monkeypatch.setattr(script.ana_lab_state_summary, "build_summary", lambda mcp_url: {
        "reload_readiness": {"status": "WARN", "reasons": ["live_behavior_stale"]},
    })
    monkeypatch.setattr(script.ana_post_reload_verify, "build_report", lambda mcp_url, timeout=30: {
        "status": "WARN",
        "next_action": "Restart ANA MCP.",
    })

    report = script.build_report()

    assert report["status"] == "WARN"
    assert report["aligned"] is False
    assert report["next_action"].startswith("Reload diagnostics disagree")


def test_reload_consistency_fails_when_mcp_not_ready(monkeypatch):
    script = load_script()
    monkeypatch.setattr(script.ana_reload_readiness, "build_report", lambda mcp_url: {
        "mcp": {"mcp_ready": False},
        "reload_needed": True,
        "tool_surface": {},
        "live_behavior": {},
    })
    monkeypatch.setattr(script.ana_operator_status, "build_status", lambda mcp_url: {
        "reload_readiness": {"status": "FAIL", "reasons": []},
    })
    monkeypatch.setattr(script.ana_lab_state_summary, "build_summary", lambda mcp_url: {
        "reload_readiness": {"status": "FAIL", "reasons": []},
    })
    monkeypatch.setattr(script.ana_post_reload_verify, "build_report", lambda mcp_url, timeout=30: {
        "status": "FAIL",
        "next_action": "Fix MCP.",
    })

    report = script.build_report()

    assert report["status"] == "FAIL"
    assert report["aligned"] is True
    assert set(report["verdicts"].values()) == {"FAIL"}
