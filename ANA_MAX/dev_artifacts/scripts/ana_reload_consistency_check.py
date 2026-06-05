"""Check that ANA reload diagnostics agree on the live MCP state."""

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
import ana_operator_status
import ana_post_reload_verify
import ana_reload_readiness


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def status_from_reload_readiness(report: dict[str, Any]) -> str:
    if report.get("mcp", {}).get("mcp_ready") is not True:
        return "FAIL"
    return "WARN" if report.get("reload_needed") else "PASS"


def build_report(mcp_url: str = DEFAULT_MCP_URL, timeout: int = 30) -> dict[str, Any]:
    readiness = ana_reload_readiness.build_report(mcp_url)
    operator = ana_operator_status.build_status(mcp_url)
    lab_state = ana_lab_state_summary.build_summary(mcp_url)
    post_reload = ana_post_reload_verify.build_report(mcp_url, timeout=timeout)
    verdicts = {
        "reload_readiness": status_from_reload_readiness(readiness),
        "operator_status": str(operator.get("reload_readiness", {}).get("status") or "UNKNOWN"),
        "lab_state": str(lab_state.get("reload_readiness", {}).get("status") or "UNKNOWN"),
        "post_reload_verify": str(post_reload.get("status") or "UNKNOWN"),
    }
    statuses = set(verdicts.values())
    aligned = len(statuses) == 1
    blocking = sorted(status for status in statuses if status in {"FAIL", "UNKNOWN"})
    report = {
        "schema": "ana.reload_consistency_check.v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "mcp_url": mcp_url,
        "status": "FAIL" if blocking else ("PASS" if aligned else "WARN"),
        "aligned": aligned,
        "verdicts": verdicts,
        "signals": {
            "reload_reasons": readiness.get("reload_reasons", []),
            "operator_reasons": operator.get("reload_readiness", {}).get("reasons", []),
            "lab_state_reasons": lab_state.get("reload_readiness", {}).get("reasons", []),
            "post_reload_next_action": post_reload.get("next_action"),
            "tool_surface": ana_operator_status.format_tool_surface(readiness.get("tool_surface") or {}),
            "live_behavior": ana_operator_status.format_live_behavior(readiness.get("live_behavior") or {}),
        },
        "next_action": build_next_action(aligned, verdicts, readiness, post_reload),
        "safety": "Read-only consistency check. It does not install, reload, restart, or mutate files unless --no-write is omitted for the report.",
    }
    return report


def build_next_action(
    aligned: bool,
    verdicts: dict[str, str],
    readiness: dict[str, Any],
    post_reload: dict[str, Any],
) -> str:
    if any(value == "FAIL" for value in verdicts.values()):
        return "Fix failed reload diagnostics before continuing."
    if not aligned:
        return "Reload diagnostics disagree; inspect individual reports before action work."
    status = next(iter(verdicts.values()), "UNKNOWN")
    if status == "WARN":
        return str(readiness.get("safe_to_restart_guidance") or post_reload.get("next_action") or "Restart ANA MCP, then rerun reload diagnostics.")
    if status == "PASS":
        return "Reload diagnostics agree. Continue with Autonomy Pass or one scoped lab action."
    return "Reload diagnostic status is unknown; inspect reports before action work."


def write_report(report: dict[str, Any]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"reload_consistency_{stamp}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check ANA reload diagnostic consistency.")
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
        verdicts = report.get("verdicts", {})
        print(
            "ANA Reload Consistency: "
            f"{report['status']} "
            f"aligned={report['aligned']} "
            f"readiness={verdicts.get('reload_readiness')} "
            f"operator={verdicts.get('operator_status')} "
            f"lab_state={verdicts.get('lab_state')} "
            f"post_reload={verdicts.get('post_reload_verify')}"
        )
        print(f"next_action={report['next_action']}")
        if path:
            print(f"report={path}")
    return 0 if report["status"] in {"PASS", "WARN"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
