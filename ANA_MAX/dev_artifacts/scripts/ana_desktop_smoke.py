"""End-to-end desktop smoke test through ANA MAX MCP.

The script opens Notepad, focuses it, types a marker, and captures proof.
It is intentionally conservative: observe, act once, verify.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from typing import Any


DEFAULT_MCP_URL = "http://127.0.0.1:8766/mcp"
DEFAULT_TEXT = "ANA MAX desktop smoke ok"


try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass


def json_request(url: str, payload: dict[str, Any], timeout: int = 20) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def rpc(mcp_url: str, method: str, params: dict[str, Any] | None = None, timeout: int = 20) -> dict[str, Any]:
    payload = {
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000) % 1_000_000,
        "method": method,
        "params": params or {},
    }
    return json_request(mcp_url, payload, timeout=timeout)


def call_tool(mcp_url: str, name: str, arguments: dict[str, Any], timeout: int = 25) -> dict[str, Any]:
    response = rpc(
        mcp_url,
        "tools/call",
        {"name": name, "arguments": arguments},
        timeout=timeout,
    )
    content = response.get("result", {}).get("content", [])
    if not content:
        return {"success": False, "error": "missing MCP content", "raw_response": response}
    text = str(content[0].get("text") or "")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {"success": False, "error": "non-JSON response", "text": text}
    return parsed if isinstance(parsed, dict) else {"success": False, "data": parsed}


def health(mcp_url: str, timeout: int = 10) -> dict[str, Any]:
    health_url = mcp_url.rstrip("/").removesuffix("/mcp") + "/health"
    req = urllib.request.Request(health_url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def print_step(name: str, payload: dict[str, Any]) -> None:
    ok = payload.get("success")
    if ok is None:
        ok = payload.get("status") == "online" or payload.get("mcp_ready") is True
    status = "OK" if ok else "WARN"
    message = payload.get("message") or payload.get("error") or payload.get("status") or ""
    print(f"[{status}] {name}: {message}")


def find_edit_element(inspect_payload: dict[str, Any]) -> dict[str, Any] | None:
    data = inspect_payload.get("data") if isinstance(inspect_payload.get("data"), dict) else {}
    elements = data.get("elements") if isinstance(data.get("elements"), list) else []
    for element in elements:
        if element.get("control_type") == "Edit":
            return element
    for element in elements:
        if element.get("control_type") == "Document":
            return element
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a Notepad eyes-and-hands smoke test.")
    parser.add_argument("--mcp-url", default=DEFAULT_MCP_URL)
    parser.add_argument("--text", default=DEFAULT_TEXT)
    parser.add_argument("--no-launch", action="store_true", help="Use an already-open Notepad.")
    parser.add_argument("--close-at-end", action="store_true", help="Close Notepad after the test.")
    args = parser.parse_args()

    report: dict[str, Any] = {"schema": "ana.desktop_smoke.v1", "steps": []}

    try:
        health_payload = health(args.mcp_url)
    except Exception as exc:
        print(f"[FAIL] health: {exc}")
        return 1
    report["health"] = health_payload
    print_step("health", health_payload)
    if not health_payload.get("mcp_ready"):
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1

    process = None
    if not args.no_launch:
        process = subprocess.Popen(["notepad.exe"])
        time.sleep(1.2)
        report["notepad_pid"] = process.pid
        print(f"[OK] launch_notepad: pid={process.pid}")

    steps = [
        ("windows_before", "desktop_capture", {"operation": "get_windows"}),
        ("focus_notepad", "window_manager", {"action": "focus", "title": "Notepad"}),
        ("inspect_notepad", "windows_uia_bridge", {"action": "inspect_window", "window_title": "Notepad", "confirm": True}),
    ]

    inspect_payload: dict[str, Any] = {}
    for step_name, tool, arguments in steps:
        payload = call_tool(args.mcp_url, tool, arguments)
        report["steps"].append({"step": step_name, "tool": tool, "arguments": arguments, "result": payload})
        print_step(step_name, payload)
        if step_name == "inspect_notepad":
            inspect_payload = payload

    edit = find_edit_element(inspect_payload)
    typed = False
    if edit:
        control_type = edit.get("control_type") or "Edit"
        type_args = {
            "action": "type_text",
            "window_title": "Notepad",
            "control_type": control_type,
            "text": args.text,
            "confirm": True,
        }
        if edit.get("auto_id"):
            type_args["auto_id"] = edit["auto_id"]
        elif edit.get("title"):
            type_args["element_title"] = edit["title"]
        else:
            type_args["control_type"] = control_type
        type_payload = call_tool(args.mcp_url, "windows_uia_bridge", type_args)
        report["steps"].append({"step": "type_uia", "tool": "windows_uia_bridge", "arguments": type_args, "result": type_payload})
        print_step("type_uia", type_payload)
        typed = type_payload.get("success") is True
    if not typed:
        focus_payload = call_tool(args.mcp_url, "window_manager", {"action": "focus", "title": "Notepad"})
        click_payload = call_tool(args.mcp_url, "desktop_control", {"operation": "click_at", "target": "400,300", "confirm": True})
        type_payload = call_tool(args.mcp_url, "desktop_control", {"operation": "type", "target": args.text, "confirm": True})
        for step_name, tool, arguments, payload in [
            ("focus_notepad_fallback", "window_manager", {"action": "focus", "title": "Notepad"}, focus_payload),
            ("click_editor_fallback", "desktop_control", {"operation": "click_at", "target": "400,300", "confirm": True}, click_payload),
            ("type_desktop_fallback", "desktop_control", {"operation": "type", "target": args.text, "confirm": True}, type_payload),
        ]:
            report["steps"].append({"step": step_name, "tool": tool, "arguments": arguments, "result": payload})
            print_step(step_name, payload)

    for step_name, tool, arguments in [
        ("snapshot_after", "foreground_ui_snapshot", {"include_text": True, "max_elements": "12"}),
        ("screenshot_after", "desktop_control", {"operation": "view", "confirm": True}),
    ]:
        payload = call_tool(args.mcp_url, tool, arguments)
        report["steps"].append({"step": step_name, "tool": tool, "arguments": arguments, "result": payload})
        print_step(step_name, payload)

    if args.close_at_end:
        close_payload = call_tool(args.mcp_url, "window_manager", {"action": "close", "title": "Notepad"})
        report["steps"].append({"step": "close_notepad", "tool": "window_manager", "arguments": {"action": "close", "title": "Notepad"}, "result": close_payload})
        print_step("close_notepad", close_payload)

    success = any(
        step.get("step") in {"type_uia", "type_desktop_fallback"}
        and step.get("result", {}).get("success") is True
        for step in report["steps"]
    )
    report["success"] = success
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if success else 2


if __name__ == "__main__":
    raise SystemExit(main())
