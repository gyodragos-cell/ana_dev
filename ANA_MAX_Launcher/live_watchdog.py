"""
ANA MAX live watchdog.

Keeps one console alive with:
- MCP health and tool count checks
- Frida version check through MCP with confirm=True
- Desktop/window sanity check
- Live tail of ana_max.log for tool calls, warnings, and errors
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path


ANA_DIR = Path(r"C:\Users\billy\Desktop\ana_dev\ANA_MAX")
LAUNCHER_DIR = Path(__file__).resolve().parent
LOG_FILE = ANA_DIR / "logs" / "ana_max.log"
MCP_URL = "http://127.0.0.1:8766/mcp"
HEALTH_URL = "http://127.0.0.1:8766/health"

if str(LAUNCHER_DIR) not in sys.path:
    sys.path.insert(0, str(LAUNCHER_DIR))

from mcp_readiness_check import check as smart_readiness_check  # noqa: E402


def stamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


def http_json(url: str, payload: dict | None = None, timeout: int = 10) -> dict:
    data = None
    method = "GET"
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        method = "POST"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def mcp_call(tool: str, arguments: dict, timeout: int = 15) -> dict:
    payload = {
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000) % 100000,
        "method": "tools/call",
        "params": {"name": tool, "arguments": arguments},
    }
    data = http_json(MCP_URL, payload, timeout=timeout)
    text = data["result"]["content"][0]["text"]
    return json.loads(text)


def mcp_tool_count(timeout: int = 10) -> int:
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    data = http_json(MCP_URL, payload, timeout=timeout)
    return len(data["result"]["tools"])


def print_status() -> None:
    try:
        health = http_json(HEALTH_URL, timeout=5)
        tools = mcp_tool_count()
        print(f"[{stamp()}] OK health={health.get('status')} tools={tools}", flush=True)
    except Exception as exc:
        print(f"[{stamp()}] ERROR MCP health failed: {exc}", flush=True)
        return

    try:
        ready, report = smart_readiness_check(MCP_URL, timeout=12)
        if ready:
            actions = report.get("agent_coach_actions", [])
            print(f"[{stamp()}] OK smart_ready tool_router + agent_coach actions={actions}", flush=True)
        else:
            failed = [item.get("name") for item in report.get("checks", []) if not item.get("ok")]
            print(f"[{stamp()}] WARN smart readiness failed: {failed}", flush=True)
    except Exception as exc:
        print(f"[{stamp()}] WARN smart readiness check error: {exc}", flush=True)

    try:
        frida = mcp_call("frida_instrument", {"operation": "version", "confirm": True})
        if frida.get("success"):
            print(f"[{stamp()}] OK frida={frida.get('data', {}).get('version')}", flush=True)
        else:
            print(f"[{stamp()}] WARN frida failed: {frida.get('message') or frida.get('error')}", flush=True)
    except Exception as exc:
        print(f"[{stamp()}] WARN frida check error: {exc}", flush=True)

    try:
        windows = mcp_call("windows_uia_bridge", {"action": "list_windows", "confirm": True})
        if windows.get("success"):
            count = windows.get("data", {}).get("count")
            print(f"[{stamp()}] OK visible_windows={count}", flush=True)
        else:
            print(f"[{stamp()}] WARN window check failed: {windows.get('message') or windows.get('error')}", flush=True)
    except Exception as exc:
        print(f"[{stamp()}] WARN window check error: {exc}", flush=True)

    try:
        coach = mcp_call(
            "agent_coach",
            {
                "action": "recommend",
                "task": "Watchdog periodic runtime check",
                "limit": 120,
                "repeat_threshold": 5,
                "max_tools": 5,
                "include_prompt": False,
            },
        )
        if coach.get("success"):
            data = coach.get("data", {})
            severity = data.get("severity", "ok")
            headline = data.get("headline", "")
            primary_tool = data.get("primary_tool", "")
            if severity == "ok":
                print(f"[{stamp()}] OK coach={headline} primary={primary_tool}", flush=True)
            else:
                print(f"[{stamp()}] COACH {severity.upper()}: {headline} primary={primary_tool}", flush=True)
                coach_data = data.get("coach", {}) if isinstance(data.get("coach"), dict) else {}
                for item in coach_data.get("advice", [])[:3]:
                    print(f"[{stamp()}] COACH - {item}", flush=True)
        else:
            print(f"[{stamp()}] WARN coach failed: {coach.get('message') or coach.get('error')}", flush=True)
    except Exception as exc:
        print(f"[{stamp()}] WARN coach check error: {exc}", flush=True)


def log_position() -> int:
    if not LOG_FILE.exists():
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        return 0
    with LOG_FILE.open("rb") as handle:
        handle.seek(0, 2)
        return handle.tell()


def print_log_line(line: str) -> None:
    upper = line.upper()
    interesting = (
        "ERROR" in upper
        or "WARNING" in upper
        or "TOOL START" in upper
        or "TOOL END" in upper
        or "HTTP /MCP" in upper
        or "HTTP /EXECUTE" in upper
    )
    if not interesting:
        return
    prefix = "LOG"
    if "ERROR" in upper or "STATUS=ERROR" in upper or "SUCCESS=FALSE" in upper:
        prefix = "ERROR"
    elif "WARNING" in upper or "REQUIRES_CONFIRMATION" in upper:
        prefix = "WARN"
    elif "STATUS=SUCCESS" in upper or "SUCCESS=TRUE" in upper:
        prefix = "OK"
    print(f"[{stamp()}] {prefix} {line.rstrip()}", flush=True)


def main() -> int:
    print("=" * 80)
    print("ANA MAX LIVE WATCHDOG")
    print("=" * 80)
    print(f"MCP: {MCP_URL}")
    print(f"Log: {LOG_FILE}")
    print("Press Ctrl+C to stop this watchdog.")
    print("=" * 80)

    pos = log_position()
    next_status = 0.0

    while True:
        now = time.time()
        if now >= next_status:
            print_status()
            next_status = now + 15

        if LOG_FILE.exists():
            try:
                with LOG_FILE.open("r", encoding="utf-8", errors="replace") as handle:
                    handle.seek(pos)
                    lines = handle.readlines()
                    pos = handle.tell()
                for line in lines:
                    print_log_line(line)
            except OSError as exc:
                print(f"[{stamp()}] WARN log read failed: {exc}", flush=True)

        time.sleep(0.5)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print(f"\n[{stamp()}] Watchdog stopped.")
