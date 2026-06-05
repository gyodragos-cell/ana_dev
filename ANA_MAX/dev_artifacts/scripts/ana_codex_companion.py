"""ANA companion check for Codex work.

This is the small bridge Billy asked for: before Codex edits or tests, ANA gets
to observe the active workspace, route the task, challenge blind/repeated work,
and return a compact "ANA vs Codex" next-action report.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
from typing import Any
import urllib.request


REPO_ROOT = Path(__file__).resolve().parents[3]
ANA_ROOT = REPO_ROOT / "ANA_MAX"
REPORT_DIR = ANA_ROOT / "dev_artifacts" / "reports"
DEFAULT_MCP_URL = "http://127.0.0.1:8766/mcp"


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def health_url(mcp_url: str) -> str:
    return mcp_url.rstrip("/").removesuffix("/mcp") + "/health"


def json_request(url: str, payload: dict[str, Any] | None = None, timeout: int = 30) -> dict[str, Any]:
    data = None
    method = "GET"
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        method = "POST"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def rpc(mcp_url: str, method: str, params: dict[str, Any] | None = None, timeout: int = 30) -> dict[str, Any]:
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
        return {"success": False, "error": "non-JSON tool response", "text": text[:500]}
    return parsed if isinstance(parsed, dict) else {"success": False, "data": parsed}


def call_tool(mcp_url: str, name: str, arguments: dict[str, Any] | None = None, timeout: int = 30) -> dict[str, Any]:
    return unwrap_tool_response(
        rpc(mcp_url, "tools/call", {"name": name, "arguments": arguments or {}}, timeout=timeout)
    )


def safe_data(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data")
    return data if isinstance(data, dict) else {}


def compact_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    data = safe_data(payload)
    return {
        "success": payload.get("success"),
        "message": payload.get("message"),
        "active_app": data.get("active_app"),
        "title": data.get("title"),
        "buttons": (data.get("buttons") or [])[:8],
        "suggested_actions": (data.get("suggested_actions") or [])[:3],
    }


def compact_context(payload: dict[str, Any]) -> dict[str, Any]:
    data = safe_data(payload)
    code_map = data.get("code_map") if isinstance(data.get("code_map"), dict) else {}
    graph_map = data.get("graph_map") if isinstance(data.get("graph_map"), dict) else {}
    state = data.get("compressed_state") if isinstance(data.get("compressed_state"), dict) else {}
    return {
        "success": payload.get("success"),
        "message": payload.get("message"),
        "current_file_candidates": state.get("current_file_candidates", [])[:5],
        "evidence": state.get("evidence", []),
        "code_results": [
            {
                "file": item.get("file"),
                "score": item.get("score"),
                "matched_terms": item.get("matched_terms", []),
            }
            for item in (code_map.get("results") or [])[:5]
            if isinstance(item, dict)
        ],
        "graph_results": [
            {
                "name": item.get("name"),
                "kind": item.get("kind"),
                "score": item.get("score"),
                "matched_terms": item.get("matched_terms", []),
            }
            for item in (graph_map.get("results") or [])[:5]
            if isinstance(item, dict)
        ],
    }


def compact_router(payload: dict[str, Any]) -> dict[str, Any]:
    data = safe_data(payload)
    return {
        "success": payload.get("success"),
        "message": payload.get("message"),
        "mode": data.get("mode"),
        "headline": data.get("headline"),
        "recommended_tools": data.get("recommended_tools", []),
        "steps": data.get("steps", []),
        "guardrail": data.get("guardrail", ""),
    }


def compact_coach(payload: dict[str, Any]) -> dict[str, Any]:
    data = safe_data(payload)
    coach = data.get("coach") if isinstance(data.get("coach"), dict) else {}
    return {
        "success": payload.get("success"),
        "message": payload.get("message"),
        "severity": data.get("severity") or coach.get("severity"),
        "headline": data.get("headline"),
        "primary_tool": data.get("primary_tool"),
        "tool_stack": data.get("tool_stack", []),
        "signals": coach.get("signals", []),
        "next_action": data.get("next_action"),
    }


def compact_healthcheck(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not payload:
        return None
    data = safe_data(payload)
    return {
        "success": payload.get("success"),
        "message": payload.get("message"),
        "ok": data.get("ok"),
        "failed": data.get("failed"),
        "dependencies": data.get("dependencies", {}),
    }


def compact_radar(payload: dict[str, Any]) -> dict[str, Any]:
    data = safe_data(payload)
    return {
        "success": payload.get("success"),
        "message": payload.get("message"),
        "count": data.get("count", 0),
        "summary": data.get("summary", {}),
        "recommended_next_step": data.get("recommended_next_step", ""),
        "findings": [
            {
                "source": item.get("source"),
                "kind": item.get("kind"),
                "severity": item.get("severity"),
                "summary": item.get("summary"),
            }
            for item in (data.get("findings") or [])[:5]
            if isinstance(item, dict)
        ],
    }


def build_debate(report: dict[str, Any], planned_tool: str = "") -> dict[str, Any]:
    health = report.get("health", {})
    router = report.get("router", {})
    coach = report.get("coach", {})
    context = report.get("context", {})
    radar = report.get("error_radar", {})
    challenges: list[str] = []

    if not (health.get("status") == "online" and health.get("mcp_ready")):
        challenges.append("MCP health is not ready; Codex must not act blind.")
    if coach.get("severity") in {"warn", "critical"}:
        signal_text = "; ".join(str(item.get("type")) for item in coach.get("signals", []) if isinstance(item, dict))
        challenges.append(f"Coach severity is {coach.get('severity')}; inspect signals before editing: {signal_text or 'no compact signal'}")
    if planned_tool and coach.get("primary_tool") and planned_tool != coach.get("primary_tool"):
        challenges.append(f"Codex planned {planned_tool}, but ANA primary tool is {coach.get('primary_tool')}.")
    if not context.get("current_file_candidates") and not context.get("code_results"):
        challenges.append("Code Context Pack returned no focused file candidates.")
    if int(radar.get("count") or 0) > 0:
        challenges.append(f"Error Radar has {radar.get('count')} finding(s): {radar.get('recommended_next_step') or 'review before mutation'}.")

    status = "FAIL" if not (health.get("status") == "online" and health.get("mcp_ready")) else ("WARN" if challenges else "PASS")
    ana_line = coach.get("headline") or router.get("headline") or "ANA has no challenge."
    codex_line = (
        "I stop and repair MCP readiness before acting."
        if status == "FAIL"
        else "I will address ANA's challenge before any mutation."
        if status == "WARN"
        else "I may proceed with one scoped action, then verify."
    )
    next_action = (
        coach.get("next_action")
        or (router.get("steps") or ["Use one scoped verified action."])[0]
    )
    return {
        "status": status,
        "ana": ana_line,
        "codex": codex_line,
        "challenges": challenges,
        "next_action": next_action,
        "lines": [
            f"[ANA] {ana_line}",
            *[f"[ANA challenge] {challenge}" for challenge in challenges],
            f"[CODEX] {codex_line}",
            f"[NEXT] {next_action}",
        ],
    }


def run_companion(
    goal: str,
    mcp_url: str = DEFAULT_MCP_URL,
    planned_tool: str = "",
    timeout: int = 30,
    include_text: bool = False,
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema": "ana.codex_companion.v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "goal": goal,
        "planned_tool": planned_tool,
        "mcp_url": mcp_url,
    }

    try:
        report["health"] = json_request(health_url(mcp_url), timeout=timeout)
    except Exception as exc:
        report["health"] = {"status": "offline", "mcp_ready": False, "error": str(exc)}

    snapshot = call_tool(
        mcp_url,
        "foreground_ui_snapshot",
        {"include_text": include_text, "max_elements": "30" if include_text else "20"},
        timeout=timeout,
    )
    router = call_tool(mcp_url, "tool_router", {"task": goal, "max_tools": 6}, timeout=timeout)
    coach = call_tool(
        mcp_url,
        "agent_coach",
        {"action": "recommend", "task": goal, "max_tools": 6, "include_prompt": False},
        timeout=timeout,
    )
    context = call_tool(
        mcp_url,
        "code_context_pack",
        {"query": goal, "include_graph": True, "include_text": False, "limit": 4},
        timeout=max(timeout, 60),
    )
    radar = call_tool(mcp_url, "error_radar", {"scope": "quick", "limit": 12}, timeout=timeout)

    compacted_coach = compact_coach(coach)
    healthcheck = None
    if compacted_coach.get("severity") in {"warn", "critical"} or compacted_coach.get("primary_tool") == "tool_healthcheck":
        healthcheck = call_tool(mcp_url, "tool_healthcheck", {"scope": "safe"}, timeout=max(timeout, 60))

    report["snapshot"] = compact_snapshot(snapshot)
    report["router"] = compact_router(router)
    report["coach"] = compacted_coach
    report["context"] = compact_context(context)
    report["error_radar"] = compact_radar(radar)
    report["tool_healthcheck"] = compact_healthcheck(healthcheck)
    report["debate"] = build_debate(report, planned_tool=planned_tool)
    report["status"] = report["debate"]["status"]
    return report


def write_report(report: dict[str, Any]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    path = REPORT_DIR / f"codex_companion_{stamp}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def print_human(report: dict[str, Any], report_path: Path | None = None) -> None:
    debate = report.get("debate", {})
    print(f"ANA Codex Companion: {report.get('status')} goal={report.get('goal')}")
    for line in debate.get("lines", []):
        print(line)
    context = report.get("context", {})
    candidates = context.get("current_file_candidates") or []
    if candidates:
        print("context=" + ", ".join(str(item) for item in candidates[:4]))
    healthcheck = report.get("tool_healthcheck")
    if healthcheck:
        print(f"healthcheck={healthcheck.get('message')} failed={healthcheck.get('failed')}")
    if report_path:
        print(f"report={report_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Let ANA observe and challenge Codex before work.")
    parser.add_argument("--goal", default="Prepare the next scoped ANA MAX lab action.")
    parser.add_argument("--planned-tool", default="", help="Optional Codex-planned primary tool for ANA to challenge.")
    parser.add_argument("--mcp-url", default=DEFAULT_MCP_URL)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--include-text", action="store_true", help="Allow foreground UI text in the snapshot.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-write", action="store_true", help="Do not write a companion report.")
    parser.add_argument("--strict", action="store_true", help="Return non-zero on WARN as well as FAIL.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = run_companion(
        goal=args.goal,
        mcp_url=args.mcp_url,
        planned_tool=args.planned_tool,
        timeout=args.timeout,
        include_text=args.include_text,
    )
    report_path = None if args.no_write else write_report(report)
    if args.json:
        print(json.dumps({**report, "report": str(report_path) if report_path else None}, indent=2, ensure_ascii=False))
    else:
        print_human(report, report_path)
    if report["status"] == "FAIL":
        return 2
    if args.strict and report["status"] == "WARN":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
