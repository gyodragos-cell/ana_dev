"""Tests for compact ANA operator status."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import json


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "ana_operator_status.py"


def load_script():
    script_dir = str(SCRIPT.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location("ana_operator_status", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def context_maps_pass():
    return {
        "status": "PASS",
        "code_map": {"status": "PASS", "summaries": 10},
        "graph_map": {"status": "PASS", "nodes": 20, "edges": 30},
    }


def test_operator_status_recommends_reload_when_marker_missing(monkeypatch):
    script = load_script()
    monkeypatch.setattr(script, "read_package", lambda: {"version": "1.0.45"})
    monkeypatch.setattr(script, "latest_handoff", lambda: {"checkpoint": "SESSION.md"})
    monkeypatch.setattr(script, "latest_rem_sleep", lambda: {"file": "REM.md", "timestamp": "2026"})
    monkeypatch.setattr(script, "latest_autonomy_patch_advisor", lambda: {
        "first_review_batch": "runtime",
        "first_review_commands": ["python -m compileall -q ANA_MAX/core ANA_MAX/tools"],
    })
    monkeypatch.setattr(script, "live_tool_surface", lambda mcp_url: {
        "status": "PASS",
        "live_count": 90,
        "manifest_count": 90,
        "extra_live": [],
        "missing_live": [],
    })
    monkeypatch.setattr(script.ana_lab_state_summary, "build_summary", lambda mcp_url: {
        "mcp": {"mcp_ready": True, "tools_count": 91},
        "live_reload": {"status": "WARN", "has_marker": False},
        "live_behavior": {"status": "PASS", "checks": {"session_audit_identity_surface_field": True}},
        "identity_surface": {"status": "PASS", "files_checked": 10, "violations": 0, "missing_required": 0},
        "git": {"changed_paths": 10},
        "memory_hygiene": {
            "archive_candidates": 2,
            "archive_readiness": {"status": "PASS", "total_moves": 2},
        },
        "file_activity": {"diff": {"created": 1, "deleted": 2, "modified": 3}},
    })

    status = script.build_status()

    assert status["schema"] == "ana.operator_status.v1"
    assert status["package"]["version"] == "1.0.45"
    assert "install_latest_lab_vsix.ps1 -Apply" in status["install_command"]
    assert status["verify_command"].endswith("ana_post_reload_verify.py --no-write")
    assert status["recommended_next_step"].startswith("Install VSIX")
    assert "no_reload_quality_gate" in status["reports"]
    assert "trace_report" in status["reports"]
    assert status["rem_sleep"]["file"] == "REM.md"
    assert status["next_verification"]["first_review_batch"] == "runtime"
    assert status["file_activity"]["diff"]["deleted"] == 2
    assert status["reload_readiness"]["status"] == "WARN"
    assert status["reload_readiness"]["reload_needed"] is True
    assert status["reload_readiness"]["reasons"] == ["missing_reload_marker"]
    assert status["live_tool_surface"]["status"] == "PASS"
    assert status["live_behavior"]["status"] == "PASS"
    assert status["identity_surface"]["status"] == "PASS"


def test_operator_status_recommends_autonomy_when_marker_present(monkeypatch):
    script = load_script()
    monkeypatch.setattr(script, "read_package", lambda: {"version": "1.0.45"})
    monkeypatch.setattr(script, "latest_handoff", lambda: {"checkpoint": "SESSION.md"})
    monkeypatch.setattr(script, "latest_report", lambda pattern: {"file": "", "status": "", "summary": ""})
    monkeypatch.setattr(script, "latest_trace_status", lambda: {"file": "", "status": "", "summary": ""})
    monkeypatch.setattr(script, "latest_autonomy_patch_advisor", lambda: {})
    monkeypatch.setattr(script, "live_tool_surface", lambda mcp_url: {
        "status": "PASS",
        "live_count": 90,
        "manifest_count": 90,
        "extra_live": [],
        "missing_live": [],
    })
    monkeypatch.setattr(script.ana_lab_state_summary, "build_summary", lambda mcp_url: {
        "mcp": {"mcp_ready": True, "tools_count": 91},
        "live_reload": {"status": "PASS", "has_marker": True},
        "live_behavior": {"status": "PASS", "checks": {"session_audit_identity_surface_field": True}},
        "identity_surface": {"status": "PASS", "files_checked": 10, "violations": 0, "missing_required": 0},
        "git": {"changed_paths": 10},
        "memory_hygiene": {"archive_candidates": 2},
        "file_activity": {"diff": {"created": 0, "deleted": 0, "modified": 0}},
    })

    status = script.build_status()

    assert status["reload_readiness"]["status"] == "PASS"
    assert status["reload_readiness"]["reload_needed"] is False
    assert status["reload_readiness"]["reasons"] == []
    assert status["recommended_next_step"].startswith("Run Autonomy Pass")


def test_operator_status_recommends_scoped_action_after_clean_autonomy(monkeypatch):
    script = load_script()
    monkeypatch.setattr(script, "read_package", lambda: {"version": "1.0.45"})
    monkeypatch.setattr(script, "latest_handoff", lambda: {"checkpoint": "SESSION.md"})
    monkeypatch.setattr(script, "context_maps_status", context_maps_pass)
    monkeypatch.setattr(script, "latest_report", lambda pattern: {
        "file": "autonomy_runner.json",
        "status": "PASS",
        "summary": "pass=17,warn=0",
    } if pattern == "autonomy_runner_*.json" else {"file": "", "status": "", "summary": ""})
    monkeypatch.setattr(script, "latest_trace_status", lambda: {"file": "autonomy_runner.json", "status": "PASS"})
    monkeypatch.setattr(script, "latest_autonomy_patch_advisor", lambda: {
        "first_review_batch": "runtime",
        "first_review_commands": ["python -m compileall -q ANA_MAX/core ANA_MAX/tools"],
    })
    monkeypatch.setattr(script, "live_tool_surface", lambda mcp_url: {
        "status": "PASS",
        "live_count": 90,
        "manifest_count": 90,
        "extra_live": [],
        "missing_live": [],
    })
    monkeypatch.setattr(script.ana_lab_state_summary, "build_summary", lambda mcp_url: {
        "mcp": {"mcp_ready": True, "tools_count": 90},
        "live_reload": {"status": "PASS", "has_marker": True},
        "live_behavior": {"status": "PASS", "checks": {"session_audit_identity_surface_field": True}},
        "identity_surface": {"status": "PASS", "files_checked": 10, "violations": 0, "missing_required": 0},
        "git": {"changed_paths": 10},
        "memory_hygiene": {"archive_candidates": 2},
        "file_activity": {"diff": {"created": 0, "deleted": 0, "modified": 0}},
    })

    status = script.build_status()

    assert status["reload_readiness"]["status"] == "PASS"
    assert status["reports"]["autonomy_runner"]["status"] == "PASS"
    assert status["next_verification"]["first_review_commands"][0].startswith("python -m compileall")
    assert status["recommended_next_step"] == "Continue with one scoped lab action."


def test_operator_status_recommends_reload_when_live_tool_surface_has_drift(monkeypatch):
    script = load_script()
    monkeypatch.setattr(script, "read_package", lambda: {"version": "1.0.45"})
    monkeypatch.setattr(script, "latest_handoff", lambda: {"checkpoint": "SESSION.md"})
    monkeypatch.setattr(script, "latest_report", lambda pattern: {"file": "", "status": "", "summary": ""})
    monkeypatch.setattr(script, "latest_trace_status", lambda: {"file": "", "status": "", "summary": ""})
    monkeypatch.setattr(script, "latest_autonomy_patch_advisor", lambda: {})
    monkeypatch.setattr(script.ana_lab_state_summary, "build_summary", lambda mcp_url: {
        "mcp": {"mcp_ready": True, "tools_count": 91},
        "live_reload": {"status": "PASS", "has_marker": True},
        "live_behavior": {"status": "PASS", "checks": {"session_audit_identity_surface_field": True}},
        "identity_surface": {"status": "PASS", "files_checked": 10, "violations": 0, "missing_required": 0},
        "git": {"changed_paths": 10},
        "memory_hygiene": {"archive_candidates": 2},
        "file_activity": {"diff": {"created": 0, "deleted": 0, "modified": 0}},
    })
    monkeypatch.setattr(script, "live_tool_surface", lambda mcp_url: {
        "status": "WARN",
        "live_count": 91,
        "manifest_count": 90,
        "extra_live": ["adal_integration"],
        "missing_live": [],
    })

    status = script.build_status()

    assert status["live_tool_surface"]["extra_live"] == ["adal_integration"]
    assert status["reload_readiness"]["status"] == "WARN"
    assert status["reload_readiness"]["reasons"] == ["live_tool_surface_drift"]
    assert status["recommended_next_step"].startswith("Install VSIX")


def test_operator_status_recommends_reload_when_live_behavior_has_drift(monkeypatch):
    script = load_script()
    monkeypatch.setattr(script, "read_package", lambda: {"version": "1.0.45"})
    monkeypatch.setattr(script, "latest_handoff", lambda: {"checkpoint": "SESSION.md"})
    monkeypatch.setattr(script, "latest_report", lambda pattern: {"file": "", "status": "", "summary": ""})
    monkeypatch.setattr(script, "latest_trace_status", lambda: {"file": "", "status": "", "summary": ""})
    monkeypatch.setattr(script, "latest_autonomy_patch_advisor", lambda: {})
    monkeypatch.setattr(script, "live_tool_surface", lambda mcp_url: {
        "status": "PASS",
        "live_count": 90,
        "manifest_count": 90,
        "extra_live": [],
        "missing_live": [],
    })
    monkeypatch.setattr(script.ana_lab_state_summary, "build_summary", lambda mcp_url: {
        "mcp": {"mcp_ready": True, "tools_count": 90},
        "live_reload": {"status": "PASS", "has_marker": True},
        "live_behavior": {"status": "WARN", "checks": {"session_audit_identity_surface_field": False}},
        "identity_surface": {"status": "PASS", "files_checked": 10, "violations": 0, "missing_required": 0},
        "git": {"changed_paths": 10},
        "memory_hygiene": {"archive_candidates": 2},
        "file_activity": {"diff": {"created": 0, "deleted": 0, "modified": 0}},
    })

    status = script.build_status()

    assert status["live_behavior"]["status"] == "WARN"
    assert status["reload_readiness"]["status"] == "WARN"
    assert status["reload_readiness"]["reasons"] == ["live_behavior_stale"]
    assert status["recommended_next_step"].startswith("Restart ANA MCP")


def test_operator_status_prioritizes_identity_problem(monkeypatch):
    script = load_script()
    monkeypatch.setattr(script, "read_package", lambda: {"version": "1.0.45"})
    monkeypatch.setattr(script, "latest_handoff", lambda: {"checkpoint": "SESSION.md"})
    monkeypatch.setattr(script, "latest_report", lambda pattern: {"file": "", "status": "", "summary": ""})
    monkeypatch.setattr(script, "latest_trace_status", lambda: {"file": "", "status": "", "summary": ""})
    monkeypatch.setattr(script, "latest_autonomy_patch_advisor", lambda: {})
    monkeypatch.setattr(script, "live_tool_surface", lambda mcp_url: {
        "status": "PASS",
        "live_count": 90,
        "manifest_count": 90,
        "extra_live": [],
        "missing_live": [],
    })
    monkeypatch.setattr(script.ana_lab_state_summary, "build_summary", lambda mcp_url: {
        "mcp": {"mcp_ready": True, "tools_count": 90},
        "live_reload": {"status": "PASS", "has_marker": True},
        "live_behavior": {"status": "PASS", "checks": {"session_audit_identity_surface_field": True}},
        "identity_surface": {"status": "FAIL", "files_checked": 10, "violations": 1, "missing_required": 0},
        "git": {"changed_paths": 10},
        "memory_hygiene": {"archive_candidates": 2},
        "file_activity": {"diff": {"created": 0, "deleted": 0, "modified": 0}},
    })

    status = script.build_status()

    assert status["identity_surface"]["status"] == "FAIL"
    assert status["recommended_next_step"].startswith("Fix active identity surface")


def test_recommended_next_step_keeps_vsix_flow_for_marker_or_surface():
    script = load_script()

    marker = script.build_recommended_next_step(False, ["missing_reload_marker"])
    surface = script.build_recommended_next_step(False, ["live_tool_surface_drift"])

    assert marker.startswith("Install VSIX")
    assert surface.startswith("Install VSIX")


def test_recommended_next_step_refreshes_stale_context_maps_after_clean_autonomy():
    script = load_script()

    next_step = script.build_recommended_next_step(
        False,
        [],
        {"autonomy_runner": {"status": "PASS"}},
        {
            "code_map": {"status": "STALE"},
            "graph_map": {"status": "PASS"},
        },
    )

    assert next_step.startswith("Run python ANA_MAX/dev_artifacts/scripts/ana_refresh_context_maps.py")


def test_latest_report_returns_newest_named_report(tmp_path):
    script = load_script()
    older = tmp_path / "lab_quality_gate_20260531_010000.json"
    newer = tmp_path / "lab_quality_gate_20260531_020000.json"
    older.write_text(json.dumps({"status": "FAIL"}), encoding="utf-8")
    newer.write_text(json.dumps({"status": "PASS", "steps": [{"status": "PASS"}]}), encoding="utf-8")

    report = script.latest_report("lab_quality_gate_*.json", tmp_path)

    assert report["file"] == newer.name
    assert report["path"].endswith(newer.name)
    assert report["status"] == "PASS"
    assert report["summary"] == "pass=1"


def test_latest_trace_status_uses_autonomy_when_trace_is_stale(tmp_path, monkeypatch):
    script = load_script()
    autonomy = tmp_path / "autonomy_runner_20260531_020000.json"
    trace = tmp_path / "trace_report_20260531_010000.json"
    autonomy.write_text(json.dumps({"status": "PASS"}), encoding="utf-8")
    trace.write_text(json.dumps({"schema": "ana.trace_report.v1", "ok": True, "steps": 1, "spans": 1, "aligned": True}), encoding="utf-8")

    monkeypatch.setattr(script.ana_trace_report, "summarize_report", lambda path: {
        "ok": True,
        "steps": 12,
        "spans": 12,
        "aligned": True,
    })

    report = script.latest_trace_status(tmp_path)

    assert report["file"] == autonomy.name
    assert report["status"] == "PASS"
    assert report["summary"] == "steps=12,spans=12,aligned=True"


def test_latest_autonomy_patch_advisor_extracts_first_review_command(tmp_path):
    script = load_script()
    report_path = tmp_path / "autonomy_runner_20260531_020000.json"
    report_path.write_text(
        json.dumps({
            "steps": [
                {
                    "name": "patch_advisor",
                    "data": {
                        "first_review_batch": "runtime",
                        "first_review_next_step": "Run focused runtime tests.",
                        "first_review_commands": [
                            "python -m compileall -q ANA_MAX/core ANA_MAX/tools",
                            "python -m pytest tests/runtime/test_tool_router_tool.py -q",
                        ],
                    },
                },
                {
                    "name": "review_batch_plan",
                    "data": {
                        "status": "DRY_RUN",
                        "mode": "dry_run",
                        "category": "all",
                        "batch_count": 6,
                        "command_count": 10,
                        "batches": ["runtime", "script", "test", "config", "extension", "doc"],
                        "first_command": "python -m compileall -q ANA_MAX/core ANA_MAX/tools",
                    },
                },
            ]
        }),
        encoding="utf-8",
    )

    data = script.latest_autonomy_patch_advisor(tmp_path)

    assert data["file"] == report_path.name
    assert data["first_review_batch"] == "runtime"
    assert data["first_review_commands"][0].startswith("python -m compileall")
    assert data["review_batch_plan"]["mode"] == "dry_run"
    assert data["review_batch_plan"]["batch_count"] == 6
    assert data["review_batch_plan"]["command_count"] == 10
    assert data["review_batch_plan"]["batches"][:2] == ["runtime", "script"]


def test_latest_review_batch_run_summarizes_command_results(tmp_path):
    script = load_script()
    report_path = tmp_path / "review_batch_runner_20260601_175453.json"
    report_path.write_text(
        json.dumps({
            "schema": "ana.review_batch_runner.v1",
            "status": "PASS",
            "mode": "run",
            "category": "runtime",
            "commands": [
                {"status": "pass", "command": "python -m compileall -q ANA_MAX/core"},
                {"status": "pass", "command": "python -m pytest tests/runtime/test_tool_router_tool.py -q"},
            ],
        }),
        encoding="utf-8",
    )

    data = script.latest_review_batch_run(tmp_path)

    assert data["file"] == report_path.name
    assert data["status"] == "PASS"
    assert data["mode"] == "run"
    assert data["category"] == "runtime"
    assert data["commands"] == 2
    assert data["passed"] == 2
    assert data["failed"] == 0
    assert data["first_command"].startswith("python -m compileall")


def test_recent_review_batch_runs_keeps_latest_per_category(tmp_path):
    script = load_script()
    older = tmp_path / "review_batch_runner_20260601_175453.json"
    newer = tmp_path / "review_batch_runner_20260601_180250.json"
    doc = tmp_path / "review_batch_runner_20260601_180706.json"
    older.write_text(
        json.dumps({
            "status": "FAIL",
            "mode": "run",
            "category": "test",
            "commands": [{"status": "fail", "command": "python -m pytest tests/runtime -q"}],
        }),
        encoding="utf-8",
    )
    newer.write_text(
        json.dumps({
            "status": "PASS",
            "mode": "run",
            "category": "test",
            "commands": [{"status": "pass", "command": "python -m pytest tests/runtime -q"}],
        }),
        encoding="utf-8",
    )
    doc.write_text(
        json.dumps({
            "status": "PASS",
            "mode": "run",
            "category": "doc",
            "commands": [{"status": "pass", "command": "python ANA_MAX/dev_artifacts/scripts/ana_governance_check.py"}],
        }),
        encoding="utf-8",
    )

    data = script.recent_review_batch_runs(tmp_path)

    assert data["order"] == ["test", "doc"]
    assert data["categories"]["test"]["status"] == "PASS"
    assert data["categories"]["test"]["file"] == newer.name
    assert data["categories"]["doc"]["passed"] == 1


def test_recent_review_batch_runs_marks_stale_category(tmp_path):
    script = load_script()
    report_path = tmp_path / "review_batch_runner_20260601_180250.json"
    report_path.write_text(
        json.dumps({
            "status": "PASS",
            "mode": "run",
            "category": "test",
            "commands": [{"status": "pass", "command": "python -m pytest tests/runtime -q"}],
        }),
        encoding="utf-8",
    )

    data = script.recent_review_batch_runs(
        tmp_path,
        freshness={
            "available": True,
            "categories": {
                "test": {
                    "latest_mtime": script.safe_mtime(report_path) + 30,
                    "latest_path": "tests/runtime/test_ana_operator_status.py",
                },
            },
        },
    )

    assert data["categories"]["test"]["status"] == "PASS"
    assert data["categories"]["test"]["fresh"] is False
    assert data["categories"]["test"]["latest_active_path"] == "tests/runtime/test_ana_operator_status.py"


def test_summarize_report_handles_no_reload_summary(tmp_path):
    script = load_script()
    report_path = tmp_path / "no_reload_quality_gate_20260531_020000.json"
    report_path.write_text(
        json.dumps({"summary": {"pass": 7}, "advisory_summary": {"warn": 1}}),
        encoding="utf-8",
    )

    report = script.summarize_report(report_path)

    assert report["status"] == "PASS"
    assert report["summary"] == "pass=7,advisory_warn=1"


def test_summarize_report_handles_trace_report(tmp_path):
    script = load_script()
    report_path = tmp_path / "trace_report_20260531_020000.json"
    report_path.write_text(
        json.dumps({
            "schema": "ana.trace_report.v1",
            "ok": True,
            "steps": 12,
            "spans": 12,
            "aligned": True,
        }),
        encoding="utf-8",
    )

    report = script.summarize_report(report_path)

    assert report["status"] == "PASS"
    assert report["summary"] == "steps=12,spans=12,aligned=True"


def test_format_report_includes_status_and_summary():
    script = load_script()

    rendered = script.format_report({"file": "gate.json", "status": "PASS", "summary": "pass=7"})

    assert rendered == "gate.json:PASS(pass=7)"


def test_format_package_artifacts_shows_main_and_copy_status():
    script = load_script()

    ready = script.format_package_artifacts({
        "main_vsix_exists": True,
        "copy_vsix_exists": True,
    })
    missing_copy = script.format_package_artifacts({
        "main_vsix_exists": True,
        "copy_vsix_exists": False,
    })

    assert ready == "PASS(main=True,copy=True)"
    assert missing_copy == "WARN(main=True,copy=False)"


def test_latest_rem_sleep_returns_newest_written_report(tmp_path):
    script = load_script()
    older = tmp_path / "REM_SLEEP_REPORT_2026-05-31T190000+0000.md"
    newer = tmp_path / "REM_SLEEP_REPORT_2026-05-31T221219+0000.md"
    older.write_text("# old", encoding="utf-8")
    newer.write_text("# new", encoding="utf-8")

    report = script.latest_rem_sleep(tmp_path)

    assert report["file"] == newer.name
    assert report["path"].endswith(newer.name)
    assert report["timestamp"] == "2026-05-31T221219+0000"


def test_format_rem_sleep_includes_timestamp():
    script = load_script()

    rendered = script.format_rem_sleep({"file": "REM_SLEEP_REPORT_X.md", "timestamp": "X"})

    assert rendered == "REM_SLEEP_REPORT_X.md(X)"


def test_format_next_verification_includes_first_command():
    script = load_script()

    rendered = script.format_next_verification({
        "first_review_batch": "runtime",
        "first_review_commands": ["python -m compileall -q ANA_MAX/core ANA_MAX/tools"],
    })

    assert rendered == "batch=runtime command=python -m compileall -q ANA_MAX/core ANA_MAX/tools"


def test_format_next_verification_includes_review_plan_summary():
    script = load_script()

    rendered = script.format_next_verification({
        "first_review_batch": "runtime",
        "first_review_commands": ["python -m compileall -q ANA_MAX/core ANA_MAX/tools"],
        "review_batch_plan": {
            "mode": "dry_run",
            "batch_count": 6,
            "command_count": 10,
        },
    })

    assert rendered == (
        "batch=runtime command=python -m compileall -q ANA_MAX/core ANA_MAX/tools "
        "plan=dry_run batches=6 commands=10"
    )


def test_format_next_verification_includes_review_coverage_when_all_passed():
    script = load_script()

    rendered = script.format_next_verification(
        {
            "first_review_batch": "runtime",
            "first_review_commands": ["python -m compileall -q ANA_MAX/core ANA_MAX/tools"],
            "review_batch_plan": {
                "mode": "dry_run",
                "batch_count": 2,
                "command_count": 3,
                "batches": ["runtime", "test"],
            },
        },
        {
            "categories": {
                "runtime": {"status": "PASS", "failed": 0, "timeout": 0},
                "test": {"status": "PASS", "failed": 0, "timeout": 0},
            }
        },
    )

    assert rendered.endswith("verified=2/2 all_pass=true")


def test_format_review_batch_coverage_marks_missing_category():
    script = load_script()

    rendered = script.format_review_batch_coverage(
        {"batches": ["runtime", "test"]},
        {"categories": {"runtime": {"status": "PASS", "failed": 0, "timeout": 0}}},
    )

    assert rendered == "verified=1/2 all_pass=false"


def test_format_review_batch_coverage_marks_stale_category():
    script = load_script()

    rendered = script.format_review_batch_coverage(
        {"batches": ["runtime", "test"]},
        {
            "categories": {
                "runtime": {"status": "PASS", "failed": 0, "timeout": 0, "fresh": True},
                "test": {"status": "PASS", "failed": 0, "timeout": 0, "fresh": False},
            }
        },
    )

    assert rendered == "verified=1/2 all_pass=false fresh=false stale=test"


def test_format_review_batch_run_includes_counts():
    script = load_script()

    rendered = script.format_review_batch_run({
        "file": "review_batch_runner_20260601_175453.json",
        "status": "PASS",
        "mode": "run",
        "category": "runtime",
        "commands": 2,
        "passed": 2,
        "failed": 0,
        "timeout": 0,
        "planned": 0,
    })

    assert rendered == (
        "review_batch_runner_20260601_175453.json:PASS"
        "(mode=run,category=runtime,commands=2,pass=2,fail=0,timeout=0,planned=0)"
    )


def test_format_review_batch_runs_includes_category_ledger():
    script = load_script()

    rendered = script.format_review_batch_runs({
        "order": ["runtime", "test"],
        "categories": {
            "runtime": {"status": "PASS", "commands": 2, "passed": 2, "failed": 0, "timeout": 0},
            "test": {"status": "PASS", "commands": 1, "passed": 1, "failed": 0, "timeout": 0},
        },
    })

    assert rendered == "runtime:PASS(2/2,fail=0,timeout=0),test:PASS(1/1,fail=0,timeout=0)"


def test_format_review_batch_runs_includes_freshness_when_available():
    script = load_script()

    rendered = script.format_review_batch_runs({
        "order": ["runtime", "test"],
        "categories": {
            "runtime": {
                "status": "PASS",
                "commands": 2,
                "passed": 2,
                "failed": 0,
                "timeout": 0,
                "fresh": True,
            },
            "test": {
                "status": "PASS",
                "commands": 1,
                "passed": 1,
                "failed": 0,
                "timeout": 0,
                "fresh": False,
            },
        },
    })

    assert rendered == (
        "runtime:PASS(2/2,fail=0,timeout=0,fresh=true),"
        "test:PASS(1/1,fail=0,timeout=0,fresh=false)"
    )


def test_format_file_activity_counts_created_deleted_modified():
    script = load_script()

    rendered = script.format_file_activity({"diff": {"created": 1, "deleted": 2, "modified": 3}})

    assert rendered == "created=1,deleted=2,modified=3"


def test_format_tool_surface_counts_drift():
    script = load_script()

    rendered = script.format_tool_surface({
        "status": "WARN",
        "live_count": 91,
        "manifest_count": 90,
        "extra_live": ["stale_tool"],
        "missing_live": [],
    })

    assert rendered == "WARN(live=91,manifest=90,extra=1,missing=0)"


def test_format_identity_surface_counts_violations():
    script = load_script()

    rendered = script.format_identity_surface({
        "status": "FAIL",
        "files_checked": 10,
        "violations": 1,
        "missing_required": 0,
    })

    assert rendered == "FAIL(files=10,violations=1,missing=0)"


def test_format_live_behavior_counts_checks():
    script = load_script()

    rendered = script.format_live_behavior({
        "status": "WARN",
        "checks": {
            "one": True,
            "two": False,
        },
    })

    assert rendered == "WARN(checks=1/2)"


def test_format_memory_hygiene_shows_archive_readiness():
    script = load_script()

    rendered = script.format_memory_hygiene({
        "archive_candidates": 12,
        "archive_readiness": {"status": "PASS", "total_moves": 12},
    })

    assert rendered == "archive_candidates=12,date_basis=utc,readiness=PASS,moves=12"


def test_format_memory_hygiene_marks_stale_archive_plan():
    script = load_script()

    rendered = script.format_memory_hygiene({
        "archive_candidates": 12,
        "archive_readiness": {"status": "PASS", "total_moves": 10},
    })

    assert rendered == "archive_candidates=12,date_basis=utc,readiness=STALE,moves=10,delta=+2"


def test_context_map_entry_marks_stale_against_active_source(tmp_path):
    script = load_script()
    index = tmp_path / "index.json"
    index.write_text(json.dumps({
        "updated_at": "2026-06-01T23:17:45Z",
        "files": {"ANA_MAX/tools/example.py": {}},
    }), encoding="utf-8")
    active_source = {
        "available": True,
        "latest_mtime": index.stat().st_mtime + 30,
        "latest_path": "ANA_MAX/tools/example.py",
    }

    data = script.context_map_entry("code", index, active_source)

    assert data["status"] == "STALE"
    assert data["summaries"] == 1
    assert data["stale_source"] == "ANA_MAX/tools/example.py"


def test_context_map_entry_marks_graph_stale_when_code_map_is_newer(tmp_path):
    script = load_script()
    graph = tmp_path / "graph.json"
    graph.write_text(json.dumps({
        "updated_at": "2026-06-01T23:17:55Z",
        "stats": {"nodes": 3, "edges": 4},
    }), encoding="utf-8")

    data = script.context_map_entry(
        "graph",
        graph,
        {"available": True, "latest_mtime": 0, "latest_path": ""},
        required_mtime=graph.stat().st_mtime + 30,
        required_label="code_map",
    )

    assert data["status"] == "STALE"
    assert data["nodes"] == 3
    assert data["edges"] == 4
    assert data["stale_source"] == "code_map"


def test_format_context_maps_shows_counts_and_stale_source():
    script = load_script()

    rendered = script.format_context_maps({
        "code_map": {"status": "PASS", "summaries": 956},
        "graph_map": {
            "status": "STALE",
            "nodes": 10335,
            "edges": 27883,
            "stale_source": "ANA_MAX/dev_artifacts/scripts/ana_operator_status.py",
        },
    })

    assert rendered == (
        "code:PASS(956) graph:STALE(10335n/27883e,"
        "stale=graph=.../dev_artifacts/scripts/ana_operator_status.py)"
    )
