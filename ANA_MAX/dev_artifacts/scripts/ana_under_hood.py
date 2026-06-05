"""Collect a compact under-the-hood ANA MAX runtime report."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
ANA_ROOT = REPO_ROOT / "ANA_MAX"
DEFAULT_MCP_URL = "http://127.0.0.1:8766/mcp"


try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass


def run(command: list[str], timeout: int = 15) -> dict[str, Any]:
    started = time.perf_counter()
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
            "elapsed_ms": int((time.perf_counter() - started) * 1000),
            "stdout": tail(result.stdout),
            "stderr": tail(result.stderr),
            "command": command,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "returncode": None,
            "elapsed_ms": int((time.perf_counter() - started) * 1000),
            "stdout": tail(exc.stdout or ""),
            "stderr": tail(exc.stderr or "timeout"),
            "command": command,
        }


def tail(text: str, max_chars: int = 5000) -> str:
    text = str(text or "").strip()
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]


def read_tail(path: Path, lines: int) -> list[str]:
    if not path.exists():
        return []
    data = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return data[-lines:]


def json_request(url: str, payload: dict[str, Any] | None = None, timeout: int = 15) -> dict[str, Any]:
    data = None
    method = "GET"
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        method = "POST"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def rpc(mcp_url: str, method: str, params: dict[str, Any] | None = None, timeout: int = 20) -> dict[str, Any]:
    payload = {
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000) % 1_000_000,
        "method": method,
        "params": params or {},
    }
    return json_request(mcp_url, payload=payload, timeout=timeout)


def unwrap_tool_response(response: dict[str, Any]) -> dict[str, Any]:
    content = response.get("result", {}).get("content", [])
    if not content:
        return {"success": False, "error": response.get("error") or "missing MCP content"}
    text = str(content[0].get("text") or "")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {"success": False, "error": "non-JSON response", "text": text}
    return parsed if isinstance(parsed, dict) else {"success": False, "data": parsed}


def call_tool(mcp_url: str, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    return unwrap_tool_response(
        rpc(mcp_url, "tools/call", {"name": name, "arguments": arguments}, timeout=25)
    )


def health_url(mcp_url: str) -> str:
    return mcp_url.rstrip("/").removesuffix("/mcp") + "/health"


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect ANA MAX under-the-hood diagnostics.")
    parser.add_argument("--mcp-url", default=DEFAULT_MCP_URL)
    parser.add_argument("--lines", type=int, default=80)
    parser.add_argument("--output")
    args = parser.parse_args()

    report: dict[str, Any] = {
        "schema": "ana.under_hood.v1",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "mcp_url": args.mcp_url,
    }

    try:
        report["health"] = json_request(health_url(args.mcp_url), timeout=10)
    except Exception as exc:
        report["health_error"] = str(exc)

    try:
        tools_response = rpc(args.mcp_url, "tools/list", timeout=20)
        tools = tools_response.get("result", {}).get("tools", [])
        report["tools"] = {
            "count": len(tools),
            "names": sorted(tool.get("name") for tool in tools if isinstance(tool, dict) and tool.get("name")),
        }
    except Exception as exc:
        report["tools_error"] = str(exc)

    report["processes"] = run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-CimInstance Win32_Process -Filter \"name = 'python.exe'\" | "
            "Select-Object ProcessId,CommandLine | ConvertTo-Json -Depth 4",
        ]
    )
    report["port_8766"] = run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-NetTCPConnection -LocalPort 8766 -ErrorAction SilentlyContinue | "
            "Select-Object LocalAddress,LocalPort,State,OwningProcess | ConvertTo-Json -Depth 4",
        ]
    )
    report["git_status"] = run(["git", "status", "--short"], timeout=20)
    report["mcp_readiness"] = run(
        [
            sys.executable,
            "ANA_MAX_Launcher/mcp_readiness_check.py",
            "--mcp-url",
            args.mcp_url,
            "--expect-tool",
            "session_rem_sleep",
            "--expect-tool",
            "session_lifecycle",
        ],
        timeout=90,
    )

    report["tool_healthcheck"] = call_tool(args.mcp_url, "tool_healthcheck", {})
    report["agent_coach"] = call_tool(
        args.mcp_url,
        "agent_coach",
        {
            "action": "recommend",
            "task": "under-the-hood runtime diagnostic and stuck-session recovery",
            "max_tools": 6,
            "include_prompt": False,
        },
    )
    report["error_radar"] = call_tool(args.mcp_url, "error_radar", {"scope": "all", "limit": 10})
    report["window_snapshot"] = call_tool(args.mcp_url, "foreground_ui_snapshot", {"include_text": False, "max_elements": "8"})

    report["logs"] = {
        "ana_max_tail": read_tail(ANA_ROOT / "logs" / "ana_max.log", args.lines),
        "observability_tail": read_tail(ANA_ROOT / "logs" / "observability.jsonl", min(args.lines, 40)),
    }

    if args.output:
        output_path = Path(args.output)
    else:
        output_dir = ANA_ROOT / "dev_artifacts" / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"under_hood_{time.strftime('%Y%m%d_%H%M%S')}.json"
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    summary = {
        "health": report.get("health", {}).get("status"),
        "mcp_ready": report.get("health", {}).get("mcp_ready"),
        "tools_count": report.get("tools", {}).get("count"),
        "readiness_ok": report.get("mcp_readiness", {}).get("ok"),
        "tool_health_ok": report.get("tool_healthcheck", {}).get("success"),
        "coach_primary_tool": (
            report.get("agent_coach", {}).get("data", {}).get("primary_tool")
            if isinstance(report.get("agent_coach", {}).get("data"), dict)
            else None
        ),
        "report": str(output_path),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["mcp_ready"] and summary["readiness_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
