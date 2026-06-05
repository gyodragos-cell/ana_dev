"""Verify ANA MCP after an operator reload/restart.

This script is intentionally read-only. It does not stop, kill, restart, or
reload anything. It only checks whether the already-running MCP server loaded
the latest marker, then runs the nucleus smoke and compact lab state summary.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any


DEFAULT_MCP_URL = "http://127.0.0.1:8766/mcp"
REPO_ROOT = Path(__file__).resolve().parents[3]
ANA_ROOT = REPO_ROOT / "ANA_MAX"
REPORT_DIR = ANA_ROOT / "dev_artifacts" / "reports"
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import ana_lab_state_summary
import ana_live_behavior_check
import ana_live_reload_check
import ana_nucleus_smoke
import ana_operator_status


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def status_from_parts(
    live_reload: dict[str, Any],
    nucleus: dict[str, Any],
    lab_state: dict[str, Any],
    tool_surface: dict[str, Any] | None = None,
    identity_surface: dict[str, Any] | None = None,
    live_behavior: dict[str, Any] | None = None,
) -> str:
    if nucleus.get("status") == "FAIL":
        return "FAIL"
    if live_reload.get("status") != "PASS":
        return "WARN"
    if tool_surface and tool_surface.get("status") == "WARN":
        return "WARN"
    if identity_surface and identity_surface.get("status") != "PASS":
        return "WARN"
    if live_behavior and live_behavior.get("status") == "WARN":
        return "WARN"
    if nucleus.get("status") == "WARN":
        return "WARN"
    if lab_state.get("mcp", {}).get("mcp_ready") is not True:
        return "FAIL"
    return "PASS"


def build_next_action(report: dict[str, Any]) -> str:
    if report["status"] == "FAIL":
        return "Fix failed MCP/Nucleus checks before continuing."
    if report["live_reload"].get("status") != "PASS":
        return "Reload/restart ANA MCP server, then rerun post-reload verify."
    if report.get("tool_surface", {}).get("status") == "WARN":
        return "Restart ANA MCP so live tools/list matches the local permission manifest, then rerun post-reload verify."
    if report.get("identity_surface", {}).get("status") != "PASS":
        return "Fix active identity surface, then rerun post-reload verify."
    if report.get("live_behavior", {}).get("status") == "WARN":
        return "Restart ANA MCP, then run Live Behavior, Reload Consistency, and Post-Reload Verify."
    if report["nucleus"].get("status") == "WARN":
        return "Review Nucleus warnings, then run one scoped action."
    return "Continue with Autonomy Pass or one scoped lab action."


def build_report(mcp_url: str = DEFAULT_MCP_URL, timeout: int = 30) -> dict[str, Any]:
    live_reload = ana_live_reload_check.check_live_reload(mcp_url, timeout=min(timeout, 20))
    nucleus = ana_nucleus_smoke.run_smoke(mcp_url, timeout=timeout)
    lab_state = ana_lab_state_summary.build_summary(mcp_url)
    tool_surface = ana_operator_status.live_tool_surface(mcp_url)
    identity_surface = lab_state.get("identity_surface") or {}
    live_behavior = ana_live_behavior_check.build_report(mcp_url, timeout=timeout)
    report = {
        "schema": "ana.post_reload_verify.v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "mcp_url": mcp_url,
        "live_reload": {
            "status": live_reload.get("status"),
            "marker": live_reload.get("marker"),
            "has_marker": live_reload.get("has_marker"),
            "next_action": live_reload.get("next_action"),
        },
        "nucleus": {
            "status": nucleus.get("status"),
            "summary": nucleus.get("summary"),
        },
        "tool_surface": tool_surface,
        "identity_surface": identity_surface,
        "live_behavior": live_behavior,
        "lab_state": {
            "mcp": lab_state.get("mcp"),
            "live_reload": lab_state.get("live_reload"),
            "memory_hygiene": lab_state.get("memory_hygiene"),
            "git": {
                "changed_paths": lab_state.get("git", {}).get("changed_paths"),
                "tracked": lab_state.get("git", {}).get("tracked"),
                "untracked": lab_state.get("git", {}).get("untracked"),
            },
        },
        "safety": "Read-only post-reload verification. No process or file mutation except optional report writing.",
    }
    report["status"] = status_from_parts(
        live_reload,
        nucleus,
        lab_state,
        tool_surface,
        identity_surface,
        live_behavior,
    )
    report["next_action"] = build_next_action(report)
    return report


def write_report(report: dict[str, Any]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"post_reload_verify_{stamp}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def print_human(report: dict[str, Any], report_path: Path | None = None) -> None:
    nucleus_summary = report["nucleus"].get("summary") or {}
    print(
        "ANA Post Reload: "
        f"{report['status']} "
        f"marker={report['live_reload'].get('has_marker')} "
        f"tool_surface={ana_operator_status.format_tool_surface(report.get('tool_surface') or {})} "
        f"identity={ana_operator_status.format_identity_surface(report.get('identity_surface') or {})} "
        f"behavior={report.get('live_behavior', {}).get('status')} "
        f"nucleus={report['nucleus'].get('status')} "
        f"({nucleus_summary.get('pass', 0)} pass / "
        f"{nucleus_summary.get('warn', 0)} warn / "
        f"{nucleus_summary.get('fail', 0)} fail)"
    )
    print(f"next_action={report['next_action']}")
    if report_path:
        print(f"report={report_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify ANA MCP after operator reload/restart.")
    parser.add_argument("--mcp-url", default=DEFAULT_MCP_URL)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-write", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_report(args.mcp_url, timeout=args.timeout)
    path = None if args.no_write else write_report(report)
    if args.json:
        print(json.dumps({**report, "report": str(path) if path else None}, indent=2, ensure_ascii=False))
    else:
        print_human(report, path)
    return 0 if report["status"] in {"PASS", "WARN"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
