"""Small CLI wrapper for calling ANA MAX MCP tools.

Examples:
  python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py --health
  python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py --list
  python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py --schema desktop_control
  python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py desktop_control "{\"operation\":\"view\",\"confirm\":true}"
  python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py desktop_control operation=view confirm=true
  python ANA_MAX/dev_artifacts/scripts/ana_mcp_call.py agent_coach action=recommend max_tools:=5
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from typing import Any


DEFAULT_MCP_URL = "http://127.0.0.1:8766/mcp"


try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass


def health_url(mcp_url: str) -> str:
    return mcp_url.rstrip("/").removesuffix("/mcp") + "/health"


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
        with open(text[1:], "r", encoding="utf-8") as handle:
            text = handle.read().strip()
    if text.startswith("{"):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Arguments must be a JSON object: {exc}") from exc
        if not isinstance(parsed, dict):
            raise SystemExit("Arguments must be a JSON object.")
        return parsed

    parsed: dict[str, Any] = {}
    for part in parts:
        if ":=" in part:
            key, raw_value = part.split(":=", 1)
            if not key:
                raise SystemExit(f"Empty argument key in {part!r}.")
            try:
                parsed[key] = json.loads(raw_value)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Invalid JSON value in {part!r}: {exc}") from exc
            continue
        if "=" not in part:
            raise SystemExit(
                "Arguments must be JSON, @file, key=value, or key:=json pairs "
                f"(bad item: {part!r})."
            )
        key, value = part.split("=", 1)
        if not key:
            raise SystemExit(f"Empty argument key in {part!r}.")
        parsed[key] = coerce_value(value)
    return parsed


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
    if not isinstance(parsed, dict):
        return {"success": False, "error": "tool response is not a JSON object", "data": parsed}
    return parsed


def print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def list_tools(mcp_url: str, timeout: int) -> int:
    response = rpc(mcp_url, "tools/list", timeout=timeout)
    tools = response.get("result", {}).get("tools", [])
    names = sorted(tool.get("name") for tool in tools if isinstance(tool, dict) and tool.get("name"))
    print_json({"mcp_url": mcp_url, "tool_count": len(names), "tools": names})
    return 0 if names else 1


def show_schema(mcp_url: str, timeout: int, tool_name: str) -> int:
    response = rpc(mcp_url, "tools/list", timeout=timeout)
    tools = response.get("result", {}).get("tools", [])
    for tool in tools:
        if isinstance(tool, dict) and tool.get("name") == tool_name:
            print_json(tool)
            return 0
    print_json({"success": False, "error": f"tool not found: {tool_name}"})
    return 1


def call_tool(mcp_url: str, timeout: int, tool_name: str, arguments: dict[str, Any], raw: bool) -> int:
    response = rpc(
        mcp_url,
        "tools/call",
        {"name": tool_name, "arguments": arguments},
        timeout=timeout,
    )
    payload = response if raw else unwrap_tool_response(response)
    print_json(payload)
    if raw:
        return 0 if "error" not in response else 1
    return 0 if payload.get("success") is True else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Call ANA MAX MCP tools from a short CLI.")
    parser.add_argument("tool", nargs="?", help="Tool name, for example desktop_control")
    parser.add_argument(
        "arguments",
        nargs="*",
        help="Tool arguments as JSON, @json-file, or key=value pairs",
    )
    parser.add_argument("--mcp-url", default=DEFAULT_MCP_URL)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--health", action="store_true", help="Print /health and exit")
    parser.add_argument("--list", action="store_true", help="List MCP tools and exit")
    parser.add_argument("--schema", help="Print one tool schema and exit")
    parser.add_argument("--raw", action="store_true", help="Print raw JSON-RPC response")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.health:
        print_json(json_request(health_url(args.mcp_url), timeout=args.timeout))
        return 0
    if args.list:
        return list_tools(args.mcp_url, args.timeout)
    if args.schema:
        return show_schema(args.mcp_url, args.timeout, args.schema)
    if not args.tool:
        parser.error("provide a tool name, --health, --list, or --schema TOOL")

    return call_tool(
        args.mcp_url,
        args.timeout,
        args.tool,
        parse_arguments(args.arguments),
        args.raw,
    )


if __name__ == "__main__":
    raise SystemExit(main())
