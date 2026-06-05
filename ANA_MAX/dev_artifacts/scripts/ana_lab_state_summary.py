"""Produce a compact ANA lab state summary for handoff."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from typing import Any
import urllib.request

import ana_file_activity_snapshot
import ana_identity_surface_check
import ana_memory_archive
import ana_live_behavior_check
import ana_live_reload_check
import ana_memory_hygiene
import ana_operator_status
import ana_trace_report


DEFAULT_MCP_URL = "http://127.0.0.1:8766/mcp"
REPO_ROOT = Path(__file__).resolve().parents[3]
ANA_ROOT = REPO_ROOT / "ANA_MAX"
REPORT_DIR = ANA_ROOT / "dev_artifacts" / "reports"


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def health_url(mcp_url: str) -> str:
    return mcp_url.rstrip("/").removesuffix("/mcp") + "/health"


def get_json(url: str, timeout: int = 10) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def git_dirty_summary() -> dict[str, Any]:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
    )
    lines = [line for line in result.stdout.splitlines() if line.strip()] if result.returncode == 0 else []
    tracked = sum(1 for line in lines if not line.startswith("??"))
    untracked = sum(1 for line in lines if line.startswith("??"))
    return {
        "ok": result.returncode == 0,
        "changed_paths": len(lines),
        "tracked": tracked,
        "untracked": untracked,
        "sample": [line[3:].replace("\\", "/") if len(line) > 3 else line for line in lines[:8]],
    }


def package_artifacts() -> dict[str, Any]:
    package_path = REPO_ROOT / "vscode_extension" / "package.json"
    try:
        package = json.loads(package_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "version": "",
            "copy_vsix": "",
            "copy_vsix_exists": False,
            "main_vsix": "",
            "main_vsix_exists": False,
            "error": "package_json_unavailable",
        }
    version = str(package.get("version") or "")
    copy_vsix = REPO_ROOT / "vscode_extension" / f"ana-codex-cockpit-{version}.vsix"
    main_vsix = ANA_ROOT / f"ana-max-codex-cockpit-{version}.vsix"
    return {
        "version": version,
        "copy_vsix": str(copy_vsix),
        "copy_vsix_exists": copy_vsix.exists(),
        "main_vsix": str(main_vsix),
        "main_vsix_exists": main_vsix.exists(),
    }


def latest_trace_summary() -> dict[str, Any]:
    source = ana_trace_report.latest_autonomy_report(REPORT_DIR)
    if not source:
        return {"available": False, "reason": "no_autonomy_report"}
    try:
        report = ana_trace_report.summarize_report(source)
    except Exception as exc:
        return {"available": False, "reason": str(exc), "source_report": str(source)}
    return {
        "available": True,
        "source_report": str(source),
        "ok": report.get("ok"),
        "steps": report.get("steps"),
        "spans": report.get("spans"),
        "aligned": report.get("aligned"),
        "operations": report.get("operations", {}),
    }


def latest_memory_archive_readiness() -> dict[str, Any]:
    reports = sorted(REPORT_DIR.glob("memory_archive_*.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    for source in reports:
        try:
            loaded = json.loads(source.read_text(encoding="utf-8"))
        except Exception:
            continue
        if loaded.get("schema") != "ana.memory_archive.v1" or loaded.get("mode") != "dry_run":
            continue
        try:
            readiness = ana_memory_archive.check_archive_readiness(loaded)
        except Exception as exc:
            return {
                "available": True,
                "status": "FAIL",
                "source_report": str(source),
                "reason": str(exc),
            }
        return {
            "available": True,
            "status": readiness.get("status"),
            "source_report": str(source),
            "total_moves": readiness.get("total_moves"),
            "archive_root": readiness.get("archive_root"),
            "archive_date_basis": readiness.get("archive_date_basis", "utc"),
            "summary": readiness.get("summary", {}),
            "failures": len(readiness.get("failures") or []),
            "warnings": len(readiness.get("warnings") or []),
        }
    return {"available": False, "reason": "no_dry_run_archive_report"}


def reconcile_archive_readiness(memory: dict[str, Any], readiness: dict[str, Any]) -> dict[str, Any]:
    reconciled = dict(readiness or {})
    candidates = memory.get("archive_candidates") if isinstance(memory, dict) else None
    moves = reconciled.get("total_moves")
    if (
        reconciled.get("status") == "PASS"
        and isinstance(candidates, int)
        and isinstance(moves, int)
        and candidates != moves
    ):
        reconciled["status"] = "STALE"
        reconciled["stale_reason"] = "archive_candidate_count_changed"
        reconciled["current_archive_candidates"] = candidates
        reconciled["candidate_delta"] = candidates - moves
    return reconciled


def build_summary(mcp_url: str = DEFAULT_MCP_URL, keep_latest: int = ana_memory_hygiene.DEFAULT_KEEP_LATEST) -> dict[str, Any]:
    health = {}
    try:
        health = get_json(health_url(mcp_url), timeout=10)
    except Exception as exc:
        health = {"status": "error", "error": str(exc)}
    live_reload = ana_live_reload_check.check_live_reload(mcp_url, timeout=20)
    memory = ana_memory_hygiene.build_report(keep_latest=keep_latest, include_plan=True)
    archive_readiness = reconcile_archive_readiness(memory, latest_memory_archive_readiness())
    dirty = git_dirty_summary()
    trace = latest_trace_summary()
    file_activity, _baseline = ana_file_activity_snapshot.build_report(REPO_ROOT, sample_limit=8)
    tool_surface = ana_operator_status.live_tool_surface(mcp_url)
    identity_surface = ana_identity_surface_check.build_report()
    live_behavior = ana_live_behavior_check.build_report(mcp_url, timeout=60)
    context_maps = ana_operator_status.context_maps_status()
    reload_reasons: list[str] = []
    if not live_reload.get("has_marker"):
        reload_reasons.append("missing_reload_marker")
    if tool_surface.get("status") == "WARN":
        reload_reasons.append("live_tool_surface_drift")
    if live_behavior.get("status") == "WARN":
        reload_reasons.append("live_behavior_stale")
    reload_or_surface_stale = bool(reload_reasons)
    identity_problem = identity_surface.get("status") != "PASS"
    maps_need_refresh = ana_operator_status.context_maps_need_refresh(context_maps)
    return {
        "schema": "ana.lab_state_summary.v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "package": package_artifacts(),
        "mcp": {
            "status": health.get("status"),
            "mcp_ready": health.get("mcp_ready"),
            "tools_count": health.get("tools_count"),
            "version": health.get("version"),
        },
        "live_reload": {
            "status": live_reload.get("status"),
            "marker": live_reload.get("marker"),
            "has_marker": live_reload.get("has_marker"),
            "next_action": live_reload.get("next_action"),
        },
        "reload_readiness": {
            "status": "WARN" if reload_or_surface_stale else "PASS",
            "reload_needed": reload_or_surface_stale,
            "reasons": reload_reasons,
        },
        "memory_hygiene": {
            "checkpoints": memory.get("checkpoints", {}).get("count"),
            "rem_sleep_reports": memory.get("rem_sleep_reports", {}).get("count"),
            "archive_candidates": memory.get("archive_candidates"),
            "archive_plan_moves": memory.get("archive_plan", {}).get("total_moves"),
            "archive_root": memory.get("archive_plan", {}).get("archive_root"),
            "archive_date_basis": memory.get("archive_plan", {}).get("archive_date_basis", "utc"),
            "archive_readiness": archive_readiness,
        },
        "trace": trace,
        "tool_surface": tool_surface,
        "live_behavior": live_behavior,
        "context_maps": context_maps,
        "identity_surface": {
            "status": identity_surface.get("status"),
            "files_checked": identity_surface.get("files_checked"),
            "violations": len(identity_surface.get("violations") or []),
            "missing_required": len(identity_surface.get("missing_required") or []),
        },
        "file_activity": {
            "baseline_available": file_activity.get("baseline_available"),
            "files_scanned": file_activity.get("files_scanned"),
            "diff": file_activity.get("diff"),
            "privacy": file_activity.get("privacy"),
        },
        "git": dirty,
        "recommended_next_step": (
            "Fix active identity surface, then rerun Lab State Summary."
            if identity_problem
            else (
                build_reload_next_step(reload_reasons)
                if reload_or_surface_stale
                else (
                    f"Run {ana_operator_status.CONTEXT_MAP_REFRESH_COMMAND}, then rerun Lab State Summary."
                    if maps_need_refresh
                    else "Run Nucleus Smoke, then continue with one scoped action."
                )
            )
        ),
    }


def build_reload_next_step(reload_reasons: list[str]) -> str:
    if reload_reasons == ["live_behavior_stale"]:
        return "Restart ANA MCP, then run Live Behavior, Reload Consistency, and Post-Reload Verify."
    if reload_reasons == ["live_tool_surface_drift"]:
        return "Restart ANA MCP so live tools/list matches the local permission manifest, then rerun Lab State Summary."
    if "missing_reload_marker" in reload_reasons:
        return "Reload/restart ANA MCP server, then rerun post-reload verify."
    return "Restart ANA MCP, then rerun post-reload verify."


def write_report(report: dict[str, Any]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"lab_state_summary_{stamp}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize current ANA lab state.")
    parser.add_argument("--mcp-url", default=DEFAULT_MCP_URL)
    parser.add_argument("--keep-latest", type=int, default=ana_memory_hygiene.DEFAULT_KEEP_LATEST)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-write", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_summary(args.mcp_url, keep_latest=max(1, args.keep_latest))
    path = None if args.no_write else write_report(report)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(
            "ANA Lab State: "
            f"mcp_ready={report['mcp'].get('mcp_ready')} "
            f"tools={report['mcp'].get('tools_count')} "
            f"package={ana_operator_status.format_package_artifacts(report.get('package') or {})} "
            f"reload={report['reload_readiness'].get('status')} "
            f"tool_surface={ana_operator_status.format_tool_surface(report.get('tool_surface') or {})} "
            f"behavior={ana_operator_status.format_live_behavior(report.get('live_behavior') or {})} "
            f"maps={ana_operator_status.format_context_maps(report.get('context_maps') or {})} "
            f"identity={ana_operator_status.format_identity_surface(report.get('identity_surface') or {})} "
            f"trace_aligned={report.get('trace', {}).get('aligned')} "
            f"file_deleted={report.get('file_activity', {}).get('diff', {}).get('deleted')} "
            f"dirty={report['git'].get('changed_paths')} "
            f"archive_candidates={report['memory_hygiene'].get('archive_candidates')} "
            f"date_basis={report['memory_hygiene'].get('archive_date_basis', 'utc')} "
            f"archive_readiness={format_archive_readiness(report['memory_hygiene'].get('archive_readiness', {}))}"
        )
        print(f"next_action={report['recommended_next_step']}")
        if path:
            print(f"report={path}")
    return 0


def format_archive_readiness(readiness: dict[str, Any]) -> str:
    status = readiness.get("status") if isinstance(readiness, dict) else None
    status = status or "UNKNOWN"
    delta = readiness.get("candidate_delta") if isinstance(readiness, dict) else None
    if status == "STALE" and isinstance(delta, int):
        sign = "+" if delta > 0 else ""
        return f"{status}({sign}{delta})"
    return str(status)


if __name__ == "__main__":
    raise SystemExit(main())
