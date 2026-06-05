"""Safe Frida diagnostics wrapper through ANA MAX MCP."""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
ANA_ROOT = REPO_ROOT / "ANA_MAX"
DEFAULT_MCP_URL = "http://127.0.0.1:8766/mcp"
READ_ONLY_OPERATIONS = {"version", "devices", "list_processes", "list_modules", "find_functions"}
ACTIVE_OPERATIONS = {"attach", "spawn", "inject", "hook", "terminate"}


try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass


def json_request(url: str, payload: dict[str, Any] | None = None, timeout: int = 30) -> dict[str, Any]:
    data = None
    method = "GET"
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        method = "POST"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def rpc(mcp_url: str, method: str, params: dict[str, Any] | None = None, timeout: int = 40) -> dict[str, Any]:
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
        return {"success": False, "error": "non-JSON MCP response", "text": text}
    return parsed if isinstance(parsed, dict) else {"success": False, "data": parsed}


def call_tool(mcp_url: str, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    return unwrap_tool_response(
        rpc(mcp_url, "tools/call", {"name": name, "arguments": arguments}, timeout=50)
    )


def health_url(mcp_url: str) -> str:
    return mcp_url.rstrip("/").removesuffix("/mcp") + "/health"


def parse_kv(parts: list[str]) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    for part in parts:
        if "=" not in part:
            raise SystemExit(f"Bad argument {part!r}; use key=value.")
        key, value = part.split("=", 1)
        if key == "timeout":
            parsed[key] = int(value)
        else:
            parsed[key] = value
    return parsed


def summarize(payload: dict[str, Any], max_processes: int) -> dict[str, Any]:
    data = payload.get("data")
    if isinstance(data, dict) and isinstance(data.get("processes"), list):
        data = dict(data)
        data["processes"] = data["processes"][:max_processes]
        payload = dict(payload)
        payload["data"] = data
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Run safe Frida diagnostics via ANA MCP.")
    parser.add_argument("operation", nargs="?", default="summary", help="summary, version, devices, list_processes, list_modules, find_functions")
    parser.add_argument("arguments", nargs="*", help="Extra key=value args, e.g. target=python.exe module=python312.dll pattern=Py")
    parser.add_argument("--mcp-url", default=DEFAULT_MCP_URL)
    parser.add_argument("--allow-active", action="store_true", help="Allow attach/spawn/inject/hook/terminate operations.")
    parser.add_argument("--max-processes", type=int, default=30)
    parser.add_argument("--output")
    args = parser.parse_args()

    operation = args.operation
    if operation in ACTIVE_OPERATIONS and not args.allow_active:
        raise SystemExit(f"Refusing active Frida operation {operation!r}; rerun with --allow-active if intentional.")
    if operation not in READ_ONLY_OPERATIONS and operation not in ACTIVE_OPERATIONS and operation != "summary":
        raise SystemExit(f"Unknown Frida operation {operation!r}.")

    report: dict[str, Any] = {
        "schema": "ana.frida_diag.v1",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "operation": operation,
    }

    try:
        report["health"] = json_request(health_url(args.mcp_url), timeout=10)
    except Exception as exc:
        report["health_error"] = str(exc)

    if operation == "summary":
        calls = [
            ("version", {"operation": "version", "confirm": True}),
            ("devices", {"operation": "devices", "confirm": True}),
            ("list_processes", {"operation": "list_processes", "confirm": True, **parse_kv(args.arguments)}),
        ]
        results = {}
        for label, payload in calls:
            results[label] = summarize(call_tool(args.mcp_url, "frida_instrument", payload), args.max_processes)
        report["results"] = results
        success = any(item.get("success") for item in results.values())
    else:
        payload = {"operation": operation, "confirm": True, **parse_kv(args.arguments)}
        result = summarize(call_tool(args.mcp_url, "frida_instrument", payload), args.max_processes)
        report["result"] = result
        success = result.get("success") is True

    if args.output:
        output_path = Path(args.output)
    else:
        output_dir = ANA_ROOT / "dev_artifacts" / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"frida_diag_{time.strftime('%Y%m%d_%H%M%S')}.json"
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    summary = {
        "success": success,
        "operation": operation,
        "health": report.get("health", {}).get("status"),
        "mcp_ready": report.get("health", {}).get("mcp_ready"),
        "report": str(output_path),
    }
    if operation == "summary":
        results = report.get("results", {})
        summary["frida_version"] = results.get("version", {}).get("data", {}).get("version")
        summary["process_count"] = results.get("list_processes", {}).get("data", {}).get("count")
    else:
        summary["message"] = report.get("result", {}).get("message")
        summary["error"] = report.get("result", {}).get("error")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if success else 2


if __name__ == "__main__":
    raise SystemExit(main())
