"""Run one ANA MCP action with observe/act/verify/diagnose structure."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
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


def json_request(url: str, payload: dict[str, Any] | None = None, timeout: int = 20) -> dict[str, Any]:
    data = None
    method = "GET"
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        method = "POST"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def rpc(mcp_url: str, method: str, params: dict[str, Any] | None = None, timeout: int = 25) -> dict[str, Any]:
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
        return {"success": False, "error": "non-JSON tool response", "text": text}
    return parsed if isinstance(parsed, dict) else {"success": False, "data": parsed}


def call_tool(mcp_url: str, name: str, arguments: dict[str, Any], timeout: int = 30) -> dict[str, Any]:
    return unwrap_tool_response(
        rpc(mcp_url, "tools/call", {"name": name, "arguments": arguments}, timeout=timeout)
    )


def health_url(mcp_url: str) -> str:
    return mcp_url.rstrip("/").removesuffix("/mcp") + "/health"


def coerce_value(value: str) -> Any:
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered == "null":
        return None
    return value


def parse_arguments(parts: list[str]) -> dict[str, Any]:
    if not parts:
        return {}
    text = " ".join(parts).strip()
    if len(parts) == 1 and text.startswith("@"):
        text = Path(text[1:]).read_text(encoding="utf-8")
    if text.startswith("{"):
        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            raise SystemExit("Tool arguments JSON must be an object.")
        return parsed

    parsed: dict[str, Any] = {}
    for part in parts:
        if ":=" in part:
            key, raw_value = part.split(":=", 1)
            parsed[key] = json.loads(raw_value)
            continue
        if "=" not in part:
            raise SystemExit(f"Bad argument {part!r}; use key=value, key:=json, JSON, or @file.")
        key, value = part.split("=", 1)
        parsed[key] = coerce_value(value)
    return parsed


def compact(payload: dict[str, Any], max_chars: int = 1400) -> dict[str, Any]:
    text = json.dumps(payload, ensure_ascii=False)
    if len(text) <= max_chars:
        return payload
    return {
        "success": payload.get("success"),
        "message": payload.get("message"),
        "error": payload.get("error"),
        "guidance_summary": payload.get("guidance_summary"),
        "truncated": True,
    }


def print_line(label: str, payload: dict[str, Any]) -> None:
    ok = payload.get("success")
    if ok is None:
        ok = payload.get("status") == "online" or payload.get("mcp_ready") is True
    state = "OK" if ok else "FAIL"
    msg = payload.get("message") or payload.get("error") or payload.get("status") or ""
    print(f"[{state}] {label}: {msg}")


def build_next_action(action_payload: dict[str, Any], diagnosis: dict[str, Any] | None) -> str:
    if action_payload.get("success") is True:
        return "Action succeeded. Use the verification payload before the next mutation."
    guidance = action_payload.get("guidance_summary")
    if isinstance(guidance, dict) and guidance.get("next_action"):
        return str(guidance["next_action"])
    if diagnosis and isinstance(diagnosis.get("coach", {}).get("data"), dict):
        next_action = diagnosis["coach"]["data"].get("next_action")
        if next_action:
            return str(next_action)
    return "Inspect the error, change one input or tool, then retry once and verify."


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one ANA MCP step with observe/act/verify.")
    parser.add_argument("tool", help="Tool to call")
    parser.add_argument("arguments", nargs="*", help="Tool args: key=value, key:=json, JSON, or @file")
    parser.add_argument("--mcp-url", default=DEFAULT_MCP_URL)
    parser.add_argument("--no-screenshot", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()

    tool_args = parse_arguments(args.arguments)
    report: dict[str, Any] = {
        "schema": "ana.agent_step.v1",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tool": args.tool,
        "arguments": tool_args,
    }

    try:
        health = json_request(health_url(args.mcp_url), timeout=10)
    except Exception as exc:
        health = {"success": False, "error": str(exc)}
    report["health"] = health
    print_line("health", health)

    observe = {
        "workspace": call_tool(
            args.mcp_url,
            "workspace_situational_awareness",
            {"include_git": True, "include_errors": True, "include_uia": True},
        ),
        "ui": call_tool(
            args.mcp_url,
            "foreground_ui_snapshot",
            {"include_text": False, "max_elements": "8"},
        ),
    }
    report["observe"] = observe
    print_line("observe.workspace", observe["workspace"])
    print_line("observe.ui", observe["ui"])

    action = call_tool(args.mcp_url, args.tool, tool_args)
    report["action"] = action
    print_line(f"act.{args.tool}", action)

    verify: dict[str, Any] = {
        "ui": call_tool(args.mcp_url, "foreground_ui_snapshot", {"include_text": True, "max_elements": "10"}),
    }
    if not args.no_screenshot:
        verify["screenshot"] = call_tool(args.mcp_url, "desktop_control", {"operation": "view", "confirm": True})
    report["verify"] = verify
    print_line("verify.ui", verify["ui"])
    if "screenshot" in verify:
        print_line("verify.screenshot", verify["screenshot"])

    diagnosis = None
    if action.get("success") is not True:
        diagnosis = {
            "error_radar": call_tool(args.mcp_url, "error_radar", {"scope": "all", "limit": 8}),
            "coach": call_tool(
                args.mcp_url,
                "agent_coach",
                {
                    "action": "recommend",
                    "task": f"Tool {args.tool} failed during ana_agent_step",
                    "error": str(action.get("error") or action.get("message") or action),
                    "max_tools": 6,
                    "include_prompt": False,
                },
            ),
        }
        report["diagnosis"] = diagnosis
        print_line("diagnose.error_radar", diagnosis["error_radar"])
        print_line("diagnose.coach", diagnosis["coach"])

    report["success"] = action.get("success") is True
    report["next_action"] = build_next_action(action, diagnosis)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    output_path = Path(args.output) if args.output else (
        ANA_ROOT / "dev_artifacts" / "reports" / f"agent_step_{stamp}.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    report["report"] = str(output_path)

    print(json.dumps({
        "success": report["success"],
        "tool": args.tool,
        "action": compact(action),
        "next_action": report["next_action"],
        "report": str(output_path),
    }, indent=2, ensure_ascii=False))
    return 0 if report["success"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
