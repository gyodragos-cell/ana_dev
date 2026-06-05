"""Check whether live MCP exposes selected current disk-side behaviors.

Read-only. This catches the common case where the running MCP process is
healthy but stale after source edits.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


DEFAULT_MCP_URL = "http://127.0.0.1:8766/mcp"
CONTEXT_NOISE_QUERY = "next scoped lab action after green baseline"
EXPECTED_CONTEXT_TOP_FILE = "ANA_MAX/dev_artifacts/scripts/ana_autonomy_runner.py"
SCRIPT_DIR = Path(__file__).resolve().parent
ANA_ROOT = SCRIPT_DIR.parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(ANA_ROOT) not in sys.path:
    sys.path.insert(0, str(ANA_ROOT))

import ana_mcp_call
from tools.error_radar_tool import ErrorRadarTool


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def call_live_session_trust(mcp_url: str, timeout: int = 30) -> dict[str, Any]:
    response = ana_mcp_call.rpc(
        mcp_url,
        "tools/call",
        {
            "name": "session_audit",
            "arguments": {"action": "trust", "hours": 1, "limit": 40},
        },
        timeout=timeout,
    )
    return ana_mcp_call.unwrap_tool_response(response)


def call_live_error_radar(mcp_url: str, timeout: int = 30) -> dict[str, Any]:
    response = ana_mcp_call.rpc(
        mcp_url,
        "tools/call",
        {
            "name": "error_radar",
            "arguments": {"scope": "git", "limit": 20},
        },
        timeout=timeout,
    )
    return ana_mcp_call.unwrap_tool_response(response)


def call_live_code_context_query_alias(mcp_url: str, timeout: int = 30) -> dict[str, Any]:
    query = "operator status reload behavior"
    response = ana_mcp_call.rpc(
        mcp_url,
        "tools/call",
        {
            "name": "code_context_pack",
            "arguments": {
                "query": query,
                "limit": 1,
                "include_graph": False,
                "include_text": False,
            },
        },
        timeout=timeout,
    )
    return ana_mcp_call.unwrap_tool_response(response)


def call_live_code_context_graph_preference(mcp_url: str, timeout: int = 30) -> dict[str, Any]:
    query = "operator status reload behavior"
    response = ana_mcp_call.rpc(
        mcp_url,
        "tools/call",
        {
            "name": "code_context_pack",
            "arguments": {
                "query": query,
                "limit": 3,
                "include_graph": True,
                "include_text": False,
            },
        },
        timeout=timeout,
    )
    return ana_mcp_call.unwrap_tool_response(response)


def call_live_code_context_graph_limit_one(mcp_url: str, timeout: int = 30) -> dict[str, Any]:
    query = "operator status reload behavior"
    response = ana_mcp_call.rpc(
        mcp_url,
        "tools/call",
        {
            "name": "code_context_pack",
            "arguments": {
                "query": query,
                "limit": 1,
                "include_graph": True,
                "include_text": False,
            },
        },
        timeout=timeout,
    )
    return ana_mcp_call.unwrap_tool_response(response)


def call_live_agent_coach_monitor_filter(mcp_url: str, timeout: int = 30) -> dict[str, Any]:
    response = ana_mcp_call.rpc(
        mcp_url,
        "tools/call",
        {
            "name": "agent_coach",
            "arguments": {
                "action": "recommend",
                "task": "continue lab reliability work after fresh review ledger",
                "max_tools": 6,
                "include_prompt": False,
            },
        },
        timeout=timeout,
    )
    return ana_mcp_call.unwrap_tool_response(response)


def call_live_context_generated_noise_filter(mcp_url: str, timeout: int = 30) -> dict[str, Any]:
    response = ana_mcp_call.rpc(
        mcp_url,
        "tools/call",
        {
            "name": "code_context_pack",
            "arguments": {
                "query": CONTEXT_NOISE_QUERY,
                "limit": 5,
                "include_graph": True,
                "include_text": False,
            },
        },
        timeout=timeout,
    )
    return ana_mcp_call.unwrap_tool_response(response)


def dirty_tree_runtime_count(payload: dict[str, Any]) -> int | None:
    data = payload.get("data") if isinstance(payload, dict) else {}
    data = data if isinstance(data, dict) else {}
    for finding in data.get("findings") or []:
        if isinstance(finding, dict) and finding.get("kind") == "large_dirty_tree":
            details = finding.get("details") if isinstance(finding.get("details"), dict) else {}
            runtime = details.get("runtime")
            return runtime if isinstance(runtime, int) else None
    return None


def radar_summary_present(payload: dict[str, Any]) -> bool:
    data = payload.get("data") if isinstance(payload, dict) else {}
    data = data if isinstance(data, dict) else {}
    summary = data.get("summary")
    if not isinstance(summary, dict):
        return False
    required = {"by_severity", "by_kind", "by_source", "top_kind", "top_severity", "top_source"}
    return required.issubset(summary)


def disk_error_radar_runtime_count() -> int | None:
    result = ErrorRadarTool().execute(scope="git", limit=20)
    return dirty_tree_runtime_count({"data": result.data})


def generated_memory_path(value: Any) -> bool:
    text = str(value or "").replace("\\", "/").lower()
    return (
        "session_checkpoint_" in text
        or "/docs/rem_sleep/" in text
        or "/dev_artifacts/archives/" in text
        or "/archives/" in text
    )


def context_generated_noise(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data") if isinstance(payload, dict) else {}
    data = data if isinstance(data, dict) else {}
    code_map = data.get("code_map") if isinstance(data.get("code_map"), dict) else {}
    code_results = code_map.get("results") if isinstance(code_map.get("results"), list) else []
    top_file = code_results[0].get("file") if code_results and isinstance(code_results[0], dict) else None
    noisy_code_files = [
        str(item.get("file"))
        for item in code_results[:5]
        if isinstance(item, dict) and generated_memory_path(item.get("file"))
    ]
    graph_map = data.get("graph_map") if isinstance(data.get("graph_map"), dict) else {}
    graph_results = graph_map.get("results") if isinstance(graph_map.get("results"), list) else []
    noisy_graph_nodes: list[str] = []
    noisy_graph_neighbors: list[str] = []
    for item in graph_results[:8]:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or item.get("id") or "")
        if generated_memory_path(name):
            noisy_graph_nodes.append(name)
        for neighbor in item.get("neighbors") or []:
            if isinstance(neighbor, dict) and generated_memory_path(neighbor.get("name") or neighbor.get("id")):
                noisy_graph_neighbors.append(str(neighbor.get("name") or neighbor.get("id")))
    return {
        "top_file": top_file,
        "top_file_ok": top_file == EXPECTED_CONTEXT_TOP_FILE,
        "noisy_code_files": noisy_code_files[:5],
        "noisy_graph_nodes": noisy_graph_nodes[:5],
        "noisy_graph_neighbors": noisy_graph_neighbors[:5],
    }


def agent_coach_known_monitor_noise(payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = payload.get("data") if isinstance(payload, dict) else {}
    data = data if isinstance(data, dict) else {}
    coach = data.get("coach") if isinstance(data.get("coach"), dict) else {}
    signals = coach.get("signals") if isinstance(coach.get("signals"), list) else []
    noisy: list[dict[str, Any]] = []
    for signal in signals:
        if not isinstance(signal, dict):
            continue
        tool = str(signal.get("tool") or "")
        args = signal.get("args") if isinstance(signal.get("args"), dict) else {}
        error = str(signal.get("error") or "")
        if tool == "router_failure_demo" and error in {"", "demo failure"}:
            noisy.append(signal)
            continue
        if tool == "graph_context_pack" and str(args.get("action", "")).strip("'\"") == "stats":
            noisy.append(signal)
            continue
        if (
            tool == "code_context_pack"
            and str(args.get("query", "")).strip("'\"") == "operator status reload behavior"
        ):
            noisy.append(signal)
            continue
        if tool == "session_audit" and str(args.get("action", "")).strip("'\"") == "trust":
            noisy.append(signal)
            continue
        if tool == "error_radar" and str(args.get("scope", "quick")).strip("'\"") in {"quick", "git"}:
            noisy.append(signal)
    return noisy


def build_report(mcp_url: str = DEFAULT_MCP_URL, timeout: int = 30) -> dict[str, Any]:
    trust = call_live_session_trust(mcp_url, timeout=timeout)
    live_radar = call_live_error_radar(mcp_url, timeout=timeout)
    code_context = call_live_code_context_query_alias(mcp_url, timeout=timeout)
    code_context_graph = call_live_code_context_graph_preference(mcp_url, timeout=timeout)
    code_context_graph_limit_one = call_live_code_context_graph_limit_one(mcp_url, timeout=timeout)
    agent_coach = call_live_agent_coach_monitor_filter(mcp_url, timeout=timeout)
    agent_coach_noise = agent_coach_known_monitor_noise(agent_coach)
    context_noise_probe = call_live_context_generated_noise_filter(mcp_url, timeout=timeout)
    context_noise = context_generated_noise(context_noise_probe)
    disk_runtime = disk_error_radar_runtime_count()
    live_runtime = dirty_tree_runtime_count(live_radar)
    live_radar_summary = radar_summary_present(live_radar)
    data = trust.get("data") if isinstance(trust, dict) else {}
    data = data if isinstance(data, dict) else {}
    trust_data = data.get("trust") if isinstance(data.get("trust"), dict) else {}
    signals = trust_data.get("signals") if isinstance(trust_data.get("signals"), dict) else {}
    identity = data.get("identity_surface") if isinstance(data.get("identity_surface"), dict) else None
    code_data = code_context.get("data") if isinstance(code_context, dict) else {}
    code_data = code_data if isinstance(code_data, dict) else {}
    code_map = code_data.get("code_map") if isinstance(code_data.get("code_map"), dict) else {}
    compressed_state = code_data.get("compressed_state") if isinstance(code_data.get("compressed_state"), dict) else {}
    graph_data = code_context_graph.get("data") if isinstance(code_context_graph, dict) else {}
    graph_data = graph_data if isinstance(graph_data, dict) else {}
    graph_code_map = graph_data.get("code_map") if isinstance(graph_data.get("code_map"), dict) else {}
    graph_results = graph_code_map.get("results") if isinstance(graph_code_map.get("results"), list) else []
    graph_top_file = graph_results[0].get("file") if graph_results and isinstance(graph_results[0], dict) else None
    limit_one_data = code_context_graph_limit_one.get("data") if isinstance(code_context_graph_limit_one, dict) else {}
    limit_one_data = limit_one_data if isinstance(limit_one_data, dict) else {}
    limit_one_code_map = limit_one_data.get("code_map") if isinstance(limit_one_data.get("code_map"), dict) else {}
    limit_one_results = limit_one_code_map.get("results") if isinstance(limit_one_code_map.get("results"), list) else []
    limit_one_top_file = limit_one_results[0].get("file") if limit_one_results and isinstance(limit_one_results[0], dict) else None

    checks = {
        "session_audit_identity_surface_field": identity is not None,
        "session_audit_identity_signal": "identity_surface_status" in signals,
        "code_context_query_alias": (
            code_context.get("success") is True
            and compressed_state.get("goal") == "operator status reload behavior"
            and str(code_map.get("query") or "") == "operator status reload behavior"
        ),
        "code_context_graph_preference": (
            code_context_graph.get("success") is True
            and graph_top_file == "ANA_MAX/dev_artifacts/scripts/ana_operator_status.py"
        ),
        "code_context_graph_limit_one": (
            code_context_graph_limit_one.get("success") is True
            and limit_one_top_file == "ANA_MAX/dev_artifacts/scripts/ana_operator_status.py"
        ),
        "error_radar_runtime_breakdown": (
            disk_runtime is None
            or live_radar.get("success") is True
            and live_runtime == disk_runtime
        ),
        "error_radar_summary": live_radar.get("success") is True and live_radar_summary,
        "agent_coach_monitor_noise_filter": agent_coach.get("success") is True and not agent_coach_noise,
        "context_generated_memory_noise_filter": (
            context_noise_probe.get("success") is True
            and context_noise.get("top_file_ok") is True
            and not context_noise.get("noisy_code_files")
            and not context_noise.get("noisy_graph_nodes")
            and not context_noise.get("noisy_graph_neighbors")
        ),
    }
    status = "PASS" if trust.get("success") is True and all(checks.values()) else "WARN"
    return {
        "schema": "ana.live_behavior_check.v1",
        "status": status,
        "checks": checks,
        "session_audit": {
            "call_success": trust.get("success") is True,
            "message": trust.get("message"),
            "trust_score": trust_data.get("score"),
            "identity_surface_status": identity.get("status") if identity else None,
            "identity_signal_status": signals.get("identity_surface_status"),
        },
        "error_radar": {
            "call_success": live_radar.get("success") is True,
            "live_runtime": live_runtime,
            "disk_runtime": disk_runtime,
            "summary_present": live_radar_summary,
        },
        "agent_coach": {
            "call_success": agent_coach.get("success") is True,
            "known_monitor_noise": agent_coach_noise[:5],
        },
        "context_generated_memory_noise": {
            "call_success": context_noise_probe.get("success") is True,
            **context_noise,
        },
        "code_context_pack": {
            "call_success": code_context.get("success") is True,
            "query": code_map.get("query"),
            "goal": compressed_state.get("goal"),
            "graph_preference_success": code_context_graph.get("success") is True,
            "graph_preference_top_file": graph_top_file,
            "graph_limit_one_success": code_context_graph_limit_one.get("success") is True,
            "graph_limit_one_top_file": limit_one_top_file,
        },
        "next_action": (
            "Live MCP exposes current checked behavior."
            if status == "PASS"
            else "Restart ANA MCP, then run Live Behavior, Reload Consistency, and Post-Reload Verify."
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check live MCP behavior freshness.")
    parser.add_argument("--mcp-url", default=DEFAULT_MCP_URL)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument(
        "--allow-warn",
        action="store_true",
        help="Return exit code 0 for WARN while still printing/reporting WARN evidence.",
    )
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_report(args.mcp_url, timeout=args.timeout)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        checks = report.get("checks") or {}
        print(
            "ANA Live Behavior: "
            f"{report['status']} "
            f"session_audit_identity_field={checks.get('session_audit_identity_surface_field')} "
            f"session_audit_identity_signal={checks.get('session_audit_identity_signal')} "
            f"code_context_query_alias={checks.get('code_context_query_alias')} "
            f"code_context_graph_preference={checks.get('code_context_graph_preference')} "
            f"code_context_graph_limit_one={checks.get('code_context_graph_limit_one')} "
            f"error_radar_runtime={checks.get('error_radar_runtime_breakdown')} "
            f"error_radar_summary={checks.get('error_radar_summary')} "
            f"agent_coach_monitor_noise={checks.get('agent_coach_monitor_noise_filter')} "
            f"context_generated_memory_noise={checks.get('context_generated_memory_noise_filter')}"
        )
        print(f"next_action={report['next_action']}")
    if report.get("status") == "PASS":
        return 0
    return 0 if args.allow_warn and report.get("status") == "WARN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
