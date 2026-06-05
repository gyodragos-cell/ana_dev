"""Local ANA mirror feed for shared operator/agent visibility.

This watches the local desktop through ANA MCP and writes a compact JSONL feed:
- active app/window title
- foreground UI snapshot summary
- optional screenshots at a slower interval
- event_stream stats

It intentionally avoids raw keyboard hooks. The mirror is for situational
awareness, not invisible keylogging.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_MCP_URL = "http://127.0.0.1:8766/mcp"
REPO_ROOT = Path(__file__).resolve().parents[3]
LOG_PATH = REPO_ROOT / "ANA_MAX" / "logs" / "ana_mirror.jsonl"


try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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


def rpc(mcp_url: str, method: str, params: dict[str, Any] | None = None, timeout: int = 20) -> dict[str, Any]:
    payload = {
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000) % 1_000_000,
        "method": method,
        "params": params or {},
    }
    return json_request(mcp_url, payload=payload, timeout=timeout)


def call_tool(mcp_url: str, tool_name: str, arguments: dict[str, Any], timeout: int = 20) -> dict[str, Any]:
    response = rpc(
        mcp_url,
        "tools/call",
        {"name": tool_name, "arguments": arguments},
        timeout=timeout,
    )
    content = response.get("result", {}).get("content", [])
    if not content:
        return {"success": False, "error": "missing MCP content", "raw_response": response}
    text = str(content[0].get("text") or "")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {"success": False, "error": "non-JSON tool response", "text": text[:1000]}
    return parsed if isinstance(parsed, dict) else {"success": False, "data": parsed}


def compact_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data") or {}
    return {
        "active_app": data.get("active_app"),
        "title": data.get("title"),
        "buttons": (data.get("buttons") or [])[:20],
        "inputs": (data.get("inputs") or [])[:10],
        "visible_text": (data.get("visible_text") or [])[:25],
        "detected_errors": (data.get("detected_errors") or [])[:10],
        "suggested_actions": (data.get("suggested_actions") or [])[:5],
        "success": payload.get("success") is True,
        "error": payload.get("error"),
    }


def digest_payload(payload: dict[str, Any]) -> str:
    text = json.dumps(payload, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def write_event(event: dict[str, Any], log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def observe_once(
    mcp_url: str,
    log_path: Path,
    last_digest: str | None,
    include_screenshot: bool,
    timeout: int,
) -> str | None:
    event: dict[str, Any] = {"timestamp": now_iso(), "kind": "mirror_tick"}

    try:
        snapshot = call_tool(
            mcp_url,
            "foreground_ui_snapshot",
            {"include_text": True, "max_elements": "40"},
            timeout=timeout,
        )
        compact = compact_snapshot(snapshot)
        event["ui"] = compact
    except Exception as exc:
        event["ui_error"] = str(exc)
        compact = {"ui_error": str(exc)}

    current_digest = digest_payload(compact)
    if current_digest == last_digest and not include_screenshot:
        return last_digest

    try:
        stats = call_tool(mcp_url, "event_stream", {"action": "stats", "hours": 1}, timeout=timeout)
        event["event_stream"] = stats.get("data") if stats.get("success") else {"error": stats.get("error")}
    except Exception as exc:
        event["event_stream"] = {"error": str(exc)}

    if include_screenshot:
        try:
            screenshot = call_tool(
                mcp_url,
                "desktop_control",
                {"operation": "view", "confirm": True},
                timeout=timeout,
            )
            event["screenshot"] = screenshot.get("data") if screenshot.get("success") else {"error": screenshot.get("error")}
        except Exception as exc:
            event["screenshot"] = {"error": str(exc)}

    write_event(event, log_path)
    ui = event.get("ui", {})
    text = f"[{event['timestamp']}] app={ui.get('active_app')} title={ui.get('title')} events={event.get('event_stream', {}).get('total_events')}"
    if "screenshot" in event:
        text += f" screenshot={event['screenshot'].get('file')}"
    print(text, flush=True)
    return current_digest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Watch ANA MCP and write a local mirror JSONL feed.")
    parser.add_argument("--mcp-url", default=DEFAULT_MCP_URL)
    parser.add_argument("--log", default=str(LOG_PATH))
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--screenshot-every", type=float, default=10.0)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--no-screenshots", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    log_path = Path(args.log)
    print("ANA mirror watch")
    print(f"MCP: {args.mcp_url}")
    print(f"Log: {log_path}")
    print("Press Ctrl+C to stop.")

    last_digest: str | None = None
    last_screenshot = 0.0
    while True:
        now = time.time()
        include_screenshot = not args.no_screenshots and (now - last_screenshot >= args.screenshot_every)
        last_digest = observe_once(
            args.mcp_url,
            log_path,
            last_digest,
            include_screenshot=include_screenshot,
            timeout=args.timeout,
        )
        if include_screenshot:
            last_screenshot = now
        if args.once:
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
