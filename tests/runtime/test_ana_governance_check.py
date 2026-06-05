"""Tests for ANA governance checker."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import json
import os


ROOT = Path(__file__).resolve().parents[2]
ANA_MAX_DIR = ROOT / "ANA_MAX"
if str(ANA_MAX_DIR) not in sys.path:
    sys.path.insert(0, str(ANA_MAX_DIR))
SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "ana_governance_check.py"
COVERAGE_SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "ana_permission_manifest_coverage.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("ana_governance_check", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_coverage_checker():
    spec = importlib.util.spec_from_file_location("ana_permission_manifest_coverage", COVERAGE_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_governance_docs_pass():
    checker = load_checker()

    report = checker.check_docs()

    assert report["status"] == "PASS"
    assert report["summary"]["fail"] == 0
    assert report["profile_summary"]["tools_total"] > 0
    assert report["profile_summary"]["profile_counts"]["core"] > 0
    assert report["profile_summary"]["profile_counts"]["security_lab"] > 0
    names = {item["name"] for item in report["checks"]}
    assert "doc_exists:docs/ANA_SERIOUS_PROJECT_RULES.md" in names
    assert "doc_exists:docs/ANA_EXAMPLES_INDEX.md" in names
    assert "doc_exists:docs/templates/BUG_REPORT_TEMPLATE.md" in names
    assert "doc_exists:docs/examples/BUG_REPORT_EXAMPLE_ANA_AUTONOMY_WARN.md" in names
    assert "doc_exists:docs/examples/AUTONOMY_RUNNER_WARN_FOLLOWUP_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/AUTONOMY_RUNNER_PASS_CONTRACT_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/AUTONOMY_RUNNER_CHECKPOINT_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/NUCLEUS_SMOKE_SUMMARY_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/MCP_TOOLS_LIST_COVERAGE_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/MCP_TOOLS_CALL_FAILURE_NORMALIZATION_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/MCP_SCHEMA_LOOKUP_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/LIVE_MCP_RELOAD_VERIFICATION_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/RELOAD_READINESS_PREFLIGHT_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/RELOAD_CONSISTENCY_CHECK_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/LAB_QUALITY_GATE_SUMMARY_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/NO_RELOAD_QUALITY_GATE_SUMMARY_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/LAB_STATE_SUMMARY_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/LINUX_READINESS_SUMMARY_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/PERMISSION_MANIFEST_COVERAGE_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/PERMISSION_MANIFEST_RELOAD_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/PERMISSION_BLOCKED_ACTION_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/PERMISSION_INACTIVE_PROFILE_BLOCK_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/GOVERNANCE_CHECK_SUMMARY_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/TOOL_ROUTER_RECOMMENDATION_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/AGENT_COACH_RECOMMENDATION_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/ERROR_RADAR_FINDING_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/REVIEW_BATCH_RUNNER_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/CODE_CONTEXT_PACK_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/GRAPH_CONTEXT_PACK_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/CODE_MAP_QUERY_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/CODE_MAP_INCREMENTAL_REFRESH_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/GRAPH_MAP_QUERY_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/GRAPH_MAP_REFRESH_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/CODE_GRAPH_STALE_MAP_HANDLING_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/SESSION_AUDIT_TRUST_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/SESSION_CHECKPOINT_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/SESSION_REM_SLEEP_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/SESSION_LIFECYCLE_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/MEMORY_HYGIENE_REPORT_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/MEMORY_ARCHIVE_DRY_RUN_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/BINARY_MAP_STATIC_ANALYSIS_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/INPUT_API_PROBE_SPEC_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/RUNTIME_DEEP_ROUTER_ESCALATION_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/TOOL_HEALTHCHECK_SUMMARY_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/TOOL_PROFILE_SUMMARY_EXAMPLE.md" in names
    assert "doc_exists:docs/examples/DASHBOARD_LOCAL_HTML_EXAMPLE.md" in names
    assert "doc_exists:ANA_MAX/memory/tool_profiles/TOOL_PROFILE_REPORT.md" in names
    assert "profile_term:`security_lab`" in names
    assert "identity_rule:codex-first" in names
    assert "identity_rule:ana-for-codex" in names
    assert "identity_rule:neutral about external tools" in names
    assert "identity_rule:evidence over branding" in names
    assert "permission_manifest:all_tools_profiled" in names
    assert "permission_manifest:all_tool_profiles_valid" in names
    assert "tool_profile:input_api_probe:security_lab" in names
    assert "tool_requires_confirmation:desktop_control" in names


def test_permission_manifest_profiles_can_block_inactive_profile(tmp_path: Path, monkeypatch):
    from tools import base
    from tools.base import Tool, ToolDefinition, ToolResult, ToolStatus

    class DemoTool(Tool):
        def get_definition(self) -> ToolDefinition:
            return ToolDefinition(name="demo_probe", description="demo")

        def execute(self, **kwargs):
            return ToolResult(status=ToolStatus.SUCCESS, data={"ok": True})

    manifest = tmp_path / "permission_manifest.json"
    manifest.write_text(
        json.dumps(
            {
            "global_settings": {"active_profiles": ["core"]},
            "tools": {
                "demo_probe": {
                    "profile": "security_lab",
                    "readonly": True,
                    "requires_confirmation": False,
                    "allowed": True,
                }
            },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("ANA_PERMISSION_MANIFEST", str(manifest))
    monkeypatch.setattr(base, "_manifest", None)
    monkeypatch.setattr(base, "_manifest_mtime", None)
    monkeypatch.setattr(base, "_manifest_source", None)

    result = DemoTool().safe_execute()

    assert result.status == ToolStatus.BLOCKED
    assert "inactive profile" in result.error


def test_permission_manifest_reloads_when_file_changes(tmp_path: Path, monkeypatch):
    from tools import base

    manifest = tmp_path / "permission_manifest.json"
    manifest.write_text(
        json.dumps({"global_settings": {"active_profiles": ["core"]}, "tools": {}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("ANA_PERMISSION_MANIFEST", str(manifest))
    monkeypatch.setattr(base, "_manifest", None)
    monkeypatch.setattr(base, "_manifest_mtime", None)
    monkeypatch.setattr(base, "_manifest_source", None)

    first = base._load_permission_manifest()
    assert first["global_settings"]["active_profiles"] == ["core"]

    manifest.write_text(
        json.dumps({"global_settings": {"active_profiles": ["windows"]}, "tools": {}}),
        encoding="utf-8",
    )
    os.utime(manifest, (2_000_000_000, 2_000_000_000))

    second = base._load_permission_manifest()

    assert second["global_settings"]["active_profiles"] == ["windows"]


def test_permission_manifest_coverage_compare_detects_drift():
    checker = load_coverage_checker()

    report = checker.compare_tool_sets(
        runtime_tools={"tool_router", "agent_coach"},
        manifest_tools={"tool_router", "stale_tool"},
    )

    assert report["status"] == "FAIL"
    assert report["missing_in_manifest"] == ["agent_coach"]
    assert report["extra_in_manifest"] == ["stale_tool"]
