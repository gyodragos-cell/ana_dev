"""ANA MAX MCP readiness check.

This verifies the useful agent surface, not only that a server is listening.
It is intentionally small and stdlib-only so launch scripts can call it before
opening agent IDEs.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from typing import Any


DEFAULT_MCP_URL = "http://127.0.0.1:8766/mcp"


def _json_request(url: str, payload: dict[str, Any] | None = None, timeout: int = 15) -> dict[str, Any]:
    data = None
    method = "GET"
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        method = "POST"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def _rpc(mcp_url: str, method: str, params: dict[str, Any] | None = None, timeout: int = 20) -> dict[str, Any]:
    payload = {
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000) % 1_000_000,
        "method": method,
        "params": params or {},
    }
    return _json_request(mcp_url, payload, timeout=timeout)


def _unwrap_tool_payload(response: dict[str, Any]) -> dict[str, Any]:
    if "error" in response:
        return {"success": False, "error": response["error"]}
    content = response.get("result", {}).get("content", [])
    if not content:
        return {"success": False, "error": "missing MCP content"}
    text = str(content[0].get("text") or "")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {"success": False, "error": f"non-JSON tool response: {text[:120]}"}
    if not isinstance(payload, dict):
        return {"success": False, "error": "tool response is not an object"}
    return payload


def _health_url(mcp_url: str) -> str:
    return mcp_url.rstrip("/").removesuffix("/mcp") + "/health"


def check(mcp_url: str, timeout: int, expected_tools: list[str] | None = None) -> tuple[bool, dict[str, Any]]:
    report: dict[str, Any] = {
        "mcp_url": mcp_url,
        "health_url": _health_url(mcp_url),
        "checks": [],
    }

    def record(name: str, ok: bool, detail: Any = None) -> None:
        report["checks"].append({"name": name, "ok": ok, "detail": detail})

    try:
        health = _json_request(report["health_url"], timeout=timeout)
        report["health"] = health
        record("health_online", health.get("status") == "online" and bool(health.get("mcp_ready")), health)
    except (OSError, urllib.error.URLError, TimeoutError) as exc:
        record("health_online", False, str(exc))
        return False, report

    try:
        tools_response = _rpc(mcp_url, "tools/list", timeout=timeout)
        tools = tools_response.get("result", {}).get("tools", [])
        names = sorted(str(tool.get("name")) for tool in tools if isinstance(tool, dict))
        report["tool_count"] = len(names)
        record("tools_list", bool(names), {"tool_count": len(names)})
        record("tool_router_present", "tool_router" in names, "tool_router")
        record("agent_coach_present", "agent_coach" in names, "agent_coach")
        for tool_name in expected_tools or []:
            record(f"expected_tool_present:{tool_name}", tool_name in names, tool_name)

        agent_schema = next((tool for tool in tools if tool.get("name") == "agent_coach"), {})
        action_enum = (
            agent_schema.get("inputSchema", {})
            .get("properties", {})
            .get("action", {})
            .get("enum", [])
        )
        report["agent_coach_actions"] = action_enum
        record("agent_coach_recommend_schema", "recommend" in action_enum, action_enum)
    except (OSError, urllib.error.URLError, TimeoutError, KeyError, TypeError) as exc:
        record("tools_list", False, str(exc))
        return False, report

    try:
        resource_templates = _rpc(mcp_url, "resources/templates/list", timeout=timeout)
        templates = resource_templates.get("result", {}).get("resourceTemplates", [])
        record("resource_templates_list", isinstance(templates, list), {"count": len(templates)})
    except (OSError, urllib.error.URLError, TimeoutError, KeyError, TypeError) as exc:
        record("resource_templates_list", False, str(exc))
        return False, report

    router_payload = _unwrap_tool_payload(
        _rpc(
            mcp_url,
            "tools/call",
            {
                "name": "tool_router",
                "arguments": {
                    "task": "MCP tool failed with schema mismatch action versus operation",
                    "error": "Invalid value for operation",
                    "max_tools": 4,
                },
            },
            timeout=timeout,
        )
    )
    router_data = router_payload.get("data") if isinstance(router_payload.get("data"), dict) else {}
    router_tools = router_data.get("recommended_tools") if isinstance(router_data, dict) else []
    record(
        "tool_router_call",
        bool(router_payload.get("success")) and bool(router_tools),
        {"mode": router_data.get("mode"), "recommended_tools": router_tools},
    )

    recommend_payload = _unwrap_tool_payload(
        _rpc(
            mcp_url,
            "tools/call",
            {
                "name": "agent_coach",
                "arguments": {
                    "action": "recommend",
                    "task": "MCP tool failed with schema mismatch action versus operation",
                    "error": "Invalid value for operation",
                    "max_tools": 5,
                    "include_prompt": False,
                },
            },
            timeout=timeout,
        )
    )
    recommend_data = recommend_payload.get("data") if isinstance(recommend_payload.get("data"), dict) else {}
    record(
        "agent_coach_recommend_call",
        (
            bool(recommend_payload.get("success"))
            and recommend_data.get("schema") == "ana.agent_coach.recommend.v1"
            and bool(recommend_data.get("primary_tool"))
        ),
        {
            "schema": recommend_data.get("schema"),
            "primary_tool": recommend_data.get("primary_tool"),
            "tool_stack": recommend_data.get("tool_stack"),
        },
    )

    failure_payload = _unwrap_tool_payload(
        _rpc(
            mcp_url,
            "tools/call",
            {
                "name": "tool_contract_validator",
                "arguments": {
                    "action": "validate_tool",
                    "tool_name": "definitely_missing_tool_for_guidance",
                },
            },
            timeout=timeout,
        )
    )
    failure_data = failure_payload.get("data") if isinstance(failure_payload.get("data"), dict) else {}
    top_level_summary = (
        failure_payload.get("guidance_summary")
        if isinstance(failure_payload.get("guidance_summary"), dict)
        else {}
    )
    nested_summary = (
        failure_data.get("guidance_summary")
        if isinstance(failure_data.get("guidance_summary"), dict)
        else {}
    )
    guidance_summary = top_level_summary or nested_summary
    report["failure_guidance_summary"] = guidance_summary
    record(
        "failed_tool_guidance_summary",
        (
            failure_payload.get("success") is False
            and bool(guidance_summary.get("primary_tool"))
            and bool(guidance_summary.get("next_action"))
            and bool(top_level_summary)
        ),
        {
            "primary_tool": guidance_summary.get("primary_tool"),
            "source": guidance_summary.get("source"),
            "next_action": guidance_summary.get("next_action"),
            "top_level": bool(top_level_summary),
        },
    )

    ok = all(bool(item["ok"]) for item in report["checks"])
    return ok, report


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify ANA MAX MCP smart readiness.")
    parser.add_argument("--mcp-url", default=DEFAULT_MCP_URL)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument(
        "--expect-tool",
        action="append",
        default=[],
        help="Require an additional tool name to be present in tools/list. Can be repeated.",
    )
    parser.add_argument("--json", action="store_true", help="Print full JSON report.")
    args = parser.parse_args()

    try:
        ok, report = check(args.mcp_url, args.timeout, expected_tools=args.expect_tool)
    except Exception as exc:  # noqa: BLE001 - readiness check must fail closed
        ok = False
        report = {"mcp_url": args.mcp_url, "checks": [{"name": "unexpected_error", "ok": False, "detail": repr(exc)}]}

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=True))
    else:
        status = "OK" if ok else "FAIL"
        print(f"[{status}] ANA MAX MCP readiness: {args.mcp_url}")
        health = report.get("health", {})
        if health:
            print(
                f"      health={health.get('status')} "
                f"mcp_ready={health.get('mcp_ready')} "
                f"tools_count={health.get('tools_count')}"
            )
        for item in report.get("checks", []):
            mark = "OK" if item.get("ok") else "FAIL"
            print(f"      [{mark}] {item.get('name')}: {item.get('detail')}")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
