"""Read-only preflight for ANA MCP reload/restart decisions."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import subprocess
import sys
from typing import Any
import urllib.request

import ana_live_behavior_check
import ana_live_reload_check
import ana_operator_status


DEFAULT_MCP_URL = "http://127.0.0.1:8766/mcp"
REPO_ROOT = Path(__file__).resolve().parents[3]
ANA_ROOT = REPO_ROOT / "ANA_MAX"
REPORT_DIR = ANA_ROOT / "dev_artifacts" / "reports"


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def health_url(mcp_url: str) -> str:
    return mcp_url.rstrip("/").removesuffix("/mcp") + "/health"


def get_json(url: str, timeout: int = 10) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def run(command: list[str], timeout: int = 10) -> dict[str, Any]:
    try:
        result = subprocess.run(
            command,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return {
            "ok": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "command": command,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc), "command": command}


def port_owner(port: int = 8766) -> dict[str, Any]:
    if platform.system().lower().startswith("win"):
        return run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                f"Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | "
                "Select-Object LocalAddress,LocalPort,State,OwningProcess | ConvertTo-Json -Depth 4",
            ],
            timeout=15,
        )
    shell = (
        f"(command -v ss >/dev/null && ss -ltnp 'sport = :{port}') || "
        f"(command -v lsof >/dev/null && lsof -iTCP:{port} -sTCP:LISTEN -n -P)"
    )
    return run(["bash", "-lc", shell], timeout=15)


def python_processes() -> dict[str, Any]:
    if platform.system().lower().startswith("win"):
        return run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-CimInstance Win32_Process -Filter \"name = 'python.exe'\" | "
                "Select-Object ProcessId,CommandLine | ConvertTo-Json -Depth 4",
            ],
            timeout=15,
        )
    return run(["bash", "-lc", "ps -eo pid,args | grep -E 'python|ANA_MAX' | grep -v grep"], timeout=15)


def build_report(mcp_url: str = DEFAULT_MCP_URL) -> dict[str, Any]:
    try:
        health = get_json(health_url(mcp_url), timeout=10)
    except Exception as exc:
        health = {"status": "error", "error": str(exc)}
    live_reload = ana_live_reload_check.check_live_reload(mcp_url, timeout=20)
    tool_surface = ana_operator_status.live_tool_surface(mcp_url)
    live_behavior = ana_live_behavior_check.build_report(mcp_url, timeout=20)
    reload_reasons = []
    if not bool(live_reload.get("has_marker")):
        reload_reasons.append("missing_reload_marker")
    if tool_surface.get("status") == "WARN":
        reload_reasons.append("live_tool_surface_drift")
    if live_behavior.get("status") == "WARN":
        reload_reasons.append("live_behavior_stale")
    reload_needed = bool(reload_reasons)
    return {
        "schema": "ana.reload_readiness.v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "mcp_url": mcp_url,
        "mcp": {
            "status": health.get("status"),
            "mcp_ready": health.get("mcp_ready"),
            "tools_count": health.get("tools_count"),
            "version": health.get("version"),
        },
        "live_reload": {
            "status": live_reload.get("status"),
            "marker": live_reload.get("marker"),
            "has_marker": live_reload.get("has_marker"),
        },
        "tool_surface": tool_surface,
        "live_behavior": live_behavior,
        "port_8766": port_owner(8766),
        "python_processes": python_processes(),
        "reload_needed": reload_needed,
        "reload_reasons": reload_reasons,
        "safe_to_restart_guidance": build_restart_guidance(reload_reasons, health.get("mcp_ready")),
        "safety": "Read-only preflight. This script does not stop, kill, restart, or mutate processes.",
    }


def build_restart_guidance(reload_reasons: list[str], mcp_ready: bool | None) -> str:
    if not reload_reasons:
        return "Reload not required by current marker, tool-surface, or behavior checks."
    if reload_reasons == ["live_behavior_stale"] and mcp_ready:
        return "Restart ANA MCP, then run Live Behavior, Reload Consistency, and Post-Reload Verify."
    if mcp_ready:
        return "Reload/restart is useful. Use the operator's VS Code/ANA Start Server flow, then rerun Post-Reload Verify."
    return "MCP is not ready. Start ANA MCP, then rerun Reload Readiness."


def write_report(report: dict[str, Any]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"reload_readiness_{stamp}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only ANA MCP reload readiness preflight.")
    parser.add_argument("--mcp-url", default=DEFAULT_MCP_URL)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-write", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_report(args.mcp_url)
    path = None if args.no_write else write_report(report)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(
            "ANA Reload Readiness: "
            f"mcp_ready={report['mcp'].get('mcp_ready')} "
            f"reload_needed={report['reload_needed']} "
            f"marker={report['live_reload'].get('has_marker')} "
            f"tool_surface={ana_operator_status.format_tool_surface(report.get('tool_surface') or {})} "
            f"behavior={ana_operator_status.format_live_behavior(report.get('live_behavior') or {})}"
        )
        if report.get("reload_reasons"):
            print("reasons=" + ", ".join(report["reload_reasons"]))
        print(f"next_action={report['safe_to_restart_guidance']}")
        if path:
            print(f"report={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
