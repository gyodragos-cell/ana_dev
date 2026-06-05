"""Tests for the lab-safe ANA autonomy runner."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "ana_autonomy_runner.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("ana_autonomy_runner", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_finalize_warns_on_optional_issue():
    runner = load_runner()
    report = {"status": "FAIL", "steps": [], "signals": {"trust_score": 92}}

    runner.add_step(report, "health", True)
    runner.add_step(report, "foreground_ui_snapshot", False, optional=True)
    runner.finalize(report)

    assert report["status"] == "WARN"
    assert report["summary"] == {"pass": 1, "warn": 1, "fail": 0, "total": 2}
    assert "Review warnings" in report["next_action"]


def test_finalize_fails_on_required_issue():
    runner = load_runner()
    report = {"status": "PASS", "steps": [], "signals": {"trust_score": 92}}

    runner.add_step(report, "health", False)
    runner.finalize(report)

    assert report["status"] == "FAIL"
    assert report["summary"]["fail"] == 1
    assert "Fix failed" in report["next_action"]


def test_compact_foreground_ui_snapshot_uses_real_tool_shape():
    runner = load_runner()
    payload = {
        "success": True,
        "message": "UI snapshot captured for: Code",
        "data": {
            "active_app": "Code",
            "title": "Lab - Visual Studio Code",
            "buttons": ["Run", "Clear"],
            "inputs": [{"name": "Output"}],
            "visible_text": ["ANA MAX"],
            "detected_errors": [],
        },
    }

    compact = runner.compact_tool_payload("foreground_ui_snapshot", payload)

    assert compact["app"] == "Code"
    assert compact["title"] == "Lab - Visual Studio Code"
    assert compact["buttons"] == 2
    assert compact["inputs"] == 1
    assert compact["visible_text"] == 1
    assert compact["detected_errors"] == 0


def test_compact_review_batch_runs_counts_categories():
    runner = load_runner()

    compact = runner.compact_tool_payload("review_batch_runs", {
        "status": "PASS",
        "planned_categories": ["runtime", "script"],
        "passed_categories": ["runtime", "script"],
        "missing_categories": [],
        "failing_categories": [],
        "policy": {"read_only": True, "executes_commands": False},
    })

    assert compact["status"] == "PASS"
    assert compact["planned_count"] == 2
    assert compact["passed_count"] == 2
    assert compact["categories"] == ["runtime", "script"]
    assert compact["missing_categories"] == []
    assert compact["stale_categories"] == []


def test_compact_live_behavior_counts_checks_and_failed_names():
    runner = load_runner()

    compact = runner.compact_tool_payload("live_behavior", {
        "status": "WARN",
        "checks": {
            "session_audit_identity_surface_field": True,
            "context_generated_memory_noise_filter": False,
        },
    })

    assert compact["status"] == "WARN"
    assert compact["checks_passed"] == 1
    assert compact["checks_total"] == 2
    assert compact["failed_checks"] == ["context_generated_memory_noise_filter"]
    assert compact["message"] == "live_behavior 1/2 checks failed=context_generated_memory_noise_filter"


def test_compact_context_maps_counts_and_stale_sources():
    runner = load_runner()

    compact = runner.compact_tool_payload("context_maps", {
        "status": "WARN",
        "code_map": {
            "status": "STALE",
            "summaries": 957,
            "stale_source": "ANA_MAX/dev_artifacts/scripts/ana_autonomy_runner.py",
        },
        "graph_map": {
            "status": "PASS",
            "nodes": 10617,
            "edges": 29182,
        },
    })

    assert compact["status"] == "WARN"
    assert compact["code_status"] == "STALE"
    assert compact["code_summaries"] == 957
    assert compact["graph_status"] == "PASS"
    assert compact["graph_nodes"] == 10617
    assert compact["graph_edges"] == 29182
    assert compact["stale_sources"] == ["code=ANA_MAX/dev_artifacts/scripts/ana_autonomy_runner.py"]
    assert compact["message"].startswith("code:STALE(957) graph:PASS")


def test_run_review_batch_runs_warns_when_category_missing(monkeypatch):
    runner = load_runner()
    monkeypatch.setattr(runner.ana_review_batch_runner, "build_report", lambda **kwargs: {
        "batches": [{"category": "runtime"}, {"category": "test"}],
    })
    monkeypatch.setattr(runner.ana_operator_status, "recent_review_batch_runs", lambda: {
        "categories": {
            "runtime": {
                "status": "PASS",
                "commands": 2,
                "passed": 2,
                "failed": 0,
                "timeout": 0,
            },
        },
        "order": ["runtime"],
    })

    report = runner.run_review_batch_runs()

    assert report["success"] is False
    assert report["status"] == "WARN"
    assert report["passed_categories"] == ["runtime"]
    assert report["missing_categories"] == ["test"]
    assert report["policy"]["executes_commands"] is False


def test_run_review_batch_runs_warns_when_category_stale(monkeypatch):
    runner = load_runner()
    monkeypatch.setattr(runner.ana_review_batch_runner, "build_report", lambda **kwargs: {
        "batches": [{"category": "runtime"}],
    })
    monkeypatch.setattr(runner.ana_operator_status, "recent_review_batch_runs", lambda: {
        "categories": {
            "runtime": {
                "status": "PASS",
                "commands": 2,
                "passed": 2,
                "failed": 0,
                "timeout": 0,
                "fresh": False,
            },
        },
        "order": ["runtime"],
    })

    report = runner.run_review_batch_runs()

    assert report["success"] is False
    assert report["status"] == "WARN"
    assert report["passed_categories"] == []
    assert report["stale_categories"] == ["runtime"]
    assert report["policy"]["freshness_checked"] is True


def test_safe_tool_call_retries_empty_foreground_snapshot(monkeypatch):
    runner = load_runner()
    report = {"steps": []}
    calls = []

    def fake_call_tool(mcp_url, name, arguments=None, timeout=30):
        calls.append(name)
        if len(calls) == 1:
            return {"success": False, "message": "Auto guidance attached from ANA memory/coach.", "data": {}}
        return {"success": True, "message": "UI snapshot captured for: Code", "data": {"active_app": "Code", "title": "Lab"}}

    monkeypatch.setattr(runner, "call_tool", fake_call_tool)
    monkeypatch.setattr(runner.time, "sleep", lambda seconds: None)

    payload = runner.safe_tool_call(
        report,
        "http://127.0.0.1:8766/mcp",
        "foreground_ui_snapshot",
        {"include_text": True},
        optional=True,
    )

    assert payload["success"] is True
    assert len(calls) == 2
    assert report["steps"][0]["status"] == "PASS"
    assert report["steps"][0]["data"]["app"] == "Code"


def test_run_autonomy_pass_uses_safe_read_only_stack(monkeypatch):
    runner = load_runner()
    calls: list[tuple[str, dict]] = []

    def fake_json_request(url, payload=None, timeout=30):
        return {"status": "online", "mcp_ready": True, "tools_count": 91}

    def fake_rpc(mcp_url, method, params=None, timeout=30):
        required = [
            "foreground_ui_snapshot",
            "code_context_pack",
            "graph_context_pack",
            "tool_router",
            "agent_coach",
            "tool_healthcheck",
            "error_radar",
            "session_audit",
        ]
        return {"result": {"tools": [{"name": name} for name in required]}}

    def fake_call_tool(mcp_url, name, arguments=None, timeout=30):
        calls.append((name, arguments or {}))
        payloads = {
            "foreground_ui_snapshot": {"success": True, "data": {"app": "Code", "title": "Lab", "elements": []}},
            "code_context_pack": {"success": True, "data": {"compressed_state": {"evidence": ["code_map"]}, "code_map": {"results": [1]}, "graph_map": {"results": [1]}}},
            "graph_context_pack": {"success": True, "data": {"stats": {"nodes": 10, "edges": 20}, "results": [1]}},
            "tool_router": {"success": True, "data": {"recommended_tools": ["code_context_pack"], "mode": "project_state"}},
            "agent_coach": {"success": True, "data": {"primary_tool": "code_context_pack", "tool_stack": ["code_context_pack"], "next_action": "Act once."}},
            "tool_healthcheck": {"success": True, "data": {"failed": 0, "ok": 7, "checked": 7}},
            "error_radar": {"success": True, "data": {"count": 0, "findings": []}},
            "session_audit": {"success": True, "data": {"trust": {"score": 95, "signals": {}}}},
        }
        return payloads[name]

    monkeypatch.setattr(runner, "json_request", fake_json_request)
    monkeypatch.setattr(runner, "rpc", fake_rpc)
    monkeypatch.setattr(runner, "call_tool", fake_call_tool)
    monkeypatch.setattr(runner, "run_patch_advisor", lambda mcp_url, timeout=30: {
        "success": True,
        "mode": "suggest_only",
        "inputs": {
            "dirty_tree_available": True,
            "dirty_tree_total": 42,
            "blast_radius_available": True,
            "blast_radius_affected": 2,
        },
        "dirty_tree": {
            "review_batches": [
                {
                    "category": "runtime",
                    "count": 23,
                    "tracked": 17,
                    "untracked": 6,
                    "next_step": "Run focused runtime tests and inspect owning modules first.",
                    "suggested_commands": ["python -m compileall -q ANA_MAX/core ANA_MAX/tools"],
                },
                {
                    "category": "script",
                    "count": 42,
                    "tracked": 2,
                    "untracked": 40,
                    "next_step": "Run focused script tests or dry-run CLIs before relying on automation.",
                },
            ]
        },
        "recommendations": [{"title": "Review graph blast-radius before editing", "next_step": "Read tests."}],
        "policy": {"writes_files": False},
    })
    monkeypatch.setattr(runner, "run_file_activity_snapshot", lambda: {
        "success": True,
        "data": {
            "baseline_available": True,
            "files_scanned": 20,
            "diff": {"created": 1, "deleted": 0, "modified": 2},
            "privacy": {"content_read": False, "raw_private_payloads": False},
            "next_action": "Review aggregate file activity if unexpected deletes/modifies appear.",
        },
        "message": "Review aggregate file activity if unexpected deletes/modifies appear.",
    })
    monkeypatch.setattr(runner, "run_memory_archive_readiness", lambda mcp_url: {
        "success": True,
        "data": {
            "available": True,
            "status": "PASS",
            "total_moves": 190,
            "failures": 0,
            "warnings": 0,
        },
        "message": "archive_readiness=PASS",
    })
    monkeypatch.setattr(runner, "run_review_batch_plan", lambda: {
        "success": True,
        "status": "DRY_RUN",
        "mode": "dry_run",
        "category": "all",
        "commands": [
            {
                "category": "runtime",
                "status": "planned",
                "command": "python -m compileall -q ANA_MAX/core ANA_MAX/tools",
            }
        ],
        "batches": [{"category": "runtime"}],
        "policy": {
            "all_batches_plan_only": True,
            "destructive_actions": False,
        },
    })
    monkeypatch.setattr(runner, "run_review_batch_runs", lambda: {
        "success": True,
        "status": "PASS",
        "planned_categories": ["runtime"],
        "passed_categories": ["runtime"],
        "missing_categories": [],
        "failing_categories": [],
        "policy": {"read_only": True, "executes_commands": False},
    })
    monkeypatch.setattr(
        runner.ana_live_reload_check,
        "check_live_reload",
        lambda mcp_url, timeout=20: {
            "status": "PASS",
            "marker": "data.stale",
            "has_marker": True,
            "next_action": "Live MCP loaded updated behavior.",
        },
    )
    monkeypatch.setattr(runner.ana_operator_status, "live_tool_surface", lambda mcp_url: {
        "status": "PASS",
        "live_count": 90,
        "manifest_count": 90,
        "extra_live": [],
        "missing_live": [],
    })
    monkeypatch.setattr(runner.ana_live_behavior_check, "build_report", lambda mcp_url, timeout=20: {
        "status": "PASS",
        "checks": {"session_audit_identity_surface_field": True},
    })
    monkeypatch.setattr(runner.ana_operator_status, "context_maps_status", lambda: {
        "status": "PASS",
        "code_map": {"status": "PASS", "summaries": 10},
        "graph_map": {"status": "PASS", "nodes": 10, "edges": 20},
    })

    report = runner.run_autonomy_pass("http://127.0.0.1:8766/mcp", "test autonomy", checkpoint=False)

    assert report["status"] == "PASS"
    assert report["run_id"].startswith("ana-autonomy-")
    assert report["signals"]["trust_score"] == 95
    assert report["next_action"].startswith("Continue with one new scoped lab action")
    assert "review batches verified 1/1" in report["next_action"]
    called_tools = [name for name, _ in calls]
    assert called_tools == [
        "foreground_ui_snapshot",
        "code_context_pack",
        "graph_context_pack",
        "tool_router",
        "agent_coach",
        "tool_healthcheck",
        "error_radar",
        "session_audit",
    ]
    assert any(step["name"] == "patch_advisor" for step in report["steps"])
    assert any(step["name"] == "review_batch_plan" for step in report["steps"])
    assert any(step["name"] == "review_batch_runs" for step in report["steps"])
    assert any(step["name"] == "file_activity_snapshot" for step in report["steps"])
    assert any(step["name"] == "memory_archive_readiness" for step in report["steps"])
    assert report["signals"]["patch_advisor"]["dirty_tree_available"] is True
    assert report["signals"]["patch_advisor"]["dirty_tree_total"] == 42
    assert report["signals"]["patch_advisor"]["first_review_batch"] == "runtime"
    assert report["signals"]["patch_advisor"]["review_batches"][0]["count"] == 23
    assert report["signals"]["patch_advisor"]["first_review_next_step"].startswith("Run focused runtime tests")
    assert report["signals"]["patch_advisor"]["first_review_commands"][0].startswith("python -m compileall")
    assert report["signals"]["patch_advisor"]["blast_radius_available"] is True
    assert report["signals"]["file_activity"]["created"] == 1
    assert report["signals"]["file_activity"]["deleted"] == 0
    assert report["signals"]["memory_archive_readiness"]["status"] == "PASS"
    assert report["signals"]["memory_archive_readiness"]["total_moves"] == 190
    assert report["signals"]["review_batch_plan"]["mode"] == "dry_run"
    assert report["signals"]["review_batch_plan"]["command_count"] == 1
    assert report["signals"]["review_batch_plan"]["first_command"].startswith("python -m compileall")
    assert report["signals"]["review_batch_runs"]["status"] == "PASS"
    assert report["signals"]["review_batch_runs"]["planned_count"] == 1
    assert report["signals"]["review_batch_runs"]["passed_count"] == 1
    assert report["signals"]["context_maps"]["status"] == "PASS"
    assert any(step["name"] == "context_maps" for step in report["steps"])
    assert len(report["trace_spans"]) == len(report["steps"])
    assert {span["operation"] for span in report["trace_spans"]} >= {"context_pack", "verification", "audit"}
    assert all(span["raw_private_payloads"] is False for span in report["trace_spans"])
    assert calls[0][1]["max_elements"] == "20"
    assert "desktop_control" not in called_tools
    assert "frida_instrument" not in called_tools
    assert any(step["name"] == "live_reload_marker" for step in report["steps"])
    assert any(step["name"] == "live_tool_surface" for step in report["steps"])
    assert any(step["name"] == "live_behavior" for step in report["steps"])


def test_run_autonomy_pass_can_write_optional_checkpoint(monkeypatch):
    runner = load_runner()
    calls: list[tuple[str, dict]] = []

    def fake_json_request(url, payload=None, timeout=30):
        return {"status": "online", "mcp_ready": True, "tools_count": 91}

    def fake_rpc(mcp_url, method, params=None, timeout=30):
        required = [
            "foreground_ui_snapshot",
            "code_context_pack",
            "graph_context_pack",
            "tool_router",
            "agent_coach",
            "tool_healthcheck",
            "error_radar",
            "session_audit",
            "session_checkpoint",
        ]
        return {"result": {"tools": [{"name": name} for name in required]}}

    def fake_call_tool(mcp_url, name, arguments=None, timeout=30):
        calls.append((name, arguments or {}))
        payloads = {
            "foreground_ui_snapshot": {"success": True, "data": {"app": "Code", "title": "Lab", "elements": []}},
            "code_context_pack": {"success": True, "data": {"compressed_state": {"evidence": ["code_map"]}, "code_map": {"results": [1]}, "graph_map": {"results": [1]}}},
            "graph_context_pack": {"success": True, "data": {"stats": {"nodes": 10, "edges": 20}, "results": [1]}},
            "tool_router": {"success": True, "data": {"recommended_tools": ["code_context_pack"], "mode": "project_state"}},
            "agent_coach": {"success": True, "data": {"primary_tool": "code_context_pack", "tool_stack": ["code_context_pack"], "next_action": "Act once."}},
            "tool_healthcheck": {"success": True, "data": {"failed": 0, "ok": 7, "checked": 7}},
            "error_radar": {"success": True, "data": {"count": 0, "findings": []}},
            "session_audit": {"success": True, "data": {"trust": {"score": 95, "signals": {}}}},
            "session_checkpoint": {"success": True, "data": {"path": "ANA_MAX/docs/SESSION_CHECKPOINT_TEST.md"}},
        }
        return payloads[name]

    monkeypatch.setattr(runner, "json_request", fake_json_request)
    monkeypatch.setattr(runner, "rpc", fake_rpc)
    monkeypatch.setattr(runner, "call_tool", fake_call_tool)
    monkeypatch.setattr(runner, "run_patch_advisor", lambda mcp_url, timeout=30: {
        "success": True,
        "mode": "suggest_only",
        "inputs": {},
        "recommendations": [],
        "policy": {"writes_files": False},
    })
    monkeypatch.setattr(runner, "run_file_activity_snapshot", lambda: {
        "success": True,
        "data": {
            "baseline_available": True,
            "files_scanned": 20,
            "diff": {"created": 0, "deleted": 0, "modified": 0},
            "privacy": {"content_read": False, "raw_private_payloads": False},
        },
    })
    monkeypatch.setattr(runner, "run_memory_archive_readiness", lambda mcp_url: {
        "success": True,
        "data": {"available": True, "status": "PASS", "total_moves": 190},
    })
    monkeypatch.setattr(runner, "run_review_batch_plan", lambda: {
        "success": True,
        "status": "DRY_RUN",
        "mode": "dry_run",
        "category": "all",
        "commands": [],
        "batches": [],
        "policy": {"all_batches_plan_only": True, "destructive_actions": False},
    })
    monkeypatch.setattr(runner, "run_review_batch_runs", lambda: {
        "success": True,
        "status": "PASS",
        "planned_categories": [],
        "passed_categories": [],
        "missing_categories": [],
        "failing_categories": [],
        "policy": {"read_only": True, "executes_commands": False},
    })
    monkeypatch.setattr(
        runner.ana_live_reload_check,
        "check_live_reload",
        lambda mcp_url, timeout=20: {
            "status": "PASS",
            "marker": "data.stale",
            "has_marker": True,
            "next_action": "Live MCP loaded updated behavior.",
        },
    )
    monkeypatch.setattr(runner.ana_operator_status, "live_tool_surface", lambda mcp_url: {
        "status": "PASS",
        "live_count": 90,
        "manifest_count": 90,
        "extra_live": [],
        "missing_live": [],
    })
    monkeypatch.setattr(runner.ana_live_behavior_check, "build_report", lambda mcp_url, timeout=20: {
        "status": "PASS",
        "checks": {"session_audit_identity_surface_field": True},
    })
    monkeypatch.setattr(runner.ana_operator_status, "context_maps_status", lambda: {
        "status": "PASS",
        "code_map": {"status": "PASS", "summaries": 10},
        "graph_map": {"status": "PASS", "nodes": 10, "edges": 20},
    })

    report = runner.run_autonomy_pass("http://127.0.0.1:8766/mcp", "test autonomy", checkpoint=True)

    assert report["status"] == "PASS"
    assert calls[-1][0] == "session_checkpoint"
    assert calls[-1][1]["include_git"] is True
    assert "Autonomy Pass checkpoint" in calls[-1][1]["title"]


def test_live_reload_warning_takes_next_action_priority(monkeypatch):
    runner = load_runner()
    calls: list[tuple[str, dict]] = []

    def fake_json_request(url, payload=None, timeout=30):
        return {"status": "online", "mcp_ready": True, "tools_count": 91}

    def fake_rpc(mcp_url, method, params=None, timeout=30):
        required = [
            "foreground_ui_snapshot",
            "code_context_pack",
            "graph_context_pack",
            "tool_router",
            "agent_coach",
            "tool_healthcheck",
            "error_radar",
            "session_audit",
        ]
        return {"result": {"tools": [{"name": name} for name in required]}}

    def fake_call_tool(mcp_url, name, arguments=None, timeout=30):
        calls.append((name, arguments or {}))
        payloads = {
            "foreground_ui_snapshot": {"success": True, "data": {"app": "Code", "title": "Lab", "elements": []}},
            "code_context_pack": {"success": True, "data": {"compressed_state": {"evidence": ["code_map"]}, "code_map": {"results": [1]}, "graph_map": {"results": [1]}}},
            "graph_context_pack": {"success": True, "data": {"stats": {"nodes": 10, "edges": 20}, "results": [1]}},
            "tool_router": {"success": True, "data": {"recommended_tools": ["code_context_pack"], "mode": "project_state"}},
            "agent_coach": {"success": True, "data": {"primary_tool": "code_context_pack", "tool_stack": ["code_context_pack"], "next_action": "Act once."}},
            "tool_healthcheck": {"success": True, "data": {"failed": 0, "ok": 7, "checked": 7}},
            "error_radar": {"success": True, "data": {"count": 0, "findings": []}},
            "session_audit": {"success": True, "data": {"trust": {"score": 95, "signals": {}}}},
        }
        return payloads[name]

    monkeypatch.setattr(runner, "json_request", fake_json_request)
    monkeypatch.setattr(runner, "rpc", fake_rpc)
    monkeypatch.setattr(runner, "call_tool", fake_call_tool)
    monkeypatch.setattr(runner, "run_patch_advisor", lambda mcp_url, timeout=30: {
        "success": True,
        "mode": "suggest_only",
        "inputs": {},
        "recommendations": [],
        "policy": {"writes_files": False},
    })
    monkeypatch.setattr(runner, "run_file_activity_snapshot", lambda: {
        "success": True,
        "data": {
            "baseline_available": True,
            "files_scanned": 20,
            "diff": {"created": 0, "deleted": 0, "modified": 0},
            "privacy": {"content_read": False, "raw_private_payloads": False},
        },
    })
    monkeypatch.setattr(runner, "run_memory_archive_readiness", lambda mcp_url: {
        "success": True,
        "data": {"available": True, "status": "PASS", "total_moves": 190},
    })
    monkeypatch.setattr(runner, "run_review_batch_plan", lambda: {
        "success": True,
        "status": "DRY_RUN",
        "mode": "dry_run",
        "category": "all",
        "commands": [],
        "batches": [],
        "policy": {"all_batches_plan_only": True, "destructive_actions": False},
    })
    monkeypatch.setattr(runner, "run_review_batch_runs", lambda: {
        "success": True,
        "status": "PASS",
        "planned_categories": [],
        "passed_categories": [],
        "missing_categories": [],
        "failing_categories": [],
        "policy": {"read_only": True, "executes_commands": False},
    })
    monkeypatch.setattr(
        runner.ana_live_reload_check,
        "check_live_reload",
        lambda mcp_url, timeout=20: {
            "status": "WARN",
            "marker": "data.stale",
            "has_marker": False,
            "next_action": "Restart/reload ANA MCP server, then rerun Autonomy Pass.",
        },
    )
    monkeypatch.setattr(runner.ana_operator_status, "live_tool_surface", lambda mcp_url: {
        "status": "PASS",
        "live_count": 90,
        "manifest_count": 90,
        "extra_live": [],
        "missing_live": [],
    })
    monkeypatch.setattr(runner.ana_live_behavior_check, "build_report", lambda mcp_url, timeout=20: {
        "status": "PASS",
        "checks": {"session_audit_identity_surface_field": True},
    })
    monkeypatch.setattr(runner.ana_operator_status, "context_maps_status", lambda: {
        "status": "PASS",
        "code_map": {"status": "PASS", "summaries": 10},
        "graph_map": {"status": "PASS", "nodes": 10, "edges": 20},
    })

    report = runner.run_autonomy_pass("http://127.0.0.1:8766/mcp", "test autonomy", checkpoint=False)

    assert report["status"] == "WARN"
    assert report["signals"]["live_reload"]["status"] == "WARN"
    assert report["next_action"].startswith("Restart/reload ANA MCP server")


def test_live_tool_surface_warning_takes_next_action_priority(monkeypatch):
    runner = load_runner()
    report = {
        "status": "WARN",
        "steps": [],
        "signals": {
            "trust_score": 95,
            "live_reload": {"status": "PASS"},
            "live_tool_surface": {"status": "WARN", "extra_live": 1},
            "live_behavior": {"status": "PASS"},
            "coach": {"next_action": "Act once."},
        },
    }

    runner.finalize(report)

    assert report["next_action"].startswith("Restart ANA MCP so live tools/list")


def test_context_maps_warning_takes_next_action_priority():
    runner = load_runner()
    report = {
        "status": "WARN",
        "steps": [],
        "signals": {
            "trust_score": 95,
            "live_reload": {"status": "PASS"},
            "live_tool_surface": {"status": "PASS"},
            "live_behavior": {"status": "PASS"},
            "context_maps": {"status": "WARN", "code_status": "STALE"},
            "coach": {"next_action": "Act once."},
        },
    }

    runner.finalize(report)

    assert report["next_action"].startswith("Run python ANA_MAX/dev_artifacts/scripts/ana_refresh_context_maps.py")


def test_verified_review_batches_take_priority_over_coach_action():
    runner = load_runner()
    report = {
        "status": "PASS",
        "steps": [],
        "signals": {
            "live_reload": {"status": "PASS"},
            "live_tool_surface": {"status": "PASS"},
            "live_behavior": {"status": "PASS"},
            "review_batch_runs": {
                "status": "PASS",
                "planned_count": 6,
                "passed_count": 6,
                "missing_categories": [],
                "failing_categories": [],
            },
            "coach": {"next_action": "Call code_context_pack."},
        },
    }

    next_action = runner.build_next_action(report)

    assert next_action.startswith("Continue with one new scoped lab action")
    assert "review batches verified 6/6" in next_action


def test_incomplete_review_batch_coverage_keeps_coach_action():
    runner = load_runner()
    report = {
        "status": "PASS",
        "steps": [],
        "signals": {
            "live_reload": {"status": "PASS"},
            "live_tool_surface": {"status": "PASS"},
            "live_behavior": {"status": "PASS"},
            "review_batch_runs": {
                "status": "PASS",
                "planned_count": 6,
                "passed_count": 5,
                "missing_categories": ["doc"],
                "failing_categories": [],
            },
            "coach": {"next_action": "Call code_context_pack."},
        },
    }

    assert runner.build_next_action(report) == "Call code_context_pack."


def test_stale_review_batch_coverage_keeps_coach_action():
    runner = load_runner()
    report = {
        "status": "PASS",
        "steps": [],
        "signals": {
            "live_reload": {"status": "PASS"},
            "live_tool_surface": {"status": "PASS"},
            "live_behavior": {"status": "PASS"},
            "review_batch_runs": {
                "status": "WARN",
                "planned_count": 6,
                "passed_count": 5,
                "missing_categories": [],
                "failing_categories": [],
                "stale_categories": ["script"],
            },
            "coach": {"next_action": "Call code_context_pack."},
        },
    }

    assert runner.build_next_action(report) == "Call code_context_pack."


def test_live_behavior_warning_takes_next_action_priority(monkeypatch):
    runner = load_runner()
    report = {
        "status": "WARN",
        "steps": [],
        "signals": {
            "trust_score": 95,
            "live_reload": {"status": "PASS"},
            "live_tool_surface": {"status": "PASS"},
            "live_behavior": {"status": "WARN", "checks_total": 2},
            "coach": {"next_action": "Act once."},
        },
    }

    runner.finalize(report)

    assert report["next_action"].startswith("Restart ANA MCP, then run Live Behavior")


def test_patch_advisor_step_warns_if_not_suggest_only(monkeypatch):
    runner = load_runner()
    report = {"steps": []}

    payload = runner.add_local_report_step(
        report,
        "patch_advisor",
        {"success": True, "mode": "apply", "policy": {"writes_files": True}},
        predicate=lambda p: p.get("mode") == "suggest_only" and p.get("policy", {}).get("writes_files") is False,
        optional=True,
    )

    assert payload["mode"] == "apply"
    assert report["steps"][0]["status"] == "WARN"


def test_add_step_emits_trace_when_report_has_trace_spans():
    runner = load_runner()
    report = {
        "run_id": "run-test",
        "trace_id": "trace-test",
        "steps": [],
        "trace_spans": [],
    }

    runner.add_step(report, "tool_healthcheck", True, {"ok": 7, "secret": "hidden"})

    assert len(report["trace_spans"]) == 1
    span = report["trace_spans"][0]
    assert span["schema"] == "ana.agent_trace_span.v1"
    assert span["run_id"] == "run-test"
    assert span["trace_id"] == "trace-test"
    assert span["operation"] == "verification"
    assert span["status"] == "ok"
    assert "hidden" not in str(span)


def test_print_human_includes_trace_alignment(capsys):
    runner = load_runner()
    report = {
        "status": "PASS",
        "summary": {"pass": 1, "warn": 0, "fail": 0},
        "signals": {"trust_score": 90},
        "steps": [{"name": "health", "status": "PASS"}],
        "trace_spans": [{"schema": "ana.agent_trace_span.v1"}],
        "next_action": "Continue.",
    }

    runner.print_human(report)

    output = capsys.readouterr().out
    assert "trace=1/1 aligned=True" in output
