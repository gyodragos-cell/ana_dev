"""Tests for ANA post-reload verification bundle."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "ana_post_reload_verify.py"


def load_script():
    script_dir = str(SCRIPT.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location("ana_post_reload_verify", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_post_reload_verify_pass(monkeypatch):
    verify = load_script()
    monkeypatch.setattr(verify.ana_live_reload_check, "check_live_reload", lambda mcp_url, timeout=20: {
        "status": "PASS",
        "marker": "data.stale",
        "has_marker": True,
        "next_action": "Live MCP loaded updated behavior.",
    })
    monkeypatch.setattr(verify.ana_nucleus_smoke, "run_smoke", lambda mcp_url, timeout=30: {
        "status": "PASS",
        "summary": {"pass": 9, "warn": 0, "fail": 0, "total": 9},
    })
    monkeypatch.setattr(verify.ana_lab_state_summary, "build_summary", lambda mcp_url: {
        "mcp": {"mcp_ready": True, "tools_count": 90},
        "live_reload": {"status": "PASS", "has_marker": True},
        "identity_surface": {"status": "PASS", "files_checked": 10, "violations": 0, "missing_required": 0},
        "memory_hygiene": {"archive_candidates": 10},
        "git": {"changed_paths": 20, "tracked": 10, "untracked": 10},
    })
    monkeypatch.setattr(verify.ana_operator_status, "live_tool_surface", lambda mcp_url: {
        "status": "PASS",
        "live_count": 90,
        "manifest_count": 90,
        "extra_live": [],
        "missing_live": [],
    })
    monkeypatch.setattr(verify.ana_live_behavior_check, "build_report", lambda mcp_url, timeout=30: {
        "status": "PASS",
        "checks": {"session_audit_identity_surface_field": True},
    })

    report = verify.build_report()

    assert report["schema"] == "ana.post_reload_verify.v1"
    assert report["status"] == "PASS"
    assert report["live_reload"]["has_marker"] is True
    assert report["tool_surface"]["status"] == "PASS"
    assert report["identity_surface"]["status"] == "PASS"
    assert report["live_behavior"]["status"] == "PASS"
    assert report["next_action"].startswith("Continue")


def test_post_reload_verify_warns_when_marker_missing(monkeypatch):
    verify = load_script()
    monkeypatch.setattr(verify.ana_live_reload_check, "check_live_reload", lambda mcp_url, timeout=20: {
        "status": "WARN",
        "marker": "data.stale",
        "has_marker": False,
        "next_action": "Restart/reload ANA MCP server.",
    })
    monkeypatch.setattr(verify.ana_nucleus_smoke, "run_smoke", lambda mcp_url, timeout=30: {
        "status": "PASS",
        "summary": {"pass": 9, "warn": 0, "fail": 0, "total": 9},
    })
    monkeypatch.setattr(verify.ana_lab_state_summary, "build_summary", lambda mcp_url: {
        "mcp": {"mcp_ready": True, "tools_count": 91},
        "live_reload": {"status": "WARN", "has_marker": False},
        "identity_surface": {"status": "PASS", "files_checked": 10, "violations": 0, "missing_required": 0},
        "memory_hygiene": {"archive_candidates": 10},
        "git": {"changed_paths": 20, "tracked": 10, "untracked": 10},
    })
    monkeypatch.setattr(verify.ana_operator_status, "live_tool_surface", lambda mcp_url: {
        "status": "PASS",
        "live_count": 90,
        "manifest_count": 90,
        "extra_live": [],
        "missing_live": [],
    })
    monkeypatch.setattr(verify.ana_live_behavior_check, "build_report", lambda mcp_url, timeout=30: {
        "status": "PASS",
        "checks": {"session_audit_identity_surface_field": True},
    })

    report = verify.build_report()

    assert report["status"] == "WARN"
    assert report["next_action"].startswith("Reload/restart ANA MCP server")


def test_post_reload_verify_warns_when_tool_surface_has_drift(monkeypatch):
    verify = load_script()
    monkeypatch.setattr(verify.ana_live_reload_check, "check_live_reload", lambda mcp_url, timeout=20: {
        "status": "PASS",
        "marker": "data.stale",
        "has_marker": True,
        "next_action": "Live MCP loaded updated behavior.",
    })
    monkeypatch.setattr(verify.ana_nucleus_smoke, "run_smoke", lambda mcp_url, timeout=30: {
        "status": "PASS",
        "summary": {"pass": 9, "warn": 0, "fail": 0, "total": 9},
    })
    monkeypatch.setattr(verify.ana_lab_state_summary, "build_summary", lambda mcp_url: {
        "mcp": {"mcp_ready": True, "tools_count": 91},
        "live_reload": {"status": "PASS", "has_marker": True},
        "identity_surface": {"status": "PASS", "files_checked": 10, "violations": 0, "missing_required": 0},
        "memory_hygiene": {"archive_candidates": 10},
        "git": {"changed_paths": 20, "tracked": 10, "untracked": 10},
    })
    monkeypatch.setattr(verify.ana_operator_status, "live_tool_surface", lambda mcp_url: {
        "status": "WARN",
        "live_count": 91,
        "manifest_count": 90,
        "extra_live": ["adal_integration"],
        "missing_live": [],
    })
    monkeypatch.setattr(verify.ana_live_behavior_check, "build_report", lambda mcp_url, timeout=30: {
        "status": "PASS",
        "checks": {"session_audit_identity_surface_field": True},
    })

    report = verify.build_report()

    assert report["status"] == "WARN"
    assert report["tool_surface"]["extra_live"] == ["adal_integration"]
    assert report["next_action"].startswith("Restart ANA MCP")


def test_post_reload_verify_warns_when_identity_surface_has_drift(monkeypatch):
    verify = load_script()
    monkeypatch.setattr(verify.ana_live_reload_check, "check_live_reload", lambda mcp_url, timeout=20: {
        "status": "PASS",
        "marker": "data.stale",
        "has_marker": True,
        "next_action": "Live MCP loaded updated behavior.",
    })
    monkeypatch.setattr(verify.ana_nucleus_smoke, "run_smoke", lambda mcp_url, timeout=30: {
        "status": "PASS",
        "summary": {"pass": 9, "warn": 0, "fail": 0, "total": 9},
    })
    monkeypatch.setattr(verify.ana_lab_state_summary, "build_summary", lambda mcp_url: {
        "mcp": {"mcp_ready": True, "tools_count": 90},
        "live_reload": {"status": "PASS", "has_marker": True},
        "identity_surface": {"status": "FAIL", "files_checked": 10, "violations": 1, "missing_required": 0},
        "memory_hygiene": {"archive_candidates": 10},
        "git": {"changed_paths": 20, "tracked": 10, "untracked": 10},
    })
    monkeypatch.setattr(verify.ana_operator_status, "live_tool_surface", lambda mcp_url: {
        "status": "PASS",
        "live_count": 90,
        "manifest_count": 90,
        "extra_live": [],
        "missing_live": [],
    })
    monkeypatch.setattr(verify.ana_live_behavior_check, "build_report", lambda mcp_url, timeout=30: {
        "status": "PASS",
        "checks": {"session_audit_identity_surface_field": True},
    })

    report = verify.build_report()

    assert report["status"] == "WARN"
    assert report["identity_surface"]["violations"] == 1
    assert report["next_action"].startswith("Fix active identity surface")


def test_post_reload_verify_warns_when_live_behavior_is_stale(monkeypatch):
    verify = load_script()
    monkeypatch.setattr(verify.ana_live_reload_check, "check_live_reload", lambda mcp_url, timeout=20: {
        "status": "PASS",
        "marker": "data.stale",
        "has_marker": True,
    })
    monkeypatch.setattr(verify.ana_nucleus_smoke, "run_smoke", lambda mcp_url, timeout=30: {
        "status": "PASS",
        "summary": {"pass": 9, "warn": 0, "fail": 0, "total": 9},
    })
    monkeypatch.setattr(verify.ana_lab_state_summary, "build_summary", lambda mcp_url: {
        "mcp": {"mcp_ready": True, "tools_count": 90},
        "live_reload": {"status": "PASS", "has_marker": True},
        "identity_surface": {"status": "PASS", "files_checked": 10, "violations": 0, "missing_required": 0},
        "memory_hygiene": {},
        "git": {},
    })
    monkeypatch.setattr(verify.ana_operator_status, "live_tool_surface", lambda mcp_url: {
        "status": "PASS",
        "live_count": 90,
        "manifest_count": 90,
        "extra_live": [],
        "missing_live": [],
    })
    monkeypatch.setattr(verify.ana_live_behavior_check, "build_report", lambda mcp_url, timeout=30: {
        "status": "WARN",
        "checks": {"session_audit_identity_surface_field": False},
    })

    report = verify.build_report()

    assert report["status"] == "WARN"
    assert report["live_behavior"]["status"] == "WARN"
    assert report["next_action"].startswith("Restart ANA MCP, then run Live Behavior")


def test_post_reload_verify_fails_when_nucleus_fails(monkeypatch):
    verify = load_script()
    monkeypatch.setattr(verify.ana_live_reload_check, "check_live_reload", lambda mcp_url, timeout=20: {
        "status": "PASS",
        "marker": "data.stale",
        "has_marker": True,
    })
    monkeypatch.setattr(verify.ana_nucleus_smoke, "run_smoke", lambda mcp_url, timeout=30: {
        "status": "FAIL",
        "summary": {"pass": 2, "warn": 0, "fail": 1, "total": 3},
    })
    monkeypatch.setattr(verify.ana_lab_state_summary, "build_summary", lambda mcp_url: {
        "mcp": {"mcp_ready": True, "tools_count": 91},
        "live_reload": {"status": "PASS", "has_marker": True},
        "identity_surface": {"status": "PASS", "files_checked": 10, "violations": 0, "missing_required": 0},
        "memory_hygiene": {},
        "git": {},
    })
    monkeypatch.setattr(verify.ana_operator_status, "live_tool_surface", lambda mcp_url: {
        "status": "PASS",
        "live_count": 90,
        "manifest_count": 90,
        "extra_live": [],
        "missing_live": [],
    })
    monkeypatch.setattr(verify.ana_live_behavior_check, "build_report", lambda mcp_url, timeout=30: {
        "status": "PASS",
        "checks": {"session_audit_identity_surface_field": True},
    })

    report = verify.build_report()

    assert report["status"] == "FAIL"
    assert report["next_action"].startswith("Fix failed")
