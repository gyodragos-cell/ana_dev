"""ANA MAX lab quality gate.

Focused, developer-friendly gate for mother-lab work. It avoids public sync and
checks only local runtime/extension health.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
REPORT_DIR = REPO_ROOT / "ANA_MAX" / "dev_artifacts" / "reports"


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def run_step(name: str, command: list[str], timeout: int = 120) -> dict[str, Any]:
    started = datetime.now(timezone.utc)
    try:
        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        ok = result.returncode == 0
        return {
            "name": name,
            "ok": ok,
            "returncode": result.returncode,
            "command": command,
            "stdout_tail": tail(result.stdout),
            "stderr_tail": tail(result.stderr),
            "seconds": round((datetime.now(timezone.utc) - started).total_seconds(), 3),
        }
    except Exception as exc:
        return {
            "name": name,
            "ok": False,
            "command": command,
            "error": str(exc),
            "seconds": round((datetime.now(timezone.utc) - started).total_seconds(), 3),
        }


def tail(text: str, limit: int = 3000) -> str:
    text = (text or "").strip()
    return text[-limit:]


def write_report(report: dict[str, Any]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"lab_quality_gate_{stamp}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def main() -> int:
    python = sys.executable
    steps = [
        (
            "compile_core_tools_scripts",
            [
                python,
                "-m",
                "compileall",
                "-q",
                "ANA_MAX/main.py",
                "ANA_MAX/tools",
                "ANA_MAX/dev_artifacts/scripts/ana_nucleus_smoke.py",
                "ANA_MAX/dev_artifacts/scripts/ana_autonomy_runner.py",
                "ANA_MAX/dev_artifacts/scripts/ana_linux_readiness.py",
                "ANA_MAX/dev_artifacts/scripts/ana_governance_check.py",
                "ANA_MAX/dev_artifacts/scripts/ana_tool_profile_report.py",
                "ANA_MAX/dev_artifacts/scripts/ana_graph_map.py",
                "ANA_MAX/dev_artifacts/scripts/ana_code_map.py",
                "ANA_MAX/dev_artifacts/scripts/ana_local_checkpoint.py",
                "ANA_MAX/dev_artifacts/scripts/ana_operator_status.py",
                "ANA_MAX/dev_artifacts/scripts/ana_lab_state_summary.py",
                "ANA_MAX/dev_artifacts/scripts/ana_post_reload_verify.py",
                "ANA_MAX/dev_artifacts/scripts/ana_trace_report.py",
                "ANA_MAX/dev_artifacts/scripts/ana_file_activity_snapshot.py",
                "ANA_MAX/dev_artifacts/scripts/ana_dirty_tree_report.py",
                "ANA_MAX/dev_artifacts/scripts/ana_memory_archive.py",
                "ANA_MAX/dev_artifacts/scripts/ana_live_behavior_check.py",
                "ANA_MAX/dev_artifacts/scripts/ana_reload_consistency_check.py",
                "ANA_MAX/dev_artifacts/scripts/ana_identity_surface_check.py",
                "ANA_MAX/dev_artifacts/scripts/ana_vsix_version_check.py",
            ],
            120,
        ),
        (
            "pytest_focused_runtime",
            [
                python,
                "-m",
                "pytest",
                "tests/runtime/test_vscode_extension.py",
                "tests/runtime/test_ana_graph_map.py",
                "tests/runtime/test_graph_context_pack_tool.py",
                "tests/runtime/test_code_context_pack_tool.py",
                "tests/runtime/test_tool_router_tool.py",
                "tests/runtime/test_session_audit_tool.py",
                "tests/runtime/test_error_radar_tool.py",
                "tests/runtime/test_ana_autonomy_runner.py",
                "tests/runtime/test_ana_linux_readiness.py",
                "tests/runtime/test_ana_governance_check.py",
                "tests/runtime/test_ana_tool_profile_report.py",
                "tests/runtime/test_ana_local_checkpoint.py",
                "tests/runtime/test_ana_operator_status.py",
                "tests/runtime/test_ana_lab_state_summary.py",
                "tests/runtime/test_ana_post_reload_verify.py",
                "tests/runtime/test_ana_trace_report.py",
                "tests/runtime/test_ana_file_activity_snapshot.py",
                "tests/runtime/test_ana_dirty_tree_report.py",
                "tests/runtime/test_ana_memory_archive.py",
                "tests/runtime/test_ana_memory_hygiene.py",
                "tests/runtime/test_ana_live_behavior_check.py",
                "tests/runtime/test_ana_reload_consistency_check.py",
                "tests/runtime/test_ana_identity_surface_check.py",
                "tests/runtime/test_ana_vsix_version_check.py",
                "tests/runtime/test_ana_nucleus_smoke.py",
                "tests/runtime/test_session_checkpoint_tool.py",
                "-q",
            ],
            180,
        ),
        (
            "governance_check",
            [python, "ANA_MAX/dev_artifacts/scripts/ana_governance_check.py"],
            60,
        ),
        (
            "permission_manifest_coverage",
            [python, "ANA_MAX/dev_artifacts/scripts/ana_permission_manifest_coverage.py"],
            120,
        ),
        ("extension_js_syntax", ["node", "--check", "vscode_extension/extension.js"], 60),
        ("vsix_version_consistency", [python, "ANA_MAX/dev_artifacts/scripts/ana_vsix_version_check.py"], 60),
        ("identity_surface_check", [python, "ANA_MAX/dev_artifacts/scripts/ana_identity_surface_check.py", "--no-write"], 60),
        ("trace_report", [python, "ANA_MAX/dev_artifacts/scripts/ana_trace_report.py"], 60),
        ("mcp_health", [python, "ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py", "--health"], 60),
        (
            "nucleus_smoke",
            [
                python,
                "ANA_MAX/dev_artifacts/scripts/ana_nucleus_smoke.py",
                "--mcp-url",
                "http://127.0.0.1:8766/mcp",
            ],
            180,
        ),
    ]

    results = []
    for name, command, timeout in steps:
        print(f"[RUN] {name}")
        result = run_step(name, command, timeout=timeout)
        results.append(result)
        print(f"[{'PASS' if result['ok'] else 'FAIL'}] {name} {result.get('seconds')}s")

    report = {
        "schema": "ana.lab_quality_gate.v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": "PASS" if all(item["ok"] for item in results) else "FAIL",
        "results": results,
    }
    path = write_report(report)
    print(f"ANA Lab Quality Gate: {report['status']}")
    print(f"report={path}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
