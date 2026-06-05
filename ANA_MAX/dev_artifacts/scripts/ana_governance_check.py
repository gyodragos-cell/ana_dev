"""Check ANA MAX governance docs for serious-project discipline."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from collections import Counter
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
REPORT_DIR = REPO_ROOT / "ANA_MAX" / "dev_artifacts" / "reports"

REQUIRED_DOCS = [
    "docs/ANA_SERIOUS_PROJECT_RULES.md",
    "docs/ANA_PROFILE_MANIFEST.md",
    "docs/ANA_EXAMPLES_AND_TESTS_CHECKLIST.md",
    "docs/ANA_EXAMPLES_INDEX.md",
    "docs/ANA_OPERATOR_RELOAD_RUNBOOK.md",
    "docs/SAFETY_BOUNDARIES.md",
    "docs/LINUX_MATE_MIGRATION_LANE.md",
    "docs/DOCS_INDEX.md",
    "docs/templates/BUG_REPORT_TEMPLATE.md",
    "docs/examples/BUG_REPORT_EXAMPLE_ANA_AUTONOMY_WARN.md",
    "docs/examples/AUTONOMY_RUNNER_WARN_FOLLOWUP_EXAMPLE.md",
    "docs/examples/AUTONOMY_RUNNER_PASS_CONTRACT_EXAMPLE.md",
    "docs/examples/AUTONOMY_RUNNER_CHECKPOINT_EXAMPLE.md",
    "docs/examples/NUCLEUS_SMOKE_SUMMARY_EXAMPLE.md",
    "docs/examples/MCP_TOOLS_LIST_COVERAGE_EXAMPLE.md",
    "docs/examples/MCP_TOOLS_CALL_FAILURE_NORMALIZATION_EXAMPLE.md",
    "docs/examples/MCP_SCHEMA_LOOKUP_EXAMPLE.md",
    "docs/examples/LIVE_MCP_RELOAD_VERIFICATION_EXAMPLE.md",
    "docs/examples/RELOAD_READINESS_PREFLIGHT_EXAMPLE.md",
    "docs/examples/RELOAD_CONSISTENCY_CHECK_EXAMPLE.md",
    "docs/examples/POST_RELOAD_VERIFY_EXAMPLE.md",
    "docs/examples/OPERATOR_STATUS_EXAMPLE.md",
    "docs/examples/VSIX_VERSION_CONSISTENCY_EXAMPLE.md",
    "docs/examples/LAB_VSIX_INSTALL_HELPER_EXAMPLE.md",
    "docs/examples/LAB_QUALITY_GATE_SUMMARY_EXAMPLE.md",
    "docs/examples/NO_RELOAD_QUALITY_GATE_SUMMARY_EXAMPLE.md",
    "docs/examples/LAB_STATE_SUMMARY_EXAMPLE.md",
    "docs/examples/LINUX_READINESS_SUMMARY_EXAMPLE.md",
    "docs/examples/PERMISSION_MANIFEST_COVERAGE_EXAMPLE.md",
    "docs/examples/PERMISSION_MANIFEST_RELOAD_EXAMPLE.md",
    "docs/examples/PERMISSION_BLOCKED_ACTION_EXAMPLE.md",
    "docs/examples/PERMISSION_INACTIVE_PROFILE_BLOCK_EXAMPLE.md",
    "docs/examples/GOVERNANCE_CHECK_SUMMARY_EXAMPLE.md",
    "docs/examples/TOOL_ROUTER_RECOMMENDATION_EXAMPLE.md",
    "docs/examples/AGENT_COACH_RECOMMENDATION_EXAMPLE.md",
    "docs/examples/ERROR_RADAR_FINDING_EXAMPLE.md",
    "docs/examples/REVIEW_BATCH_RUNNER_EXAMPLE.md",
    "docs/examples/CODE_CONTEXT_PACK_EXAMPLE.md",
    "docs/examples/GRAPH_CONTEXT_PACK_EXAMPLE.md",
    "docs/examples/CODE_MAP_QUERY_EXAMPLE.md",
    "docs/examples/CODE_MAP_INCREMENTAL_REFRESH_EXAMPLE.md",
    "docs/examples/GRAPH_MAP_QUERY_EXAMPLE.md",
    "docs/examples/GRAPH_MAP_REFRESH_EXAMPLE.md",
    "docs/examples/CODE_GRAPH_STALE_MAP_HANDLING_EXAMPLE.md",
    "docs/examples/SESSION_AUDIT_TRUST_EXAMPLE.md",
    "docs/examples/SESSION_CHECKPOINT_EXAMPLE.md",
    "docs/examples/SESSION_CHECKPOINT_PRESERVES_NOTES_EXAMPLE.md",
    "docs/examples/LOCAL_CHECKPOINT_FALLBACK_EXAMPLE.md",
    "docs/examples/SESSION_REM_SLEEP_EXAMPLE.md",
    "docs/examples/SESSION_LIFECYCLE_EXAMPLE.md",
    "docs/examples/MEMORY_HYGIENE_REPORT_EXAMPLE.md",
    "docs/examples/MEMORY_ARCHIVE_DRY_RUN_EXAMPLE.md",
    "docs/examples/BINARY_MAP_STATIC_ANALYSIS_EXAMPLE.md",
    "docs/examples/INPUT_API_PROBE_SPEC_EXAMPLE.md",
    "docs/examples/RUNTIME_DEEP_ROUTER_ESCALATION_EXAMPLE.md",
    "docs/examples/TOOL_HEALTHCHECK_SUMMARY_EXAMPLE.md",
    "docs/examples/TOOL_PROFILE_SUMMARY_EXAMPLE.md",
    "docs/examples/DASHBOARD_LOCAL_HTML_EXAMPLE.md",
    "ANA_MAX/memory/tool_profiles/TOOL_PROFILE_REPORT.md",
]

REQUIRED_PROFILE_TERMS = [
    "`core`",
    "`windows`",
    "`linux`",
    "`security_lab`",
    "`public_safe`",
    "`private_lab`",
]

VALID_PROFILES = {"core", "windows", "linux", "security_lab", "public_safe", "private_lab"}

REQUIRED_TOOL_PROFILES = {
    "tool_router": "core",
    "agent_coach": "core",
    "code_context_pack": "core",
    "graph_context_pack": "core",
    "error_radar": "core",
    "session_audit": "core",
    "desktop_capture": "windows",
    "desktop_control": "windows",
    "foreground_ui_snapshot": "windows",
    "windows_uia_bridge": "windows",
    "uia_click": "windows",
    "uia_type": "windows",
    "binary_map": "security_lab",
    "frida_instrument": "security_lab",
    "input_api_probe": "security_lab",
    "mitm_analyzer": "security_lab",
    "network_pentest": "security_lab",
}

CONFIRMATION_REQUIRED_TOOLS = {
    "desktop_control",
    "frida_instrument",
    "input_api_probe",
    "mitm_analyzer",
    "network_pentest",
    "uia_click",
    "uia_type",
    "windows_uia_bridge",
}

FORBIDDEN_PUBLIC_PROMISES = [
    "guaranteed correctness",
    "replaces developers",
    "unbeatable",
]

REQUIRED_IDENTITY_RULES = [
    "codex-first",
    "ana-for-codex",
    "neutral about external tools",
    "evidence over branding",
]


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def check_docs() -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema": "ana.governance_check.v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": "FAIL",
        "checks": [],
    }
    for rel in REQUIRED_DOCS:
        path = REPO_ROOT / rel
        report["checks"].append({
            "name": f"doc_exists:{rel}",
            "ok": path.exists(),
            "path": rel,
        })

    profile_path = REPO_ROOT / "docs" / "ANA_PROFILE_MANIFEST.md"
    profile_text = profile_path.read_text(encoding="utf-8", errors="replace") if profile_path.exists() else ""
    for term in REQUIRED_PROFILE_TERMS:
        report["checks"].append({
            "name": f"profile_term:{term}",
            "ok": term in profile_text,
            "term": term,
        })

    rules_path = REPO_ROOT / "docs" / "ANA_SERIOUS_PROJECT_RULES.md"
    rules_text = rules_path.read_text(encoding="utf-8", errors="replace").lower() if rules_path.exists() else ""
    for phrase in FORBIDDEN_PUBLIC_PROMISES:
        report["checks"].append({
            "name": f"rules_warn_against:{phrase}",
            "ok": phrase in rules_text,
            "phrase": phrase,
        })
    for phrase in REQUIRED_IDENTITY_RULES:
        report["checks"].append({
            "name": f"identity_rule:{phrase}",
            "ok": phrase in rules_text,
            "phrase": phrase,
        })

    manifest_path = REPO_ROOT / "ANA_MAX" / "config" / "permission_manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    except json.JSONDecodeError:
        manifest = {}
    global_settings = manifest.get("global_settings", {})
    tools = manifest.get("tools", {})

    active_profiles = global_settings.get("active_profiles", [])
    report["checks"].append({
        "name": "permission_manifest:active_profiles",
        "ok": isinstance(active_profiles, list) and "core" in active_profiles,
        "path": "ANA_MAX/config/permission_manifest.json",
    })

    unprofiled_tools = [
        tool_name
        for tool_name, conf in sorted(tools.items())
        if not conf.get("profile") and not conf.get("profiles")
    ]
    report["checks"].append({
        "name": "permission_manifest:all_tools_profiled",
        "ok": not unprofiled_tools,
        "missing": unprofiled_tools,
    })

    invalid_profile_tools = []
    profile_counts: Counter[str] = Counter()
    for tool_name, conf in sorted(tools.items()):
        profile = conf.get("profile")
        profiles = conf.get("profiles") or ([profile] if profile else [])
        profile_counts.update(profiles)
        if profiles and not set(profiles).issubset(VALID_PROFILES):
            invalid_profile_tools.append({"tool": tool_name, "profiles": profiles})
    report["checks"].append({
        "name": "permission_manifest:all_tool_profiles_valid",
        "ok": not invalid_profile_tools,
        "invalid": invalid_profile_tools,
    })
    report["profile_summary"] = {
        "tools_total": len(tools),
        "profile_counts": dict(sorted(profile_counts.items())),
    }

    for tool_name, expected_profile in REQUIRED_TOOL_PROFILES.items():
        conf = tools.get(tool_name, {})
        profile = conf.get("profile")
        profiles = conf.get("profiles") or ([profile] if profile else [])
        report["checks"].append({
            "name": f"tool_profile:{tool_name}:{expected_profile}",
            "ok": expected_profile in profiles,
            "tool": tool_name,
            "expected_profile": expected_profile,
        })
        report["checks"].append({
            "name": f"tool_profile_valid:{tool_name}",
            "ok": bool(profiles) and set(profiles).issubset(VALID_PROFILES),
            "tool": tool_name,
            "profiles": profiles,
        })

    for tool_name in CONFIRMATION_REQUIRED_TOOLS:
        conf = tools.get(tool_name, {})
        report["checks"].append({
            "name": f"tool_requires_confirmation:{tool_name}",
            "ok": conf.get("requires_confirmation") is True,
            "tool": tool_name,
        })

    failures = [item for item in report["checks"] if not item["ok"]]
    report["summary"] = {
        "total": len(report["checks"]),
        "pass": len(report["checks"]) - len(failures),
        "fail": len(failures),
    }
    report["status"] = "PASS" if not failures else "FAIL"
    return report


def write_report(report: dict[str, Any]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"governance_check_{stamp}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def print_human(report: dict[str, Any], report_path: Path | None = None) -> None:
    summary = report["summary"]
    print(f"ANA Governance: {report['status']} ({summary['pass']} pass / {summary['fail']} fail)")
    profile_summary = report.get("profile_summary") or {}
    if profile_summary:
        print(f"profiles={json.dumps(profile_summary, ensure_ascii=False, sort_keys=True)}")
    for check in report["checks"]:
        print(f"[{'PASS' if check['ok'] else 'FAIL'}] {check['name']}")
    if report_path:
        print(f"report={report_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check ANA governance docs.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-write", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = check_docs()
    report_path = None if args.no_write else write_report(report)
    if args.json:
        print(json.dumps({**report, "report": str(report_path) if report_path else None}, indent=2, ensure_ascii=False))
    else:
        print_human(report, report_path)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
