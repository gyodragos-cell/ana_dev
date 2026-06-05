"""ANA MAX local lab hub.

One terminal surface for the mother-lab loop:
observe -> diagnose -> act -> verify -> learn.

Modes:
- dev: MCP health + event_stream stats, no screenshots.
- lab: dev + mirror screenshots.
- god: lab + under-hood reports and Frida read-only summary.

This is intentionally local and operator-visible. It starts monitors, prints
their output, and writes compact JSONL status into ANA_MAX/logs/ana_lab_hub.jsonl.
"""

from __future__ import annotations

import argparse
import json
import os
import queue
import subprocess
import sys
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
ANA_ROOT = REPO_ROOT / "ANA_MAX"
LOG_PATH = ANA_ROOT / "logs" / "ana_lab_hub.jsonl"
DEFAULT_MCP_URL = "http://127.0.0.1:8766/mcp"


try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass


def stamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def python_exe() -> str:
    candidate = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
    return str(candidate) if candidate.exists() else sys.executable


def health_url(mcp_url: str) -> str:
    return mcp_url.rstrip("/").removesuffix("/mcp") + "/health"


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


def rpc(mcp_url: str, method: str, params: dict[str, Any] | None = None, timeout: int = 15) -> dict[str, Any]:
    return json_request(
        mcp_url,
        {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000) % 1_000_000,
            "method": method,
            "params": params or {},
        },
        timeout=timeout,
    )


def call_tool(mcp_url: str, tool: str, args: dict[str, Any], timeout: int = 20) -> dict[str, Any]:
    response = rpc(mcp_url, "tools/call", {"name": tool, "arguments": args}, timeout=timeout)
    content = response.get("result", {}).get("content") or []
    if not content:
        return {"success": False, "error": "missing MCP content", "raw": response}
    text = str(content[0].get("text") or "")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {"success": False, "error": "non-JSON MCP content", "text": text[:1000]}
    return payload if isinstance(payload, dict) else {"success": False, "data": payload}


def write_jsonl(payload: dict[str, Any]) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


