"""ANA MAX nucleus smoke check.

Runs the core observe/route/context/graph/verify/audit loop against the live MCP
server and emits a compact JSON report plus readable status lines.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_MCP_URL = "http://127.0.0.1:8766/mcp"
REPO_ROOT = Path(__file__).resolve().parents[3]
REPORT_DIR = REPO_ROOT / "ANA_MAX" / "dev_artifacts" / "reports"

import ana_operator_status


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
    return parsed if isinstance(parsed, dict) else {"success": False, "error": "tool response is not an object", "data": parsed}


def call_tool(mcp_url: str, name: str, arguments: dict[str, Any] | None = None, timeout: int = 30) -> dict[str, Any]:
    response = rpc(
        mcp_url,
        "tools/call",
        {"name": name, "arguments": arguments or {}},
        timeout=timeout,
    )
    return unwrap_tool_response(response)


def status_for_step(step: dict[str, Any]) -> str:
    if step.get("ok"):
        return "PASS"
    if step.get("optional"):
        return "WARN"
    return "FAIL"


def add_step(report: dict[str, Any], name: str, ok: bool, data: Any = None, error: str | None = None, optional: bool = False) -> None:
    report["steps"].append({
        "name": name,
        "ok": bool(ok),
        "optional": optional,
        "status": "PASS" if ok else ("WARN" if optional else "FAIL"),
        "data": data,
        "error": error,
    })


def run_smoke(mcp_url: str, timeout: int = 30) -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema": "ana.nucleus_smoke.v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "mcp_url": mcp_url,
        "status": "FAIL",
        "steps": [],
        "summary": {},
    }

    try:
        health = json_request(health_url(mcp_url), timeout=timeout)
        add_step(report, "health", bool(health.get("status") == "online" and health.get("mcp_ready")), {
            "status": health.get("status"),
            "mcp_ready": health.get("mcp_ready"),
            "tools_count": health.get("tools_count"),
        })
    except Exception as exc:
        add_step(report, "health", False, error=str(exc))
        finalize(report)
        return report

    try:
        tools_res = rpc(mcp_url, "tools/list", timeout=timeout)
        tools = tools_res.get("result", {}).get("tools", [])
        names = sorted(tool.get("name") for tool in tools if isinstance(tool, dict) and tool.get("name"))
        required = [
            "tool_router",
            "agent_coach",
            "code_context_pack",
            "graph_context_pack",
            "tool_healthcheck",
            "error_radar",
            "session_audit",
        ]
        missing = [name for name in required if name not in names]
        add_step(report, "tools_list", not missing, {"count": len(names), "missing_required": missing})
    except Exception as exc:
        add_step(report, "tools_list", False, error=str(exc))

    checks = [
        ("tool_router", {"task": "ANA nucleus smoke code context verify", "max_tools": 6}, lambda p: p.get("success") and "code_context_pack" in p.get("data", {}).get("recommended_tools", [])),
        ("agent_coach", {"action": "recommend", "task": "ANA nucleus smoke", "max_tools": 6, "include_prompt": False}, lambda p: p.get("success") and bool(p.get("data", {}).get("primary_tool"))),
        ("code_context_pack", {"task": "ANA nucleus smoke graph context", "limit": 3, "include_graph": True}, lambda p: p.get("success") and "graph_map" in p.get("data", {})),
        ("graph_context_pack", {"action": "stats"}, lambda p: p.get("success") and int(p.get("data", {}).get("stats", {}).get("nodes") or 0) > 0),
        ("tool_healthcheck", {"scope": "safe"}, lambda p: p.get("success") and int(p.get("data", {}).get("failed") or 0) == 0),
        ("error_radar", {"limit": 20}, lambda p: p.get("success")),
        ("session_audit", {"action": "trust", "hours": 1, "limit": 100}, lambda p: p.get("success") and int(p.get("data", {}).get("trust", {}).get("score") or 0) >= 50),
    ]
    for name, args, predicate in checks:
        try:
            payload = call_tool(mcp_url, name, args, timeout=timeout)
            ok = bool(predicate(payload))
            add_step(report, name, ok, compact_tool_payload(name, payload))
        except Exception as exc:
            add_step(report, name, False, error=str(exc))

    try:
        context_maps = ana_operator_status.context_maps_status()
        add_step(
            report,
            "context_maps",
            context_maps.get("status") == "PASS",
            compact_tool_payload("context_maps", context_maps),
            optional=True,
        )
    except Exception as exc:
        add_step(report, "context_maps", False, error=str(exc), optional=True)

    finalize(report)
    return report


def compact_tool_payload(name: str, payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data") if isinstance(payload, dict) else {}
    if name == "tool_router":
        return {"message": payload.get("message"), "tools": data.get("recommended_tools"), "mode": data.get("mode")}
    if name == "agent_coach":
        return {"message": payload.get("message"), "primary_tool": data.get("primary_tool"), "severity": data.get("severity")}
    if name == "code_context_pack":
        return {
            "message": payload.get("message"),
            "code_results": len(data.get("code_map", {}).get("results", [])),
            "graph_results": len(data.get("graph_map", {}).get("results", [])),
            "evidence": data.get("compressed_state", {}).get("evidence", []),
        }
    if name == "graph_context_pack":
        stats = data.get("stats", {})
        return {"nodes": stats.get("nodes"), "edges": stats.get("edges"), "updated_at": data.get("updated_at")}
    if name == "tool_healthcheck":
        return {"message": payload.get("message"), "ok": data.get("ok"), "failed": data.get("failed")}
    if name == "error_radar":
        return {"message": payload.get("message"), "count": data.get("count"), "findings": data.get("findings", [])[:3]}
    if name == "session_audit":
        return {"message": payload.get("message"), "score": data.get("trust", {}).get("score"), "signals": data.get("trust", {}).get("signals")}
    if name == "context_maps":
        maps = data if data else payload
        code = maps.get("code_map") if isinstance(maps, dict) else {}
        graph = maps.get("graph_map") if isinstance(maps, dict) else {}
        code = code if isinstance(code, dict) else {}
        graph = graph if isinstance(graph, dict) else {}
        return {
            "message": ana_operator_status.format_context_maps(maps),
            "status": maps.get("status"),
            "code_status": code.get("status"),
            "code_summaries": code.get("summaries"),
            "graph_status": graph.get("status"),
            "graph_nodes": graph.get("nodes"),
            "graph_edges": graph.get("edges"),
        }
    return {"message": payload.get("message"), "success": payload.get("success")}


def finalize(report: dict[str, Any]) -> None:
    statuses = [step["status"] for step in report["steps"]]
    failed = statuses.count("FAIL")
    warned = statuses.count("WARN")
    passed = statuses.count("PASS")
    report["status"] = "FAIL" if failed else ("WARN" if warned else "PASS")
    report["summary"] = {
        "pass": passed,
        "warn": warned,
        "fail": failed,
        "total": len(statuses),
    }


def write_report(report: dict[str, Any]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"nucleus_smoke_{stamp}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def print_human(report: dict[str, Any], report_path: Path | None = None) -> None:
    print(f"ANA Nucleus: {report['status']} ({report['summary']['pass']} pass / {report['summary']['warn']} warn / {report['summary']['fail']} fail)")
    for step in report["steps"]:
        detail = step.get("error") or (step.get("data") or {}).get("message") or ""
        print(f"[{step['status']}] {step['name']} {detail}".rstrip())
    if report_path:
        print(f"report={report_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run ANA MAX nucleus smoke check.")
    parser.add_argument("--mcp-url", default=DEFAULT_MCP_URL)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--json", action="store_true", help="Print JSON only")
    parser.add_argument("--no-write", action="store_true", help="Do not write a report file")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = run_smoke(args.mcp_url, timeout=args.timeout)
    report_path = None if args.no_write else write_report(report)
    if args.json:
        print(json.dumps({**report, "report": str(report_path) if report_path else None}, indent=2, ensure_ascii=False))
    else:
        print_human(report, report_path)
    return 0 if report["status"] in {"PASS", "WARN"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
