"""Check whether the live MCP server loaded recently changed tool behavior."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
from typing import Any
import urllib.request


DEFAULT_MCP_URL = "http://127.0.0.1:8766/mcp"
REPO_ROOT = Path(__file__).resolve().parents[3]
REPORT_DIR = REPO_ROOT / "ANA_MAX" / "dev_artifacts" / "reports"


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def json_request(url: str, payload: dict[str, Any], timeout: int = 20) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
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
    if "error" in response:
        return {"success": False, "error": response["error"], "raw_response": response}
    content = response.get("result", {}).get("content", [])
    if not content:
        return {"success": False, "error": "missing MCP content", "raw_response": response}
    text = str(content[0].get("text") or "")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {"success": False, "error": "non-JSON tool response", "text": text[:1200]}
    return parsed if isinstance(parsed, dict) else {"success": False, "error": "tool response is not an object"}


def call_tool(mcp_url: str, name: str, arguments: dict[str, Any], timeout: int = 20) -> dict[str, Any]:
    response = rpc(mcp_url, "tools/call", {"name": name, "arguments": arguments}, timeout=timeout)
    return unwrap_tool_response(response)


def check_live_reload(mcp_url: str, timeout: int = 20) -> dict[str, Any]:
    payload = call_tool(mcp_url, "graph_context_pack", {"action": "stats"}, timeout=timeout)
    data = payload.get("data") if isinstance(payload, dict) else {}
    has_stale_marker = bool(isinstance(data, dict) and "stale" in data)
    status = "PASS" if payload.get("success") and has_stale_marker else "WARN"
    next_action = (
        "Live MCP loaded updated graph_context_pack behavior."
        if status == "PASS"
        else "Restart/reload ANA MCP server, then rerun this check."
    )
    return {
        "schema": "ana.live_reload_check.v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "mcp_url": mcp_url,
        "status": status,
        "tool": "graph_context_pack",
        "marker": "data.stale",
        "has_marker": has_stale_marker,
        "tool_success": bool(payload.get("success")),
        "message": payload.get("message"),
        "next_action": next_action,
    }


def write_report(report: dict[str, Any]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"live_reload_check_{stamp}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check live MCP reload freshness markers.")
    parser.add_argument("--mcp-url", default=DEFAULT_MCP_URL)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-write", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = check_live_reload(args.mcp_url, timeout=args.timeout)
    report_path = None if args.no_write else write_report(report)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"ANA Live Reload: {report['status']} marker={report['has_marker']}")
        print(f"next_action={report['next_action']}")
        if report_path:
            print(f"report={report_path}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
