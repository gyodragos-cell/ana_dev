"""Run a lab-safe ANA autonomy readiness pass.

This is not a general autonomous executor. It performs the observation,
routing, context, verification, audit, and optional checkpoint steps that make
the next human/Codex action less blind.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, Callable


DEFAULT_MCP_URL = "http://127.0.0.1:8766/mcp"
REPO_ROOT = Path(__file__).resolve().parents[3]
ANA_ROOT = REPO_ROOT / "ANA_MAX"
REPORT_DIR = ANA_ROOT / "dev_artifacts" / "reports"
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(ANA_ROOT) not in sys.path:
    sys.path.insert(0, str(ANA_ROOT))

import ana_live_reload_check
import ana_live_behavior_check
import ana_file_activity_snapshot
import ana_lab_state_summary
import ana_operator_status
import ana_review_batch_runner
from core.agent_trace_schema import make_span


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
        return {"success": False, "error": "non-JSON tool response", "text": text[:1200]}
    return parsed if isinstance(parsed, dict) else {"success": False, "error": "tool response is not an object", "data": parsed}


def call_tool(mcp_url: str, name: str, arguments: dict[str, Any] | None = None, timeout: int = 30) -> dict[str, Any]:
    return unwrap_tool_response(
        rpc(mcp_url, "tools/call", {"name": name, "arguments": arguments or {}}, timeout=timeout)
    )


def add_step(
    report: dict[str, Any],
    name: str,
    ok: bool,
    data: Any = None,
    error: str | None = None,
    optional: bool = False,
) -> None:
    status = "PASS" if ok else ("WARN" if optional else "FAIL")
    step = {
        "name": name,
        "status": status,
        "ok": bool(ok),
        "optional": optional,
        "data": data,
        "error": error,
    }
    report["steps"].append(step)
    add_trace_span(report, step)


def step_operation(name: str) -> str:
    if name in {"code_context_pack", "graph_context_pack", "foreground_ui_snapshot", "patch_advisor"}:
        return "context_pack"
    if name in {
        "health",
        "tools_list",
        "live_reload_marker",
        "live_tool_surface",
        "live_behavior",
        "context_maps",
        "tool_healthcheck",
        "error_radar",
        "file_activity_snapshot",
        "memory_archive_readiness",
        "review_batch_plan",
        "review_batch_runs",
    }:
        return "verification"
    if name == "session_audit":
        return "audit"
    if name == "session_checkpoint":
        return "checkpoint"
    return "tool_call"


def add_trace_span(report: dict[str, Any], step: dict[str, Any]) -> None:
    spans = report.get("trace_spans")
    if not isinstance(spans, list):
        return
    status_map = {"PASS": "ok", "WARN": "warn", "FAIL": "error"}
    name = str(step.get("name") or "unknown")
    span = make_span(
        run_id=str(report.get("run_id") or report.get("trace_id") or "ana-autonomy"),
        trace_id=str(report.get("trace_id") or report.get("run_id") or "ana-autonomy"),
        operation=step_operation(name),
        tool_name=name,
        status=status_map.get(str(step.get("status")), "warn"),
        risk_level="low",
        input_payload={"step": name, "optional": bool(step.get("optional"))},
        result_payload={
            "status": step.get("status"),
            "ok": step.get("ok"),
            "error": step.get("error"),
            "data": step.get("data"),
        },
        evidence={
            "step": name,
            "optional": bool(step.get("optional")),
            "has_error": bool(step.get("error")),
        },
    )
    spans.append(span)


def compact_tool_payload(name: str, payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data") if isinstance(payload, dict) else {}
    if not isinstance(data, dict):
        data = {}
    if name == "foreground_ui_snapshot":
        buttons = data.get("buttons", []) or []
        inputs = data.get("inputs", []) or []
        visible_text = data.get("visible_text", []) or []
        detected_errors = data.get("detected_errors", []) or []
        return {
            "message": payload.get("message"),
            "app": data.get("active_app") or data.get("app"),
            "title": data.get("title"),
            "buttons": len(buttons),
            "inputs": len(inputs),
            "visible_text": len(visible_text),
            "detected_errors": len(detected_errors),
            "fallback": data.get("fallback"),
            "reason": data.get("reason"),
        }
    if name == "code_context_pack":
        return {
            "message": payload.get("message"),
            "code_results": len(data.get("code_map", {}).get("results", []) or []),
            "graph_results": len(data.get("graph_map", {}).get("results", []) or []),
            "evidence": data.get("compressed_state", {}).get("evidence", []),
        }
    if name == "graph_context_pack":
        stats = data.get("stats", {})
        return {
            "message": payload.get("message"),
            "nodes": stats.get("nodes"),
            "edges": stats.get("edges"),
            "results": len(data.get("results", []) or []),
            "updated_at": data.get("updated_at"),
        }
    if name == "tool_router":
        return {
            "message": payload.get("message"),
            "mode": data.get("mode"),
            "recommended_tools": data.get("recommended_tools", [])[:8],
        }
    if name == "agent_coach":
        return {
            "message": payload.get("message"),
            "primary_tool": data.get("primary_tool"),
            "tool_stack": data.get("tool_stack", [])[:8],
            "next_action": data.get("next_action"),
        }
    if name == "tool_healthcheck":
        return {
            "message": payload.get("message"),
            "ok": data.get("ok"),
            "failed": data.get("failed"),
            "checked": data.get("checked"),
        }
    if name == "error_radar":
        findings = data.get("findings", []) or []
        return {
            "message": payload.get("message"),
            "count": data.get("count"),
            "findings": findings[:5],
        }
    if name == "session_audit":
        trust = data.get("trust", {})
        return {
            "message": payload.get("message"),
            "score": trust.get("score"),
            "signals": trust.get("signals"),
            "trace": data.get("trace"),
        }
    if name == "file_activity_snapshot":
        diff = data.get("diff", {})
        return {
            "baseline_available": data.get("baseline_available"),
            "files_scanned": data.get("files_scanned"),
            "created": diff.get("created"),
            "deleted": diff.get("deleted"),
            "modified": diff.get("modified"),
            "privacy": data.get("privacy"),
            "next_action": data.get("next_action"),
        }
    if name == "memory_archive_readiness":
        readiness = data if data else payload
        return {
            "available": readiness.get("available"),
            "status": readiness.get("status"),
            "total_moves": readiness.get("total_moves"),
            "current_archive_candidates": readiness.get("current_archive_candidates"),
            "candidate_delta": readiness.get("candidate_delta"),
            "failures": readiness.get("failures"),
            "warnings": readiness.get("warnings"),
        }
    if name == "live_tool_surface":
        surface = data if data else payload
        return {
            "status": surface.get("status"),
            "live_count": surface.get("live_count"),
            "manifest_count": surface.get("manifest_count"),
            "extra_live": len(surface.get("extra_live") or []),
            "missing_live": len(surface.get("missing_live") or []),
        }
    if name == "live_behavior":
        behavior = data if data else payload
        checks = behavior.get("checks") if isinstance(behavior, dict) else {}
        checks = checks if isinstance(checks, dict) else {}
        failed_checks = [key for key, value in checks.items() if value is not True]
        passed = sum(1 for value in checks.values() if value is True)
        total = len(checks)
        message = f"live_behavior {passed}/{total} checks"
        if failed_checks:
            message += f" failed={','.join(failed_checks[:5])}"
        return {
            "status": behavior.get("status"),
            "checks_passed": passed,
            "checks_total": total,
            "failed_checks": failed_checks[:8],
            "message": message,
        }
    if name == "context_maps":
        maps = data if data else payload
        code = maps.get("code_map") if isinstance(maps, dict) else {}
        graph = maps.get("graph_map") if isinstance(maps, dict) else {}
        code = code if isinstance(code, dict) else {}
        graph = graph if isinstance(graph, dict) else {}
        stale_sources = []
        if code.get("status") != "PASS" and code.get("stale_source"):
            stale_sources.append(f"code={code.get('stale_source')}")
        if graph.get("status") != "PASS" and graph.get("stale_source"):
            stale_sources.append(f"graph={graph.get('stale_source')}")
        return {
            "status": maps.get("status"),
            "code_status": code.get("status"),
            "code_summaries": code.get("summaries"),
            "graph_status": graph.get("status"),
            "graph_nodes": graph.get("nodes"),
            "graph_edges": graph.get("edges"),
            "stale_sources": stale_sources[:4],
            "message": ana_operator_status.format_context_maps(maps),
        }
    if name == "patch_advisor":
        inputs = payload.get("inputs", {}) if isinstance(payload, dict) else {}
        recommendations = payload.get("recommendations", []) if isinstance(payload, dict) else []
        first = recommendations[0] if recommendations else {}
        dirty_tree = payload.get("dirty_tree", {}) if isinstance(payload, dict) else {}
        review_batches = dirty_tree.get("review_batches", []) if isinstance(dirty_tree, dict) else []
        if not isinstance(review_batches, list):
            review_batches = []
        first_batch = review_batches[0] if review_batches and isinstance(review_batches[0], dict) else {}
        return {
            "mode": payload.get("mode"),
            "finding_count": inputs.get("finding_count"),
            "noise_filtered": inputs.get("noise_filtered"),
            "dirty_tree_available": inputs.get("dirty_tree_available"),
            "dirty_tree_total": inputs.get("dirty_tree_total"),
            "review_batches": [
                {
                    "category": batch.get("category"),
                    "count": batch.get("count"),
                    "tracked": batch.get("tracked"),
                    "untracked": batch.get("untracked"),
                }
                for batch in review_batches[:6]
                if isinstance(batch, dict)
            ],
            "first_review_batch": first_batch.get("category"),
            "first_review_next_step": first_batch.get("next_step"),
            "first_review_commands": (first_batch.get("suggested_commands") or [])[:3],
            "blast_radius_available": inputs.get("blast_radius_available"),
            "blast_radius_affected": inputs.get("blast_radius_affected"),
            "top_recommendation": first.get("title"),
            "next_step": first.get("next_step"),
        }
    if name == "review_batch_plan":
        commands = payload.get("commands", []) if isinstance(payload, dict) else []
        batches = payload.get("batches", []) if isinstance(payload, dict) else []
        if not isinstance(commands, list):
            commands = []
        if not isinstance(batches, list):
            batches = []
        first_command = commands[0] if commands and isinstance(commands[0], dict) else {}
        return {
            "status": payload.get("status"),
            "mode": payload.get("mode"),
            "category": payload.get("category"),
            "command_count": len(commands),
            "batch_count": len(batches),
            "batches": [batch.get("category") for batch in batches[:8] if isinstance(batch, dict)],
            "first_command": first_command.get("command"),
            "policy": payload.get("policy"),
        }
    if name == "review_batch_runs":
        planned = payload.get("planned_categories", []) if isinstance(payload, dict) else []
        passed = payload.get("passed_categories", []) if isinstance(payload, dict) else []
        missing = payload.get("missing_categories", []) if isinstance(payload, dict) else []
        failing = payload.get("failing_categories", []) if isinstance(payload, dict) else []
        stale = payload.get("stale_categories", []) if isinstance(payload, dict) else []
        fresh = payload.get("fresh_categories", []) if isinstance(payload, dict) else []
        return {
            "status": payload.get("status"),
            "planned_count": len(planned) if isinstance(planned, list) else 0,
            "passed_count": len(passed) if isinstance(passed, list) else 0,
            "fresh_count": len(fresh) if isinstance(fresh, list) else 0,
            "missing_categories": missing if isinstance(missing, list) else [],
            "failing_categories": failing if isinstance(failing, list) else [],
            "stale_categories": stale if isinstance(stale, list) else [],
            "categories": passed[:8] if isinstance(passed, list) else [],
            "policy": payload.get("policy"),
        }
    if name == "session_checkpoint":
        return {
            "message": payload.get("message"),
            "path": data.get("path") or data.get("file"),
            "memory_topic": data.get("memory_topic"),
        }
    return {"message": payload.get("message"), "success": payload.get("success")}


def run_patch_advisor(mcp_url: str, timeout: int = 30) -> dict[str, Any]:
    script = SCRIPT_DIR / "ana_patch_advisor.py"
    spec = importlib.util.spec_from_file_location("ana_patch_advisor_for_autonomy", script)
    if not spec or not spec.loader:
        return {"success": False, "error": f"Script not found: {script}"}
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    report = module.build_report(mcp_url, timeout=timeout)
    return {"success": True, **report}


def run_file_activity_snapshot() -> dict[str, Any]:
    report, _baseline = ana_file_activity_snapshot.build_report(REPO_ROOT, sample_limit=8)
    return {"success": True, "data": report, "message": report.get("next_action")}


def run_memory_archive_readiness(mcp_url: str) -> dict[str, Any]:
    lab_state = ana_lab_state_summary.build_summary(mcp_url)
    readiness = ((lab_state.get("memory_hygiene") or {}).get("archive_readiness") or {})
    return {
        "success": True,
        "data": readiness,
        "message": f"archive_readiness={readiness.get('status')}",
    }


def run_review_batch_plan() -> dict[str, Any]:
    report = ana_review_batch_runner.build_report(all_batches=True, execute=False, limit=12)
    return {"success": report.get("status") == "DRY_RUN", **report}


def run_review_batch_runs() -> dict[str, Any]:
    plan = ana_review_batch_runner.build_report(all_batches=True, execute=False, limit=12)
    planned_categories = [
        str(batch.get("category"))
        for batch in plan.get("batches", [])
        if isinstance(batch, dict) and batch.get("category")
    ]
    ledger = ana_operator_status.recent_review_batch_runs()
    categories = ledger.get("categories") if isinstance(ledger, dict) else {}
    categories = categories if isinstance(categories, dict) else {}
    passed_categories: list[str] = []
    fresh_categories: list[str] = []
    missing_categories: list[str] = []
    failing_categories: list[str] = []
    stale_categories: list[str] = []

    for category in planned_categories:
        summary = categories.get(category)
        if not isinstance(summary, dict):
            missing_categories.append(category)
            continue
        if summary.get("status") == "PASS" and not summary.get("failed") and not summary.get("timeout"):
            if summary.get("fresh") is False:
                stale_categories.append(category)
                continue
            passed_categories.append(category)
            fresh_categories.append(category)
        else:
            failing_categories.append(category)

    status = (
        "PASS"
        if planned_categories and not missing_categories and not failing_categories and not stale_categories
        else "WARN"
    )
    return {
        "success": status == "PASS",
        "status": status,
        "planned_categories": planned_categories,
        "passed_categories": passed_categories,
        "fresh_categories": fresh_categories,
        "missing_categories": missing_categories,
        "failing_categories": failing_categories,
        "stale_categories": stale_categories,
        "ledger": ledger,
        "policy": {
            "read_only": True,
            "executes_commands": False,
            "source": "review_batch_runner reports",
            "freshness_checked": True,
        },
    }


def add_local_report_step(
    report: dict[str, Any],
    name: str,
    payload: dict[str, Any],
    predicate: Callable[[dict[str, Any]], bool] | None = None,
    optional: bool = True,
) -> dict[str, Any]:
    ok = bool(payload.get("success", True))
    if ok and predicate:
        ok = bool(predicate(payload))
    add_step(report, name, ok, compact_tool_payload(name, payload), error=payload.get("error"), optional=optional)
    return payload


def safe_tool_call(
    report: dict[str, Any],
    mcp_url: str,
    name: str,
    arguments: dict[str, Any],
    predicate: Callable[[dict[str, Any]], bool] | None = None,
    optional: bool = False,
    timeout: int = 30,
) -> dict[str, Any]:
    try:
        payload = call_tool(mcp_url, name, arguments, timeout=timeout)
        if name == "foreground_ui_snapshot" and not foreground_snapshot_has_context(payload):
            time.sleep(0.5)
            retry_payload = call_tool(mcp_url, name, arguments, timeout=timeout)
            if foreground_snapshot_has_context(retry_payload) or not payload.get("success"):
                payload = retry_payload
        ok = bool(payload.get("success"))
        if ok and predicate:
            ok = bool(predicate(payload))
        compact = compact_tool_payload(name, payload)
        add_step(report, name, ok, compact, optional=optional)
        return payload
    except Exception as exc:
        add_step(report, name, False, error=str(exc), optional=optional)
        return {"success": False, "error": str(exc)}


def foreground_snapshot_has_context(payload: dict[str, Any]) -> bool:
    if not isinstance(payload, dict) or not payload.get("success"):
        return False
    data = payload.get("data")
    if not isinstance(data, dict):
        return False
    return bool(data.get("active_app") or data.get("app") or data.get("title") or data.get("hwnd"))


def build_next_action(report: dict[str, Any]) -> str:
    live_reload = report.get("signals", {}).get("live_reload", {})
    if isinstance(live_reload, dict) and live_reload.get("status") == "WARN":
        return str(live_reload.get("next_action") or "Restart/reload ANA MCP server, then rerun Autonomy Pass.")
    tool_surface = report.get("signals", {}).get("live_tool_surface", {})
    if isinstance(tool_surface, dict) and tool_surface.get("status") == "WARN":
        return "Restart ANA MCP so live tools/list matches the local permission manifest, then rerun Autonomy Pass."
    live_behavior = report.get("signals", {}).get("live_behavior", {})
    if isinstance(live_behavior, dict) and live_behavior.get("status") == "WARN":
        return "Restart ANA MCP, then run Live Behavior, Reload Consistency, Post-Reload Verify, and Autonomy Pass."
    context_maps = report.get("signals", {}).get("context_maps", {})
    if isinstance(context_maps, dict) and context_maps.get("status") == "WARN":
        return f"Run {ana_operator_status.CONTEXT_MAP_REFRESH_COMMAND}, then rerun Autonomy Pass."
    if report.get("status") == "FAIL":
        return "Fix failed health/tool steps first, then rerun Autonomy Pass."
    if report.get("status") == "WARN":
        return "Review warnings, then run the smallest recommended tool before editing."
    review_message = review_batch_verified_next_action(report)
    if review_message:
        return review_message
    coach = report.get("signals", {}).get("coach", {})
    if isinstance(coach, dict) and coach.get("next_action"):
        return str(coach["next_action"])
    return "Proceed with one scoped action, then verify with Nucleus Smoke or Autonomy Pass."


def review_batch_verified_next_action(report: dict[str, Any]) -> str:
    review_runs = report.get("signals", {}).get("review_batch_runs", {})
    if not isinstance(review_runs, dict) or review_runs.get("status") != "PASS":
        return ""
    planned = review_runs.get("planned_count")
    passed = review_runs.get("passed_count")
    missing = review_runs.get("missing_categories")
    failing = review_runs.get("failing_categories")
    stale = review_runs.get("stale_categories")
    if not isinstance(planned, int) or not isinstance(passed, int) or planned <= 0:
        return ""
    if passed != planned or missing or failing or stale:
        return ""
    return (
        f"Continue with one new scoped lab action; review batches verified {passed}/{planned}. "
        "Do not rerun them unless new changes land."
    )


def finalize(report: dict[str, Any]) -> None:
    statuses = [step["status"] for step in report["steps"]]
    summary = {
        "pass": statuses.count("PASS"),
        "warn": statuses.count("WARN"),
        "fail": statuses.count("FAIL"),
        "total": len(statuses),
    }
    report["summary"] = summary
    report["status"] = "FAIL" if summary["fail"] else ("WARN" if summary["warn"] else "PASS")
    trust = report.get("signals", {}).get("trust_score")
    if isinstance(trust, int) and trust < 70 and report["status"] == "PASS":
        report["status"] = "WARN"
        summary["warn"] += 1
    report["next_action"] = build_next_action(report)


def run_autonomy_pass(mcp_url: str, goal: str, checkpoint: bool = False, timeout: int = 30) -> dict[str, Any]:
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    run_id = f"ana-autonomy-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    report: dict[str, Any] = {
        "schema": "ana.autonomy_runner.v1",
        "generated_at": generated_at,
        "run_id": run_id,
        "trace_id": run_id,
        "goal": goal,
        "mcp_url": mcp_url,
        "mode": "observe_route_verify",
        "status": "FAIL",
        "steps": [],
        "trace_spans": [],
        "signals": {},
    }

    try:
        health = json_request(health_url(mcp_url), timeout=timeout)
        ok = bool(health.get("status") == "online" and health.get("mcp_ready"))
        add_step(report, "health", ok, {
            "status": health.get("status"),
            "mcp_ready": health.get("mcp_ready"),
            "tools_count": health.get("tools_count"),
        })
        report["signals"]["tools_count"] = health.get("tools_count")
    except Exception as exc:
        add_step(report, "health", False, error=str(exc))
        finalize(report)
        return report

    try:
        tools_res = rpc(mcp_url, "tools/list", timeout=timeout)
        tools = tools_res.get("result", {}).get("tools", [])
        names = sorted(tool.get("name") for tool in tools if isinstance(tool, dict) and tool.get("name"))
        required = [
            "foreground_ui_snapshot",
            "code_context_pack",
            "graph_context_pack",
            "tool_router",
            "agent_coach",
            "tool_healthcheck",
            "error_radar",
            "session_audit",
        ]
        if checkpoint:
            required.append("session_checkpoint")
        missing = [name for name in required if name not in names]
        add_step(report, "tools_list", not missing, {"count": len(names), "missing_required": missing})
        report["signals"]["available_tools"] = len(names)
    except Exception as exc:
        add_step(report, "tools_list", False, error=str(exc))

    try:
        live_reload = ana_live_reload_check.check_live_reload(mcp_url, timeout=min(timeout, 20))
        report["signals"]["live_reload"] = {
            "status": live_reload.get("status"),
            "marker": live_reload.get("marker"),
            "has_marker": live_reload.get("has_marker"),
            "next_action": live_reload.get("next_action"),
        }
        add_step(
            report,
            "live_reload_marker",
            live_reload.get("status") == "PASS",
            report["signals"]["live_reload"],
            optional=True,
        )
    except Exception as exc:
        add_step(report, "live_reload_marker", False, error=str(exc), optional=True)

    try:
        tool_surface = ana_operator_status.live_tool_surface(mcp_url)
        report["signals"]["live_tool_surface"] = compact_tool_payload("live_tool_surface", tool_surface)
        add_step(
            report,
            "live_tool_surface",
            tool_surface.get("status") == "PASS",
            report["signals"]["live_tool_surface"],
            optional=True,
        )
    except Exception as exc:
        add_step(report, "live_tool_surface", False, error=str(exc), optional=True)

    try:
        live_behavior = ana_live_behavior_check.build_report(mcp_url, timeout=min(timeout, 20))
        report["signals"]["live_behavior"] = compact_tool_payload("live_behavior", live_behavior)
        add_step(
            report,
            "live_behavior",
            live_behavior.get("status") == "PASS",
            report["signals"]["live_behavior"],
            optional=True,
        )
    except Exception as exc:
        add_step(report, "live_behavior", False, error=str(exc), optional=True)

    try:
        context_maps = ana_operator_status.context_maps_status()
        report["signals"]["context_maps"] = compact_tool_payload("context_maps", context_maps)
        add_step(
            report,
            "context_maps",
            context_maps.get("status") == "PASS",
            report["signals"]["context_maps"],
            optional=True,
        )
    except Exception as exc:
        add_step(report, "context_maps", False, error=str(exc), optional=True)

    file_activity = add_local_report_step(
        report,
        "file_activity_snapshot",
        run_file_activity_snapshot(),
        predicate=lambda p: p.get("data", {}).get("privacy", {}).get("content_read") is False,
        optional=True,
    )
    memory_readiness = add_local_report_step(
        report,
        "memory_archive_readiness",
        run_memory_archive_readiness(mcp_url),
        predicate=lambda p: p.get("data", {}).get("status") in {"PASS", "STALE"},
        optional=True,
    )

    safe_tool_call(
        report,
        mcp_url,
        "foreground_ui_snapshot",
        {"include_text": True, "max_elements": "20"},
        optional=True,
        timeout=timeout,
    )
    code_pack = safe_tool_call(
        report,
        mcp_url,
        "code_context_pack",
        {"task": goal, "limit": 5, "include_graph": True},
        predicate=lambda p: bool(p.get("data", {}).get("compressed_state")),
        timeout=timeout,
    )
    graph_pack = safe_tool_call(
        report,
        mcp_url,
        "graph_context_pack",
        {"action": "query", "query": goal, "limit": 5},
        predicate=lambda p: bool(p.get("data")),
        optional=True,
        timeout=timeout,
    )
    router = safe_tool_call(
        report,
        mcp_url,
        "tool_router",
        {"task": goal, "max_tools": 6},
        predicate=lambda p: bool(p.get("data", {}).get("recommended_tools")),
        timeout=timeout,
    )
    coach = safe_tool_call(
        report,
        mcp_url,
        "agent_coach",
        {"action": "recommend", "task": goal, "max_tools": 6, "include_prompt": False},
        predicate=lambda p: bool(p.get("data", {}).get("primary_tool")),
        timeout=timeout,
    )
    healthcheck = safe_tool_call(
        report,
        mcp_url,
        "tool_healthcheck",
        {"scope": "safe"},
        predicate=lambda p: int(p.get("data", {}).get("failed") or 0) == 0,
        timeout=timeout,
    )
    radar = safe_tool_call(
        report,
        mcp_url,
        "error_radar",
        {"limit": 20},
        optional=True,
        timeout=timeout,
    )
    patch_advisor = add_local_report_step(
        report,
        "patch_advisor",
        run_patch_advisor(mcp_url, timeout=timeout),
        predicate=lambda p: p.get("mode") == "suggest_only" and p.get("policy", {}).get("writes_files") is False,
        optional=True,
    )
    review_plan = add_local_report_step(
        report,
        "review_batch_plan",
        run_review_batch_plan(),
        predicate=lambda p: p.get("mode") == "dry_run"
        and p.get("policy", {}).get("all_batches_plan_only") is True
        and p.get("policy", {}).get("destructive_actions") is False,
        optional=True,
    )
    review_runs = add_local_report_step(
        report,
        "review_batch_runs",
        run_review_batch_runs(),
        predicate=lambda p: p.get("status") == "PASS"
        and p.get("policy", {}).get("read_only") is True
        and p.get("policy", {}).get("executes_commands") is False,
        optional=True,
    )
    audit = safe_tool_call(
        report,
        mcp_url,
        "session_audit",
        {"action": "trust", "hours": 1, "limit": 120},
        predicate=lambda p: int(p.get("data", {}).get("trust", {}).get("score") or 0) >= 50,
        timeout=timeout,
    )

    report["signals"]["router"] = compact_tool_payload("tool_router", router)
    report["signals"]["coach"] = compact_tool_payload("agent_coach", coach)
    report["signals"]["code_context"] = compact_tool_payload("code_context_pack", code_pack)
    report["signals"]["graph_context"] = compact_tool_payload("graph_context_pack", graph_pack)
    report["signals"]["tool_healthcheck"] = compact_tool_payload("tool_healthcheck", healthcheck)
    report["signals"]["error_radar"] = compact_tool_payload("error_radar", radar)
    report["signals"]["patch_advisor"] = compact_tool_payload("patch_advisor", patch_advisor)
    report["signals"]["review_batch_plan"] = compact_tool_payload("review_batch_plan", review_plan)
    report["signals"]["review_batch_runs"] = compact_tool_payload("review_batch_runs", review_runs)
    report["signals"]["file_activity"] = compact_tool_payload("file_activity_snapshot", file_activity)
    report["signals"]["memory_archive_readiness"] = compact_tool_payload("memory_archive_readiness", memory_readiness)
    trust_score = audit.get("data", {}).get("trust", {}).get("score") if isinstance(audit.get("data"), dict) else None
    if isinstance(trust_score, int):
        report["signals"]["trust_score"] = trust_score

    if checkpoint:
        safe_tool_call(
            report,
            mcp_url,
            "session_checkpoint",
            {
                "title": "Autonomy Pass checkpoint",
                "summary": "ANA Autonomy Pass ran health, observe, route, context, verify, audit, and checkpoint steps.",
                "current_goal": goal,
                "next_steps": "Use the recommended primary tool for one scoped action, then verify again.",
                "files_changed": "ANA_MAX/dev_artifacts/scripts/ana_autonomy_runner.py; vscode_extension/extension.js; vscode_extension/package.json; docs",
                "validation": "Autonomy Pass report should show health/tools/context/router/coach/healthcheck/audit status.",
                "risks": "This runner is read-only except the optional checkpoint write; deep instrumentation remains lab-only.",
                "sync_status": "Mother lab only; public release pending.",
                "include_git": True,
            },
            optional=True,
            timeout=timeout,
        )

    finalize(report)
    return report


def write_report(report: dict[str, Any]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"autonomy_runner_{stamp}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def print_human(report: dict[str, Any], report_path: Path | None = None) -> None:
    trust = report.get("signals", {}).get("trust_score")
    trust_text = f" trust={trust}%" if isinstance(trust, int) else ""
    trace_spans = report.get("trace_spans") if isinstance(report.get("trace_spans"), list) else []
    steps = report.get("steps") if isinstance(report.get("steps"), list) else []
    trace_text = f" trace={len(trace_spans)}/{len(steps)} aligned={len(trace_spans) == len(steps)}" if trace_spans else ""
    print(
        f"ANA Autonomy: {report['status']} "
        f"({report['summary']['pass']} pass / {report['summary']['warn']} warn / {report['summary']['fail']} fail){trust_text}{trace_text}"
    )
    for step in report["steps"]:
        detail = step.get("error") or (step.get("data") or {}).get("message") or ""
        print(f"[{step['status']}] {step['name']} {detail}".rstrip())
    print(f"next_action={report.get('next_action')}")
    if report_path:
        print(f"report={report_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run ANA MAX lab-safe autonomy readiness pass.")
    parser.add_argument("--mcp-url", default=DEFAULT_MCP_URL)
    parser.add_argument("--goal", default="ANA lab autonomous readiness pass")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--checkpoint", action="store_true", help="Write a session_checkpoint after the pass.")
    parser.add_argument("--json", action="store_true", help="Print JSON only.")
    parser.add_argument("--no-write", action="store_true", help="Do not write the report file.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = run_autonomy_pass(args.mcp_url, args.goal, checkpoint=args.checkpoint, timeout=args.timeout)
    report_path = None if args.no_write else write_report(report)
    if args.json:
        print(json.dumps({**report, "report": str(report_path) if report_path else None}, indent=2, ensure_ascii=False))
    else:
        print_human(report, report_path)
    return 0 if report["status"] in {"PASS", "WARN"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
