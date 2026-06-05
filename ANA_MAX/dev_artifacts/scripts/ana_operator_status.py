"""Print the compact operator status before install/reload work."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import sys
import time
from typing import Any
import urllib.request


REPO_ROOT = Path(__file__).resolve().parents[3]
ANA_ROOT = REPO_ROOT / "ANA_MAX"
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import ana_lab_state_summary
import ana_dirty_tree_report
import ana_trace_report


DEFAULT_MCP_URL = "http://127.0.0.1:8766/mcp"
REPORT_DIR = ANA_ROOT / "dev_artifacts" / "reports"
REM_SLEEP_DIR = ANA_ROOT / "docs" / "rem_sleep"
CODE_MAP_INDEX = ANA_ROOT / "memory" / "code_map" / "index.json"
GRAPH_MAP_INDEX = ANA_ROOT / "memory" / "graph_map" / "graph.json"
CONTEXT_MAP_REFRESH_COMMAND = "python ANA_MAX/dev_artifacts/scripts/ana_refresh_context_maps.py"
ACTIVE_REVIEW_CATEGORIES = {"runtime", "script", "test", "config", "extension", "doc"}
FRESHNESS_SKEW_SECONDS = 2.0


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def read_package() -> dict[str, Any]:
    package_path = REPO_ROOT / "vscode_extension" / "package.json"
    return json.loads(package_path.read_text(encoding="utf-8"))


def latest_handoff() -> dict[str, str]:
    handoff = ANA_ROOT / "docs" / "CURRENT_SESSION_HANDOFF.md"
    data = {"file": str(handoff), "checkpoint": "", "timestamp": "", "memory_topic": ""}
    if not handoff.exists():
        return data
    for line in handoff.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("Latest checkpoint:"):
            data["checkpoint"] = line.split("`", 2)[1] if "`" in line else line
        elif line.startswith("Timestamp:"):
            data["timestamp"] = line.replace("Timestamp:", "", 1).strip()
        elif line.startswith("Memory topic:"):
            data["memory_topic"] = line.split("`", 2)[1] if "`" in line else line
    return data


def latest_rem_sleep(report_dir: Path = REM_SLEEP_DIR) -> dict[str, str]:
    data = {"file": "", "path": "", "timestamp": ""}
    if not report_dir.exists():
        return data
    reports = sorted(report_dir.glob("REM_SLEEP_REPORT_*.md"), key=lambda path: path.stat().st_mtime)
    if not reports:
        return data
    latest = reports[-1]
    data["file"] = latest.name
    data["path"] = str(latest)
    match = re.search(r"REM_SLEEP_REPORT_(.+)\.md$", latest.name)
    data["timestamp"] = match.group(1) if match else ""
    return data


def latest_report(pattern: str, report_dir: Path = REPORT_DIR) -> dict[str, str]:
    data = {"file": "", "path": "", "status": "", "summary": ""}
    if not report_dir.exists():
        return data
    matches = sorted(report_dir.glob(pattern))
    if not matches:
        return data
    latest = matches[-1]
    return summarize_report(latest)


def latest_report_path(pattern: str, report_dir: Path = REPORT_DIR) -> Path | None:
    if not report_dir.exists():
        return None
    matches = sorted(report_dir.glob(pattern))
    return matches[-1] if matches else None


def latest_trace_status(report_dir: Path = REPORT_DIR) -> dict[str, str]:
    latest_trace = latest_report_path("trace_report_*.json", report_dir)
    latest_autonomy = latest_report_path("autonomy_runner_*.json", report_dir)
    if latest_trace and (not latest_autonomy or report_stamp(latest_trace) >= report_stamp(latest_autonomy)):
        return summarize_report(latest_trace)
    if not latest_autonomy:
        return {"file": "", "path": "", "status": "", "summary": ""}
    try:
        summary = ana_trace_report.summarize_report(latest_autonomy)
    except Exception:
        return {"file": latest_autonomy.name, "path": str(latest_autonomy), "status": "UNKNOWN", "summary": ""}
    return {
        "file": latest_autonomy.name,
        "path": str(latest_autonomy),
        "status": "PASS" if summary.get("ok") else "WARN",
        "summary": f"steps={summary.get('steps')},spans={summary.get('spans')},aligned={summary.get('aligned')}",
    }


def latest_autonomy_patch_advisor(report_dir: Path = REPORT_DIR) -> dict[str, Any]:
    data: dict[str, Any] = {
        "file": "",
        "path": "",
        "first_review_batch": "",
        "first_review_next_step": "",
        "first_review_commands": [],
        "review_batch_plan": {},
    }
    latest_autonomy = latest_report_path("autonomy_runner_*.json", report_dir)
    if not latest_autonomy:
        return data
    data["file"] = latest_autonomy.name
    data["path"] = str(latest_autonomy)
    try:
        payload = json.loads(latest_autonomy.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return data
    for step in payload.get("steps") or []:
        if not isinstance(step, dict) or step.get("name") != "patch_advisor":
            continue
        patch_data = step.get("data") if isinstance(step.get("data"), dict) else {}
        data["first_review_batch"] = str(patch_data.get("first_review_batch") or "")
        data["first_review_next_step"] = str(patch_data.get("first_review_next_step") or "")
        commands = patch_data.get("first_review_commands")
        if isinstance(commands, list):
            data["first_review_commands"] = [str(command) for command in commands if command][:3]
        break
    for step in payload.get("steps") or []:
        if not isinstance(step, dict) or step.get("name") != "review_batch_plan":
            continue
        review_plan = step.get("data") if isinstance(step.get("data"), dict) else {}
        data["review_batch_plan"] = compact_review_batch_plan(review_plan)
        break
    if not data["review_batch_plan"]:
        signals = payload.get("signals") if isinstance(payload.get("signals"), dict) else {}
        review_plan = signals.get("review_batch_plan") if isinstance(signals, dict) else {}
        if isinstance(review_plan, dict):
            data["review_batch_plan"] = compact_review_batch_plan(review_plan)
    return data


def latest_review_batch_run(report_dir: Path = REPORT_DIR) -> dict[str, Any]:
    data: dict[str, Any] = {
        "file": "",
        "path": "",
        "status": "",
        "mode": "",
        "category": "",
        "commands": 0,
        "passed": 0,
        "failed": 0,
        "timeout": 0,
        "planned": 0,
        "first_command": "",
    }
    latest = latest_report_path("review_batch_runner_*.json", report_dir)
    if not latest:
        return data
    data["file"] = latest.name
    data["path"] = str(latest)
    try:
        payload = json.loads(latest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        data["status"] = "UNKNOWN"
        return data
    commands = payload.get("commands")
    commands = commands if isinstance(commands, list) else []
    data.update(summarize_review_batch_payload(payload))
    for command in commands:
        if isinstance(command, dict) and command.get("command"):
            data["first_command"] = str(command.get("command"))
            break
    return data


def recent_review_batch_runs(
    report_dir: Path = REPORT_DIR,
    max_reports: int = 80,
    freshness: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data: dict[str, Any] = {"categories": {}, "order": [], "freshness": {}}
    if not report_dir.exists():
        return data
    if freshness is None:
        freshness = review_category_freshness() if is_default_report_dir(report_dir) else {"available": False}
    data["freshness"] = freshness
    freshness_categories = freshness.get("categories") if isinstance(freshness, dict) else {}
    freshness_categories = freshness_categories if isinstance(freshness_categories, dict) else {}
    reports = sorted(report_dir.glob("review_batch_runner_*.json"), reverse=True)[:max_reports]
    for report_path in reports:
        try:
            payload = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if payload.get("mode") != "run":
            continue
        category = str(payload.get("category") or "")
        if not category or category in data["categories"]:
            continue
        summary = summarize_review_batch_payload(payload)
        summary["file"] = report_path.name
        summary["path"] = str(report_path)
        summary["report_mtime"] = safe_mtime(report_path)
        category_freshness = freshness_categories.get(category)
        if isinstance(category_freshness, dict):
            summary["latest_active_mtime"] = category_freshness.get("latest_mtime")
            summary["latest_active_path"] = category_freshness.get("latest_path")
            summary["fresh"] = review_report_is_fresh(summary["report_mtime"], category_freshness)
        data["categories"][category] = summary

    preferred_order = ["runtime", "script", "test", "config", "extension", "doc"]
    data["order"] = [
        category for category in preferred_order if category in data["categories"]
    ] + sorted(category for category in data["categories"] if category not in preferred_order)
    return data


def is_default_report_dir(report_dir: Path) -> bool:
    try:
        return report_dir.resolve() == REPORT_DIR.resolve()
    except OSError:
        return False


def safe_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def review_category_freshness() -> dict[str, Any]:
    data: dict[str, Any] = {
        "available": False,
        "categories": {},
        "policy": "compare latest active dirty-tree file mtime with latest review batch report mtime",
        "skew_seconds": FRESHNESS_SKEW_SECONDS,
    }
    try:
        lines = ana_dirty_tree_report.git_status_lines()
    except Exception as exc:
        data["error"] = str(exc)
        return data
    categories: dict[str, Any] = {}
    for line in lines:
        _status, relative_path = ana_dirty_tree_report.normalize_path(line)
        category = ana_dirty_tree_report.classify(relative_path)
        if category not in ACTIVE_REVIEW_CATEGORIES:
            continue
        full_path = REPO_ROOT / relative_path
        mtime = safe_mtime(full_path)
        if not mtime:
            mtime = time.time()
        current = categories.get(category)
        if not isinstance(current, dict) or mtime > float(current.get("latest_mtime") or 0):
            categories[category] = {
                "latest_mtime": mtime,
                "latest_path": relative_path,
            }
    data["available"] = True
    data["categories"] = categories
    return data


def review_report_is_fresh(report_mtime: Any, category_freshness: dict[str, Any]) -> bool:
    try:
        latest_active = float(category_freshness.get("latest_mtime") or 0)
        report_time = float(report_mtime or 0)
    except (TypeError, ValueError):
        return False
    if latest_active <= 0:
        return True
    return report_time + FRESHNESS_SKEW_SECONDS >= latest_active


def latest_active_context_source() -> dict[str, Any]:
    data: dict[str, Any] = {
        "available": False,
        "latest_mtime": 0.0,
        "latest_path": "",
        "policy": "compare Code Map and Graph Map mtime with latest active dirty-tree file mtime",
        "skew_seconds": FRESHNESS_SKEW_SECONDS,
    }
    try:
        lines = ana_dirty_tree_report.git_status_lines()
    except Exception as exc:
        data["error"] = str(exc)
        return data
    for line in lines:
        _status, relative_path = ana_dirty_tree_report.normalize_path(line)
        category = ana_dirty_tree_report.classify(relative_path)
        if category not in ACTIVE_REVIEW_CATEGORIES:
            continue
        full_path = REPO_ROOT / relative_path
        mtime = safe_mtime(full_path)
        if not mtime:
            mtime = time.time()
        if mtime > float(data.get("latest_mtime") or 0):
            data["latest_mtime"] = mtime
            data["latest_path"] = relative_path
    data["available"] = True
    return data


def read_json_payload(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def context_map_entry(
    name: str,
    path: Path,
    active_source: dict[str, Any],
    required_mtime: float = 0.0,
    required_label: str = "",
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "name": name,
        "path": str(path),
        "file": path.name,
        "exists": path.exists(),
        "status": "MISSING",
        "mtime": 0.0,
        "updated_at": "",
        "stale_source": "",
    }
    if not path.exists():
        return data
    payload = read_json_payload(path)
    data["status"] = "PASS"
    data["mtime"] = safe_mtime(path)
    data["updated_at"] = str(payload.get("updated_at") or "")
    if name == "code":
        files = payload.get("files")
        data["summaries"] = len(files) if isinstance(files, dict) else None
    elif name == "graph":
        stats = payload.get("stats") if isinstance(payload.get("stats"), dict) else {}
        data["nodes"] = stats.get("nodes")
        data["edges"] = stats.get("edges")
        data["code_map_updated_at"] = str(payload.get("code_map_updated_at") or "")

    active_mtime = float(active_source.get("latest_mtime") or 0)
    latest_required_mtime = max(active_mtime, float(required_mtime or 0))
    if data["mtime"] and latest_required_mtime and data["mtime"] + FRESHNESS_SKEW_SECONDS < latest_required_mtime:
        data["status"] = "STALE"
        if required_mtime and required_mtime >= active_mtime:
            data["stale_source"] = required_label or "required_input"
        else:
            data["stale_source"] = str(active_source.get("latest_path") or "active_work")
    return data


def context_maps_status() -> dict[str, Any]:
    active_source = latest_active_context_source()
    code = context_map_entry("code", CODE_MAP_INDEX, active_source)
    graph_required_mtime = float(code.get("mtime") or 0) if code.get("status") == "PASS" else 0.0
    graph = context_map_entry("graph", GRAPH_MAP_INDEX, active_source, graph_required_mtime, "code_map")
    if graph.get("status") == "PASS" and code.get("status") not in ("PASS",):
        graph["status"] = "STALE"
        graph["stale_source"] = f"code_map_{str(code.get('status') or 'unknown').lower()}"
    statuses = [code.get("status"), graph.get("status")]
    return {
        "schema": "ana.context_maps_status.v1",
        "status": "PASS" if statuses == ["PASS", "PASS"] else "WARN",
        "active_source": active_source,
        "code_map": code,
        "graph_map": graph,
    }


def context_maps_need_refresh(context_maps: dict[str, Any] | None) -> bool:
    if not isinstance(context_maps, dict):
        return False
    for key in ("code_map", "graph_map"):
        entry = context_maps.get(key)
        if isinstance(entry, dict) and entry.get("status") not in (None, "PASS"):
            return True
    return False


def summarize_review_batch_payload(payload: dict[str, Any]) -> dict[str, Any]:
    commands = payload.get("commands")
    commands = commands if isinstance(commands, list) else []
    statuses = [
        str(command.get("status") or "").lower()
        for command in commands
        if isinstance(command, dict)
    ]
    return {
        "status": str(payload.get("status") or "UNKNOWN").upper(),
        "mode": str(payload.get("mode") or ""),
        "category": str(payload.get("category") or ""),
        "commands": len(commands),
        "passed": statuses.count("pass"),
        "failed": statuses.count("fail"),
        "timeout": statuses.count("timeout"),
        "planned": statuses.count("planned"),
    }


def compact_review_batch_plan(plan: dict[str, Any]) -> dict[str, Any]:
    batches = plan.get("batches")
    if not isinstance(batches, list):
        batches = []
    return {
        "mode": str(plan.get("mode") or ""),
        "status": str(plan.get("status") or ""),
        "category": str(plan.get("category") or ""),
        "batch_count": int(plan.get("batch_count") or 0),
        "command_count": int(plan.get("command_count") or 0),
        "batches": [str(batch) for batch in batches if batch][:8],
        "first_command": str(plan.get("first_command") or ""),
    }


def report_stamp(path: Path) -> str:
    match = re.search(r"_(\d{8}_\d{6})\.json$", path.name)
    if match:
        return match.group(1)
    return datetime_from_mtime(path)


def datetime_from_mtime(path: Path) -> str:
    try:
        return str(int(path.stat().st_mtime))
    except OSError:
        return ""


def summarize_report(path: Path) -> dict[str, str]:
    data = {"file": path.name, "path": str(path), "status": "", "summary": ""}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        data["status"] = "UNKNOWN"
        return data

    status = payload.get("status")
    if not status and isinstance(payload.get("summary"), dict):
        summary = payload["summary"]
        status = "PASS" if summary.get("pass") and not summary.get("fail") else ""
    data["status"] = str(status or "UNKNOWN").upper()

    parts: list[str] = []
    if isinstance(payload.get("summary"), dict):
        summary = payload["summary"]
        for key in ("pass", "warn", "fail"):
            if key in summary:
                parts.append(f"{key}={summary[key]}")
    if isinstance(payload.get("advisory_summary"), dict):
        advisory = payload["advisory_summary"]
        for key in ("warn", "fail"):
            if key in advisory:
                parts.append(f"advisory_{key}={advisory[key]}")
    if not parts and isinstance(payload.get("steps"), list):
        statuses = [str(step.get("status", "")).upper() for step in payload["steps"] if isinstance(step, dict)]
        for key in ("PASS", "WARN", "FAIL"):
            count = statuses.count(key)
            if count:
                parts.append(f"{key.lower()}={count}")
    if not parts and isinstance(payload.get("results"), list):
        ok_count = sum(1 for item in payload["results"] if isinstance(item, dict) and item.get("ok") is True)
        fail_count = sum(1 for item in payload["results"] if isinstance(item, dict) and item.get("ok") is False)
        if ok_count:
            parts.append(f"pass={ok_count}")
        if fail_count:
            parts.append(f"fail={fail_count}")
    if payload.get("schema") == "ana.trace_report.v1":
        data["status"] = "PASS" if payload.get("ok") else "WARN"
        parts = [
            f"steps={payload.get('steps')}",
            f"spans={payload.get('spans')}",
            f"aligned={payload.get('aligned')}",
        ]
    data["summary"] = ",".join(parts)
    return data


def live_tool_names(mcp_url: str = DEFAULT_MCP_URL, timeout: int = 15) -> set[str]:
    payload = {
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000) % 1_000_000,
        "method": "tools/list",
        "params": {},
    }
    request = urllib.request.Request(
        mcp_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        parsed = json.loads(response.read().decode("utf-8", errors="replace"))
    tools = parsed.get("result", {}).get("tools", [])
    return {
        str(tool.get("name"))
        for tool in tools
        if isinstance(tool, dict) and tool.get("name")
    }


def manifest_tool_names() -> set[str]:
    path = ANA_ROOT / "config" / "permission_manifest.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    tools = payload.get("tools", {})
    return set(tools) if isinstance(tools, dict) else set()


def live_tool_surface(mcp_url: str = DEFAULT_MCP_URL) -> dict[str, Any]:
    manifest = manifest_tool_names()
    try:
        live = live_tool_names(mcp_url)
    except Exception as exc:
        return {
            "status": "UNKNOWN",
            "error": str(exc),
            "live_count": None,
            "manifest_count": len(manifest),
            "extra_live": [],
            "missing_live": [],
        }
    extra = sorted(live - manifest)
    missing = sorted(manifest - live)
    return {
        "status": "PASS" if not extra and not missing else "WARN",
        "live_count": len(live),
        "manifest_count": len(manifest),
        "extra_live": extra,
        "missing_live": missing,
    }


def build_status(mcp_url: str = DEFAULT_MCP_URL) -> dict[str, Any]:
    package = read_package()
    version = str(package.get("version") or "")
    vsix = REPO_ROOT / "vscode_extension" / f"ana-codex-cockpit-{version}.vsix"
    lab_vsix = ANA_ROOT / f"ana-max-codex-cockpit-{version}.vsix"
    lab_state = ana_lab_state_summary.build_summary(mcp_url)
    tool_surface = live_tool_surface(mcp_url)
    reload_reasons: list[str] = []
    if not bool(lab_state.get("live_reload", {}).get("has_marker")):
        reload_reasons.append("missing_reload_marker")
    if tool_surface.get("status") == "WARN":
        reload_reasons.append("live_tool_surface_drift")
    live_behavior = lab_state.get("live_behavior") or {}
    if live_behavior.get("status") == "WARN":
        reload_reasons.append("live_behavior_stale")
    reload_needed = bool(reload_reasons)
    identity_surface = lab_state.get("identity_surface") or {}
    identity_problem = identity_surface.get("status") not in (None, "PASS")
    reports = {
        "no_reload_quality_gate": latest_report("no_reload_quality_gate_*.json"),
        "lab_quality_gate": latest_report("lab_quality_gate_*.json"),
        "nucleus_smoke": latest_report("nucleus_smoke_*.json"),
        "autonomy_runner": latest_report("autonomy_runner_*.json"),
        "trace_report": latest_trace_status(),
        "review_batch_runner": latest_review_batch_run(),
        "review_batch_runs": recent_review_batch_runs(),
    }
    next_verification = latest_autonomy_patch_advisor()
    context_maps = context_maps_status()
    next_step = build_recommended_next_step(identity_problem, reload_reasons, reports, context_maps)
    return {
        "schema": "ana.operator_status.v1",
        "package": {
            "version": version,
            "copy_vsix": str(vsix),
            "copy_vsix_exists": vsix.exists(),
            "main_vsix": str(lab_vsix),
            "main_vsix_exists": lab_vsix.exists(),
        },
        "mcp": lab_state.get("mcp"),
        "live_reload": lab_state.get("live_reload"),
        "reload_readiness": {
            "status": "WARN" if reload_needed else "PASS",
            "reload_needed": reload_needed,
            "reasons": reload_reasons,
        },
        "live_tool_surface": tool_surface,
        "live_behavior": live_behavior,
        "identity_surface": identity_surface,
        "handoff": latest_handoff(),
        "rem_sleep": latest_rem_sleep(),
        "reports": reports,
        "next_verification": next_verification,
        "git": lab_state.get("git"),
        "memory_hygiene": lab_state.get("memory_hygiene"),
        "context_maps": context_maps,
        "file_activity": lab_state.get("file_activity"),
        "recommended_next_step": next_step,
        "install_command": f".\\ANA_MAX\\dev_artifacts\\scripts\\install_latest_lab_vsix.ps1 -Apply",
        "verify_command": "python ANA_MAX/dev_artifacts/scripts/ana_post_reload_verify.py --no-write",
    }


def build_recommended_next_step(
    identity_problem: bool,
    reload_reasons: list[str],
    reports: dict[str, Any] | None = None,
    context_maps: dict[str, Any] | None = None,
) -> str:
    if identity_problem:
        return "Fix active identity surface, then rerun Operator Status."
    if not reload_reasons:
        autonomy = (reports or {}).get("autonomy_runner", {})
        if isinstance(autonomy, dict) and autonomy.get("status") == "PASS" and context_maps_need_refresh(context_maps):
            return f"Run {CONTEXT_MAP_REFRESH_COMMAND}, then rerun Operator Status."
        if isinstance(autonomy, dict) and autonomy.get("status") == "PASS":
            return "Continue with one scoped lab action."
        return "Run Autonomy Pass, then continue with one scoped lab action."
    if reload_reasons == ["live_behavior_stale"]:
        return "Restart ANA MCP, then run Live Behavior, Reload Consistency, and Post-Reload Verify."
    return "Install VSIX if needed, reload VS Code, restart ANA MCP, then run Post-Reload Verify."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Show compact ANA operator status.")
    parser.add_argument("--mcp-url", default=DEFAULT_MCP_URL)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    status = build_status(args.mcp_url)
    if args.json:
        print(json.dumps(status, indent=2, ensure_ascii=False))
    else:
        print(
            "ANA Operator Status: "
            f"vsix={status['package']['version']} "
            f"package={format_package_artifacts(status.get('package') or {})} "
            f"mcp_ready={status['mcp'].get('mcp_ready')} "
            f"tools={status['mcp'].get('tools_count')} "
            f"reload={status['reload_readiness'].get('status')} "
            f"marker={status['live_reload'].get('has_marker')} "
            f"tool_surface={format_tool_surface(status.get('live_tool_surface') or {})} "
            f"behavior={format_live_behavior(status.get('live_behavior') or {})} "
            f"identity={format_identity_surface(status.get('identity_surface') or {})} "
            f"files={format_file_activity(status.get('file_activity') or {})} "
            f"memory={format_memory_hygiene(status.get('memory_hygiene') or {})} "
            f"maps={format_context_maps(status.get('context_maps') or {})}"
        )
        print(f"checkpoint={status['handoff'].get('checkpoint')}")
        print(f"rem_sleep={format_rem_sleep(status.get('rem_sleep') or {})}")
        reports = status.get("reports", {})
        print(
            "reports="
            f"no_reload:{format_report(reports.get('no_reload_quality_gate', {}))} "
            f"lab:{format_report(reports.get('lab_quality_gate', {}))} "
            f"nucleus:{format_report(reports.get('nucleus_smoke', {}))} "
            f"autonomy:{format_report(reports.get('autonomy_runner', {}))} "
            f"trace:{format_report(reports.get('trace_report', {}))}"
        )
        print(f"next_action={status['recommended_next_step']}")
        print(
            "review="
            f"{format_next_verification(status.get('next_verification') or {}, reports.get('review_batch_runs', {}))}"
        )
        print(f"review_run={format_review_batch_run(reports.get('review_batch_runner', {}))}")
        print(f"review_runs={format_review_batch_runs(reports.get('review_batch_runs', {}))}")
        print(f"install={status['install_command']}")
        print(f"verify={status['verify_command']}")
    return 0


def format_report(report: dict[str, str]) -> str:
    filename = report.get("file") or "-"
    status = report.get("status")
    summary = report.get("summary")
    if not status:
        return filename
    if summary:
        return f"{filename}:{status}({summary})"
    return f"{filename}:{status}"


def format_package_artifacts(package: dict[str, Any]) -> str:
    main_exists = bool(package.get("main_vsix_exists"))
    copy_exists = bool(package.get("copy_vsix_exists"))
    status = "PASS" if main_exists and copy_exists else "WARN"
    return f"{status}(main={main_exists},copy={copy_exists})"


def format_rem_sleep(report: dict[str, str]) -> str:
    filename = report.get("file") or "-"
    timestamp = report.get("timestamp")
    return f"{filename}({timestamp})" if timestamp else filename


def format_next_verification(next_verification: dict[str, Any], review_runs: dict[str, Any] | None = None) -> str:
    batch = next_verification.get("first_review_batch") or "-"
    commands = next_verification.get("first_review_commands")
    command = "-"
    if isinstance(commands, list) and commands:
        command = str(commands[0])
    review_plan = next_verification.get("review_batch_plan")
    if isinstance(review_plan, dict) and review_plan:
        mode = review_plan.get("mode") or review_plan.get("status") or "-"
        batch_count = review_plan.get("batch_count") or 0
        command_count = review_plan.get("command_count") or 0
        verified = format_review_batch_coverage(review_plan, review_runs or {})
        suffix = f" {verified}" if verified else ""
        return f"batch={batch} command={command} plan={mode} batches={batch_count} commands={command_count}{suffix}"
    return f"batch={batch} command={command}"


def format_review_batch_coverage(review_plan: dict[str, Any], review_runs: dict[str, Any]) -> str:
    planned = review_plan.get("batches")
    if not isinstance(planned, list) or not planned:
        return ""
    planned_categories = [str(category) for category in planned if category]
    categories = review_runs.get("categories") if isinstance(review_runs, dict) else {}
    if not isinstance(categories, dict) or not categories:
        return f"verified=0/{len(planned_categories)} all_pass=false"

    passed = 0
    stale_categories: list[str] = []
    freshness_known = False
    for category in planned_categories:
        summary = categories.get(category)
        if not isinstance(summary, dict):
            continue
        if "fresh" in summary:
            freshness_known = True
        if summary.get("fresh") is False:
            stale_categories.append(category)
        if review_batch_summary_verified(summary):
            passed += 1
    all_pass = passed == len(planned_categories)
    suffix = ""
    if freshness_known:
        suffix = f" fresh={str(not stale_categories).lower()}"
        if stale_categories:
            suffix += f" stale={','.join(stale_categories[:3])}"
    return f"verified={passed}/{len(planned_categories)} all_pass={str(all_pass).lower()}{suffix}"


def review_batch_summary_verified(summary: dict[str, Any]) -> bool:
    return (
        summary.get("status") == "PASS"
        and not summary.get("failed")
        and not summary.get("timeout")
        and summary.get("fresh", True) is not False
    )


def format_review_batch_run(report: dict[str, Any]) -> str:
    filename = report.get("file") or "-"
    status = report.get("status") or "UNKNOWN"
    mode = report.get("mode") or "-"
    category = report.get("category") or "-"
    commands = report.get("commands")
    passed = report.get("passed")
    failed = report.get("failed")
    timeout = report.get("timeout")
    planned = report.get("planned")
    return (
        f"{filename}:{status}"
        f"(mode={mode},category={category},commands={commands},"
        f"pass={passed},fail={failed},timeout={timeout},planned={planned})"
    )


def format_review_batch_runs(ledger: dict[str, Any]) -> str:
    categories = ledger.get("categories") if isinstance(ledger, dict) else {}
    order = ledger.get("order") if isinstance(ledger, dict) else []
    if not isinstance(categories, dict) or not categories:
        return "-"
    order = order if isinstance(order, list) else []
    rendered: list[str] = []
    for category in order:
        summary = categories.get(category)
        if not isinstance(summary, dict):
            continue
        commands = summary.get("commands") or 0
        passed = summary.get("passed") or 0
        failed = summary.get("failed") or 0
        timeout = summary.get("timeout") or 0
        status = summary.get("status") or "UNKNOWN"
        fresh = ""
        if "fresh" in summary:
            fresh = f",fresh={str(bool(summary.get('fresh'))).lower()}"
        rendered.append(f"{category}:{status}({passed}/{commands},fail={failed},timeout={timeout}{fresh})")
    return ",".join(rendered) if rendered else "-"


def format_file_activity(activity: dict[str, Any]) -> str:
    diff = activity.get("diff") if isinstance(activity, dict) else {}
    if not isinstance(diff, dict):
        return "-"
    return (
        f"created={diff.get('created', 0)},"
        f"deleted={diff.get('deleted', 0)},"
        f"modified={diff.get('modified', 0)}"
    )


def format_tool_surface(surface: dict[str, Any]) -> str:
    status = surface.get("status") or "UNKNOWN"
    live = surface.get("live_count")
    manifest = surface.get("manifest_count")
    extra = len(surface.get("extra_live") or [])
    missing = len(surface.get("missing_live") or [])
    return f"{status}(live={live},manifest={manifest},extra={extra},missing={missing})"


def format_identity_surface(surface: dict[str, Any]) -> str:
    status = surface.get("status") or "UNKNOWN"
    files = surface.get("files_checked")
    violations = surface.get("violations")
    missing = surface.get("missing_required")
    return f"{status}(files={files},violations={violations},missing={missing})"


def format_live_behavior(behavior: dict[str, Any]) -> str:
    status = behavior.get("status") or "UNKNOWN"
    checks = behavior.get("checks") if isinstance(behavior, dict) else {}
    checks = checks if isinstance(checks, dict) else {}
    passed = sum(1 for value in checks.values() if value is True)
    total = len(checks)
    return f"{status}(checks={passed}/{total})"


def format_memory_hygiene(memory: dict[str, Any]) -> str:
    candidates = memory.get("archive_candidates")
    date_basis = memory.get("archive_date_basis") or "utc"
    readiness = memory.get("archive_readiness") if isinstance(memory, dict) else {}
    readiness = readiness if isinstance(readiness, dict) else {}
    readiness_status = readiness.get("status") or ("NONE" if readiness.get("available") is False else "UNKNOWN")
    moves = readiness.get("total_moves")
    if readiness_status == "PASS" and isinstance(candidates, int) and isinstance(moves, int) and candidates != moves:
        readiness_status = "STALE"
    delta = readiness.get("candidate_delta")
    if delta is None and isinstance(candidates, int) and isinstance(moves, int) and candidates != moves:
        delta = candidates - moves
    delta_text = ""
    if readiness_status == "STALE" and isinstance(delta, int):
        sign = "+" if delta > 0 else ""
        delta_text = f",delta={sign}{delta}"
    return f"archive_candidates={candidates},date_basis={date_basis},readiness={readiness_status},moves={moves}{delta_text}"


def format_context_maps(context_maps: dict[str, Any]) -> str:
    code = context_maps.get("code_map") if isinstance(context_maps, dict) else {}
    graph = context_maps.get("graph_map") if isinstance(context_maps, dict) else {}
    code = code if isinstance(code, dict) else {}
    graph = graph if isinstance(graph, dict) else {}

    code_status = code.get("status") or "UNKNOWN"
    code_summaries = code.get("summaries")
    graph_status = graph.get("status") or "UNKNOWN"
    graph_nodes = graph.get("nodes")
    graph_edges = graph.get("edges")

    code_suffix = f"{code_summaries}" if code_summaries is not None else "-"
    graph_suffix = f"{graph_nodes}n/{graph_edges}e" if graph_nodes is not None and graph_edges is not None else "-"
    stale_sources = []
    if code_status != "PASS" and code.get("stale_source"):
        stale_sources.append(f"code={short_status_path(str(code.get('stale_source')))}")
    if graph_status != "PASS" and graph.get("stale_source"):
        stale_sources.append(f"graph={short_status_path(str(graph.get('stale_source')))}")
    stale_text = f",stale={';'.join(stale_sources)}" if stale_sources else ""
    return f"code:{code_status}({code_suffix}) graph:{graph_status}({graph_suffix}{stale_text})"


def short_status_path(path: str, limit: int = 48) -> str:
    normalized = path.replace("\\", "/")
    if len(normalized) <= limit:
        return normalized
    return "..." + normalized[-(limit - 3):]


if __name__ == "__main__":
    raise SystemExit(main())