class ChildPump:
    def __init__(self, verbose: bool = False) -> None:
        self.queue: queue.Queue[tuple[str, str]] = queue.Queue()
        self.children: list[subprocess.Popen[str]] = []
        self.verbose = verbose

    def start(self, label: str, command: list[str]) -> None:
        env = {**os.environ, "PYTHONUNBUFFERED": "1"}
        proc = subprocess.Popen(
            command,
            cwd=str(REPO_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
        self.children.append(proc)
        thread = threading.Thread(target=self._reader, args=(label, proc), daemon=True)
        thread.start()

    def _reader(self, label: str, proc: subprocess.Popen[str]) -> None:
        assert proc.stdout is not None
        for line in proc.stdout:
            line = line.rstrip()
            if line:
                self.queue.put((label, line))
        self.queue.put((label, f"stopped code={proc.poll()}"))

    def drain(self) -> None:
        while True:
            try:
                label, line = self.queue.get_nowait()
            except queue.Empty:
                break
            if not self.verbose and not self._should_print(label, line):
                continue
            print(f"[{stamp()}] [{label}] {line}", flush=True)

    def _should_print(self, label: str, line: str) -> bool:
        if label == "MIRROR":
            return line.startswith("[") or line.startswith("ANA mirror watch") or "stopped code=" in line
        if label == "WATCHDOG":
            synthetic_noise = [
                "MCP tool failed with schema mismatch action versus operation",
                "definitely_missing_tool_for_guidance",
                "name=tool_contract_validator",
                " - INFO - HTTP /mcp tools/call start ",
                " - tools.base - INFO - TOOL END ",
                "Stop repeating tool_router with the same arguments",
                "Stop repeating ana_memory with the same arguments",
            ]
            if any(marker in line for marker in synthetic_noise):
                return False
            if line.startswith("=") or line.startswith("ANA MAX LIVE WATCHDOG") or line.startswith("MCP:"):
                return True
            # Keep human-readable health and warnings, drop raw HTTP/tool-call flood.
            keep_markers = [
                " OK health=",
                " OK smart_ready",
                " OK frida=",
                " WARN ",
                " ERROR ",
                " COACH ",
                "stopped code=",
            ]
            return any(marker in line for marker in keep_markers)
        return True

    def stop(self) -> None:
        for proc in self.children:
            if proc.poll() is None:
                proc.terminate()
        deadline = time.time() + 4
        for proc in self.children:
            if proc.poll() is not None:
                continue
            try:
                proc.wait(timeout=max(0.1, deadline - time.time()))
            except subprocess.TimeoutExpired:
                proc.kill()


def status_tick(mcp_url: str, mode: str) -> dict[str, Any]:
    event: dict[str, Any] = {"timestamp": now_iso(), "mode": mode}
    try:
        health = json_request(health_url(mcp_url), timeout=5)
        event["health"] = {
            "status": health.get("status"),
            "mcp_ready": health.get("mcp_ready"),
            "tools_count": health.get("tools_count"),
            "version": health.get("version"),
        }
    except Exception as exc:
        event["health"] = {"error": str(exc)}

    try:
        stats = call_tool(mcp_url, "event_stream", {"action": "stats", "hours": 1}, timeout=10)
        event["event_stream"] = stats.get("data") if stats.get("success") else {"error": stats.get("error")}
    except Exception as exc:
        event["event_stream"] = {"error": str(exc)}

    if mode == "god":
        try:
            coach = call_tool(
                mcp_url,
                "agent_coach",
                {
                    "action": "recommend",
                    "task": "ANA lab hub periodic check",
                    "max_tools": 5,
                    "include_prompt": False,
                },
                timeout=15,
            )
            event["coach"] = coach.get("data") if coach.get("success") else {"error": coach.get("error")}
        except Exception as exc:
            event["coach"] = {"error": str(exc)}

    write_jsonl(event)
    health = event.get("health", {})
    stats = event.get("event_stream", {})
    print(
        f"[{stamp()}] [HUB] mode={mode} health={health.get('status')} "
        f"ready={health.get('mcp_ready')} tools={health.get('tools_count')} "
        f"events={stats.get('total_events')} errors={stats.get('by_type', {}).get('error')}",
        flush=True,
    )
    return event


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run ANA MAX local lab/god-mode observability hub.")
    parser.add_argument("--mode", choices=["dev", "lab", "god"], default="lab")
    parser.add_argument("--mcp-url", default=DEFAULT_MCP_URL)
    parser.add_argument("--duration", type=float, default=0.0, help="Seconds to run; 0 means until Ctrl+C.")
    parser.add_argument("--tick", type=float, default=10.0)
    parser.add_argument("--no-watchdog", action="store_true")
    parser.add_argument("--no-mirror", action="store_true")
    parser.add_argument("--no-screenshots", action="store_true")
    parser.add_argument("--verbose", action="store_true", help="Print raw child monitor output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    py = python_exe()
    pump = ChildPump(verbose=args.verbose)

    print("=" * 80)
    print("ANA MAX LAB HUB")
    print("=" * 80)
    print(f"repo={REPO_ROOT}")
    print(f"mode={args.mode}")
    print(f"mcp={args.mcp_url}")
    print(f"log={LOG_PATH}")
    print("Ctrl+C stops child monitors.")
    print("=" * 80)

    if not args.no_mirror:
        mirror_cmd = [
            py,
            str(ANA_ROOT / "dev_artifacts" / "scripts" / "ana_mirror_watch.py"),
            "--interval",
            "2",
            "--screenshot-every",
            "10" if args.mode in {"lab", "god"} and not args.no_screenshots else "999999",
        ]
        if args.no_screenshots or args.mode == "dev":
            mirror_cmd.append("--no-screenshots")
        pump.start("MIRROR", mirror_cmd)

    if not args.no_watchdog:
        pump.start("WATCHDOG", [py, str(REPO_ROOT / "ANA_MAX_Launcher" / "live_watchdog.py")])

    if args.mode == "god":
        try:
            frida = call_tool(args.mcp_url, "frida_instrument", {"operation": "version", "confirm": True}, timeout=15)
            print(f"[{stamp()}] [GOD] frida={frida.get('data') or frida.get('message') or frida.get('error')}", flush=True)
        except Exception as exc:
            print(f"[{stamp()}] [GOD] frida_check_error={exc}", flush=True)

    end_time = time.time() + args.duration if args.duration > 0 else None
    next_tick = 0.0
    try:
        while True:
            pump.drain()
            now = time.time()
            if now >= next_tick:
                status_tick(args.mcp_url, args.mode)
                next_tick = now + args.tick
            if end_time and now >= end_time:
                break
            time.sleep(0.2)
    except KeyboardInterrupt:
        print(f"\n[{stamp()}] [HUB] stopping...")
    finally:
        pump.stop()
        pump.drain()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
