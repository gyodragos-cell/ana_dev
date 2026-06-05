"""Run the no-reload ANA MAX quality gate.

This validates the current MCP/tool-routing milestone without installing VSIX
files or reloading IDEs.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
ANA_ROOT = REPO_ROOT / "ANA_MAX"
REPORT_DIR = ANA_ROOT / "dev_artifacts" / "reports"


@dataclass
class Step:
    name: str
    command: list[str]
    timeout: int


def run_step(step: Step) -> dict:
    started = time.perf_counter()
    try:
        result = subprocess.run(
            step.command,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=step.timeout,
        )
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return {
            "name": step.name,
            "status": "pass" if result.returncode == 0 else "fail",
            "returncode": result.returncode,
            "elapsed_ms": elapsed_ms,
            "command": step.command,
            "stdout_tail": tail(result.stdout),
            "stderr_tail": tail(result.stderr),
        }
    except subprocess.TimeoutExpired as exc:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return {
            "name": step.name,
            "status": "timeout",
            "returncode": None,
            "elapsed_ms": elapsed_ms,
            "command": step.command,
            "stdout_tail": tail(exc.stdout or ""),
            "stderr_tail": tail(exc.stderr or ""),
        }


def run_advisory(step: Step) -> dict:
    result = run_step(step)
    if result["status"] == "pass":
        result["status"] = "ok"
    elif result["status"] == "fail":
        result["status"] = "warn"
    return result


def tail(text: str, max_chars: int = 4000) -> str:
    text = str(text or "").strip()
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]


def main() -> int:
    python = sys.executable
    steps = [
        Step(
            "compile_core_routing",
            [
                python,
                "-m",
                "compileall",
                "-q",
                "ANA_MAX/tools/base.py",
                "ANA_MAX/tools/agent_coach_tool.py",
                "ANA_MAX/tools/session_rem_sleep_tool.py",
                "ANA_MAX/tools/tool_router_tool.py",
                "ANA_MAX/core/agent_trace_schema.py",
                "ANA_MAX/main.py",
                "ANA_MAX/mcp_stdio.py",
                "ANA_MAX_Launcher/mcp_readiness_check.py",
                "ANA_MAX/dev_artifacts/scripts/package_cockpit_vsix.py",
                "ANA_MAX/dev_artifacts/scripts/ana_permission_manifest_coverage.py",
                "ANA_MAX/dev_artifacts/scripts/ana_local_checkpoint.py",
                "ANA_MAX/dev_artifacts/scripts/ana_operator_status.py",
                "ANA_MAX/dev_artifacts/scripts/ana_lab_state_summary.py",
                "ANA_MAX/dev_artifacts/scripts/ana_post_reload_verify.py",
                "ANA_MAX/dev_artifacts/scripts/ana_vsix_version_check.py",
                "ANA_MAX/dev_artifacts/scripts/ana_patch_advisor.py",
                "ANA_MAX/dev_artifacts/scripts/ana_graph_map.py",
                "ANA_MAX/dev_artifacts/scripts/ana_trace_report.py",
                "ANA_MAX/dev_artifacts/scripts/ana_file_activity_snapshot.py",
                "ANA_MAX/dev_artifacts/scripts/ana_dirty_tree_report.py",
                "ANA_MAX/dev_artifacts/scripts/ana_review_batch_runner.py",
                "ANA_MAX/dev_artifacts/scripts/ana_memory_archive.py",
                "ANA_MAX/dev_artifacts/scripts/ana_live_tool_surface_check.py",
                "ANA_MAX/dev_artifacts/scripts/ana_live_behavior_check.py",
                "ANA_MAX/dev_artifacts/scripts/ana_reload_consistency_check.py",
                "ANA_MAX/dev_artifacts/scripts/ana_identity_surface_check.py",
                "ANA_MAX/dev_artifacts/scripts/ana_nucleus_smoke.py",
            ],
            60,
        ),
        Step(
            "pytest_routing_guidance",
            [
                python,
                "-m",
                "pytest",
                "tests/runtime/test_tool_router_tool.py",
                "tests/runtime/test_agent_coach_recommend.py",
                "tests/runtime/test_session_rem_sleep_tool.py",
                "tests/runtime/test_ana_governance_check.py",
                "tests/runtime/test_ana_local_checkpoint.py",
                "tests/runtime/test_ana_operator_status.py",
                "tests/runtime/test_ana_lab_state_summary.py",
                "tests/runtime/test_ana_post_reload_verify.py",
                "tests/runtime/test_ana_vsix_version_check.py",
                "tests/runtime/test_ana_patch_advisor.py",
                "tests/runtime/test_agent_trace_schema.py",
                "tests/runtime/test_ana_graph_map.py",
                "tests/runtime/test_ana_trace_report.py",
                "tests/runtime/test_ana_file_activity_snapshot.py",
                "tests/runtime/test_ana_dirty_tree_report.py",
                "tests/runtime/test_ana_review_batch_runner.py",
                "tests/runtime/test_ana_memory_archive.py",
                "tests/runtime/test_ana_memory_hygiene.py",
                "tests/runtime/test_ana_live_tool_surface_check.py",
                "tests/runtime/test_ana_live_behavior_check.py",
                "tests/runtime/test_ana_reload_consistency_check.py",
                "tests/runtime/test_ana_identity_surface_check.py",
                "tests/runtime/test_ana_nucleus_smoke.py",
                "tests/runtime/test_session_checkpoint_tool.py",
                "tests/runtime/test_vscode_extension.py",
                "-q",
            ],
            120,
        ),
        Step(
            "permission_manifest_coverage",
            [
                python,
                "ANA_MAX/dev_artifacts/scripts/ana_permission_manifest_coverage.py",
                "--no-write",
            ],
            120,
        ),
        Step(
            "identity_surface_check",
            [
                python,
                "ANA_MAX/dev_artifacts/scripts/ana_identity_surface_check.py",
                "--no-write",
            ],
            60,
        ),
        Step(
            "mcp_smart_readiness",
            [
                python,
                "ANA_MAX_Launcher/mcp_readiness_check.py",
                "--mcp-url",
                "http://127.0.0.1:8766/mcp",
            ],
            90,
        ),
        Step(
            "mcp_all_tools_smoke",
            [
                python,
                "ANA_MAX/dev_artifacts/tests/smoke_mcp_all_tools.py",
            ],
            300,
        ),
        Step(
            "vsix_version_consistency",
            [
                python,
                "ANA_MAX/dev_artifacts/scripts/ana_vsix_version_check.py",
            ],
            60,
        ),
        Step(
            "package_cockpit_vsix_no_install",
            [
                python,
                "ANA_MAX/dev_artifacts/scripts/package_cockpit_vsix.py",
            ],
            90,
        ),
    ]
    advisories = [
        Step(
            "live_reload_marker",
            [
                python,
                "ANA_MAX/dev_artifacts/scripts/ana_live_reload_check.py",
                "--no-write",
            ],
            60,
        ),
        Step(
            "live_tool_surface",
            [
                python,
                "ANA_MAX/dev_artifacts/scripts/ana_live_tool_surface_check.py",
            ],
            60,
        ),
        Step(
            "live_behavior",
            [
                python,
                "ANA_MAX/dev_artifacts/scripts/ana_live_behavior_check.py",
            ],
            60,
        ),
    ]

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    results = [run_step(step) for step in steps]
    advisory_results = [run_advisory(step) for step in advisories]
    summary: dict[str, int] = {}
    for result in results:
        summary[result["status"]] = summary.get(result["status"], 0) + 1
    advisory_summary: dict[str, int] = {}
    for result in advisory_results:
        advisory_summary[result["status"]] = advisory_summary.get(result["status"], 0) + 1

    report = {
        "schema": "ana.no_reload_quality_gate.v1",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary": dict(sorted(summary.items())),
        "advisory_summary": dict(sorted(advisory_summary.items())),
        "results": results,
        "advisories": advisory_results,
    }
    report_path = REPORT_DIR / f"no_reload_quality_gate_{time.strftime('%Y%m%d_%H%M%S')}.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")

    print(json.dumps({"summary": report["summary"], "report": str(report_path)}, indent=2))
    for result in advisory_results:
        if result["status"] != "ok":
            print(f"ADVISORY {result['name']}")
            if result.get("stdout_tail"):
                print(result["stdout_tail"])
    for result in results:
        status = result["status"]
        if status != "pass":
            print(f"{status.upper():7} {result['name']}")
            if result.get("stderr_tail"):
                print(result["stderr_tail"])
            elif result.get("stdout_tail"):
                print(result["stdout_tail"])

    return 0 if all(result["status"] == "pass" for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
