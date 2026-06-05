"""Tests for compact ANA lab state summary."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "ana_lab_state_summary.py"


def load_script():
    script_dir = str(SCRIPT.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location("ana_lab_state_summary", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_build_summary_compacts_core_lab_signals(monkeypatch):
    summary = load_script()

    monkeypatch.setattr(summary, "get_json", lambda url, timeout=10: {
        "status": "online",
        "mcp_ready": True,
        "tools_count": 91,
        "version": "18.0-MAX",
    })
    monkeypatch.setattr(summary, "package_artifacts", lambda: {
        "version": "1.0.65",
        "copy_vsix_exists": True,
        "main_vsix_exists": True,
    })
    monkeypatch.setattr(summary.ana_live_reload_check, "check_live_reload", lambda mcp_url, timeout=20: {
        "status": "WARN",
        "marker": "data.stale",
        "has_marker": False,
        "next_action": "Restart/reload ANA MCP server, then rerun this check.",
    })
    monkeypatch.setattr(summary.ana_memory_hygiene, "build_report", lambda keep_latest=20, include_plan=True: {
        "checkpoints": {"count": 10},
        "rem_sleep_reports": {"count": 2},
        "archive_candidates": 4,
        "archive_plan": {
            "total_moves": 4,
            "archive_root": "dev_artifacts/archives/memory_hygiene_20260531",
            "archive_date_basis": "utc",
        },
    })
    monkeypatch.setattr(summary, "latest_memory_archive_readiness", lambda: {
        "available": True,
        "status": "PASS",
        "source_report": "ANA_MAX/dev_artifacts/reports/memory_archive_test.json",
        "total_moves": 4,
        "archive_root": "dev_artifacts/archives/memory_hygiene_20260531",
        "archive_date_basis": "utc",
        "summary": {"by_kind": {"checkpoints": 3, "rem_sleep_reports": 1}},
        "failures": 0,
        "warnings": 0,
    })
    monkeypatch.setattr(summary, "latest_trace_summary", lambda: {
        "available": True,
        "ok": True,
        "steps": 12,
        "spans": 12,
        "aligned": True,
        "operations": {"verification": 5},
    })
    monkeypatch.setattr(summary, "git_dirty_summary", lambda: {
        "ok": True,
        "changed_paths": 12,
        "tracked": 3,
        "untracked": 9,
        "sample": [],
    })
    monkeypatch.setattr(summary.ana_file_activity_snapshot, "build_report", lambda root, sample_limit=8: ({
        "baseline_available": True,
        "files_scanned": 20,
        "diff": {"created": 1, "deleted": 2, "modified": 3, "samples": {}},
        "privacy": {"content_read": False, "raw_private_payloads": False},
    }, {"manifest": {}}))
    monkeypatch.setattr(summary.ana_operator_status, "live_tool_surface", lambda mcp_url: {
        "status": "WARN",
        "live_count": 91,
        "manifest_count": 90,
        "extra_live": ["adal_integration"],
        "missing_live": [],
    })
    monkeypatch.setattr(summary.ana_operator_status, "context_maps_status", lambda: {
        "status": "PASS",
        "code_map": {"status": "PASS", "summaries": 10},
        "graph_map": {"status": "PASS", "nodes": 20, "edges": 30},
    })
    monkeypatch.setattr(summary.ana_identity_surface_check, "build_report", lambda: {
        "status": "PASS",
        "files_checked": 10,
        "violations": [],
        "missing_required": [],
    })
    seen_live_behavior_timeout = {}
    def fake_live_behavior(mcp_url, timeout=20):
        seen_live_behavior_timeout["timeout"] = timeout
        return {
        "status": "WARN",
        "checks": {
            "session_audit_identity_surface_field": False,
            "session_audit_identity_signal": False,
        },
        }
    monkeypatch.setattr(summary.ana_live_behavior_check, "build_report", fake_live_behavior)

    report = summary.build_summary()

    assert report["schema"] == "ana.lab_state_summary.v1"
    assert report["package"]["version"] == "1.0.65"
    assert report["package"]["copy_vsix_exists"] is True
    assert report["package"]["main_vsix_exists"] is True
    assert report["mcp"]["tools_count"] == 91
    assert report["live_reload"]["status"] == "WARN"
    assert report["reload_readiness"]["status"] == "WARN"
    assert report["reload_readiness"]["reload_needed"] is True
    assert report["reload_readiness"]["reasons"] == [
        "missing_reload_marker",
        "live_tool_surface_drift",
        "live_behavior_stale",
    ]
    assert report["memory_hygiene"]["archive_candidates"] == 4
    assert report["memory_hygiene"]["archive_date_basis"] == "utc"
    assert report["memory_hygiene"]["archive_readiness"]["status"] == "PASS"
    assert report["memory_hygiene"]["archive_readiness"]["total_moves"] == 4
    assert report["memory_hygiene"]["archive_readiness"]["archive_date_basis"] == "utc"
    assert report["trace"]["aligned"] is True
    assert report["tool_surface"]["status"] == "WARN"
    assert report["tool_surface"]["extra_live"] == ["adal_integration"]
    assert report["live_behavior"]["status"] == "WARN"
    assert report["context_maps"]["status"] == "PASS"
    assert seen_live_behavior_timeout["timeout"] == 60
    assert report["identity_surface"]["status"] == "PASS"
    assert report["identity_surface"]["violations"] == 0
    assert report["file_activity"]["diff"]["deleted"] == 2
    assert report["file_activity"]["privacy"]["content_read"] is False
    assert report["git"]["changed_paths"] == 12
    assert "Reload/restart" in report["recommended_next_step"]


def test_build_summary_recommends_mcp_restart_for_live_behavior_only(monkeypatch):
    summary = load_script()

    monkeypatch.setattr(summary, "get_json", lambda url, timeout=10: {
        "status": "online",
        "mcp_ready": True,
        "tools_count": 90,
        "version": "18.0-MAX",
    })
    monkeypatch.setattr(summary.ana_live_reload_check, "check_live_reload", lambda mcp_url, timeout=20: {
        "status": "PASS",
        "marker": "ok",
        "has_marker": True,
        "next_action": "Live MCP loaded updated behavior.",
    })
    monkeypatch.setattr(summary.ana_memory_hygiene, "build_report", lambda keep_latest=20, include_plan=True: {
        "checkpoints": {"count": 10},
        "rem_sleep_reports": {"count": 2},
        "archive_candidates": 4,
        "archive_plan": {
            "total_moves": 4,
            "archive_root": "dev_artifacts/archives/memory_hygiene_20260531",
            "archive_date_basis": "utc",
        },
    })
    monkeypatch.setattr(summary, "latest_memory_archive_readiness", lambda: {
        "available": True,
        "status": "PASS",
        "total_moves": 4,
        "archive_root": "dev_artifacts/archives/memory_hygiene_20260531",
        "archive_date_basis": "utc",
    })
    monkeypatch.setattr(summary, "latest_trace_summary", lambda: {"available": True, "aligned": True})
    monkeypatch.setattr(summary, "git_dirty_summary", lambda: {"ok": True, "changed_paths": 0})
    monkeypatch.setattr(summary.ana_file_activity_snapshot, "build_report", lambda root, sample_limit=8: ({
        "baseline_available": True,
        "files_scanned": 20,
        "diff": {"created": 0, "deleted": 0, "modified": 0, "samples": {}},
        "privacy": {"content_read": False, "raw_private_payloads": False},
    }, {"manifest": {}}))
    monkeypatch.setattr(summary.ana_operator_status, "live_tool_surface", lambda mcp_url: {
        "status": "PASS",
        "live_count": 90,
        "manifest_count": 90,
        "extra_live": [],
        "missing_live": [],
    })
    monkeypatch.setattr(summary.ana_operator_status, "context_maps_status", lambda: {
        "status": "PASS",
        "code_map": {"status": "PASS", "summaries": 10},
        "graph_map": {"status": "PASS", "nodes": 20, "edges": 30},
    })
    monkeypatch.setattr(summary.ana_identity_surface_check, "build_report", lambda: {
        "status": "PASS",
        "files_checked": 10,
        "violations": [],
        "missing_required": [],
    })
    monkeypatch.setattr(summary.ana_live_behavior_check, "build_report", lambda mcp_url, timeout=60: {
        "status": "WARN",
        "checks": {"error_radar_runtime_breakdown": False},
    })

    report = summary.build_summary()

    assert report["reload_readiness"]["reasons"] == ["live_behavior_stale"]
    assert report["recommended_next_step"].startswith("Restart ANA MCP, then run Live Behavior")


def test_build_summary_recommends_map_refresh_when_context_maps_are_stale(monkeypatch):
    summary = load_script()

    monkeypatch.setattr(summary, "get_json", lambda url, timeout=10: {
        "status": "online",
        "mcp_ready": True,
        "tools_count": 90,
        "version": "18.0-MAX",
    })
    monkeypatch.setattr(summary.ana_live_reload_check, "check_live_reload", lambda mcp_url, timeout=20: {
        "status": "PASS",
        "marker": "ok",
        "has_marker": True,
        "next_action": "Live MCP loaded updated behavior.",
    })
    monkeypatch.setattr(summary.ana_memory_hygiene, "build_report", lambda keep_latest=20, include_plan=True: {
        "checkpoints": {"count": 10},
        "rem_sleep_reports": {"count": 2},
        "archive_candidates": 4,
        "archive_plan": {"total_moves": 4, "archive_date_basis": "utc"},
    })
    monkeypatch.setattr(summary, "latest_memory_archive_readiness", lambda: {
        "available": True,
        "status": "PASS",
        "total_moves": 4,
        "archive_date_basis": "utc",
    })
    monkeypatch.setattr(summary, "latest_trace_summary", lambda: {"available": True, "aligned": True})
    monkeypatch.setattr(summary, "git_dirty_summary", lambda: {"ok": True, "changed_paths": 0})
    monkeypatch.setattr(summary.ana_file_activity_snapshot, "build_report", lambda root, sample_limit=8: ({
        "baseline_available": True,
        "files_scanned": 20,
        "diff": {"created": 0, "deleted": 0, "modified": 0, "samples": {}},
        "privacy": {"content_read": False, "raw_private_payloads": False},
    }, {"manifest": {}}))
    monkeypatch.setattr(summary.ana_operator_status, "live_tool_surface", lambda mcp_url: {
        "status": "PASS",
        "live_count": 90,
        "manifest_count": 90,
        "extra_live": [],
        "missing_live": [],
    })
    monkeypatch.setattr(summary.ana_operator_status, "context_maps_status", lambda: {
        "status": "WARN",
        "code_map": {"status": "STALE", "summaries": 10, "stale_source": "ANA_MAX/tools/example.py"},
        "graph_map": {"status": "PASS", "nodes": 20, "edges": 30},
    })
    monkeypatch.setattr(summary.ana_identity_surface_check, "build_report", lambda: {
        "status": "PASS",
        "files_checked": 10,
        "violations": [],
        "missing_required": [],
    })
    monkeypatch.setattr(summary.ana_live_behavior_check, "build_report", lambda mcp_url, timeout=60: {
        "status": "PASS",
        "checks": {"session_audit_identity_surface_field": True},
    })

    report = summary.build_summary()

    assert report["reload_readiness"]["status"] == "PASS"
    assert report["context_maps"]["status"] == "WARN"
    assert report["recommended_next_step"].startswith("Run python ANA_MAX/dev_artifacts/scripts/ana_refresh_context_maps.py")


def test_reconcile_archive_readiness_marks_stale_candidate_count():
    summary = load_script()

    readiness = summary.reconcile_archive_readiness(
        {"archive_candidates": 12},
        {"available": True, "status": "PASS", "total_moves": 10},
    )

    assert readiness["status"] == "STALE"
    assert readiness["stale_reason"] == "archive_candidate_count_changed"
    assert readiness["current_archive_candidates"] == 12
    assert readiness["candidate_delta"] == 2


def test_format_archive_readiness_shows_delta():
    summary = load_script()

    rendered = summary.format_archive_readiness({"status": "STALE", "candidate_delta": 2})

    assert rendered == "STALE(+2)"


