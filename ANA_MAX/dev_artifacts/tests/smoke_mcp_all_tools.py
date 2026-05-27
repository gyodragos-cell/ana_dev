from __future__ import annotations

import json
import socket
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import request
from urllib.error import HTTPError, URLError


MCP_URL = "http://127.0.0.1:8766/mcp"
REPORT_DIR = Path(__file__).resolve().parents[1] / "reports"


SAFE_CASES: dict[str, dict[str, Any]] = {
    "adal_integration": {"operation": "version"},
    "adb_operations": {"operation": "devices", "timeout": 15},
    "agent_coach": {
        "action": "recommend",
        "task": "MCP tool failed with schema mismatch action versus operation",
        "error": "Invalid value for operation",
        "limit": 20,
        "repeat_threshold": 5,
        "max_tools": 5,
        "include_prompt": False,
    },
    "ana_health_check": {"include_contracts": False},
    "ana_identity": {},
    "ana_memory": {"action": "stats"},
    "ana_orchestrator": {"action": "status"},
    "ana_patch_suggester": {"issues": []},
    "ana_runtime_inspector": {"action": "snapshot"},
    "autonomy_dashboard": {},
    "baseline_update_suggester": {},
    "browser_control": {"operation": "status"},
    "clipboard_manager": {"action": "history", "limit": 3},
    "code_search": {"operation": "list_files", "path": ".", "max_results": 3},
    "code_tools": {"operation": "analyze", "target": "main.py"},
    "codebase_understanding": {"action": "semantic_search", "query": "MCP", "project_path": "."},
    "context_bridge": {"action": "status"},
    "context_engine": {"action": "get_context"},
    "conversation_learning": {"action": "recent", "limit": 3},
    "debugger": {"action": "analyze", "traceback_text": "ValueError: ana smoke test"},
    "desktop_capture": {"operation": "get_windows"},
    "docs_generator": {"action": "status"},
    "edge_tts_voice": {"operation": "list_voices"},
    "error_radar": {"action": "scan", "path": ".", "max_results": 5},
    "event_stream": {"action": "stats"},
    "file_operations": {"operation": "list", "path": ".", "max_results": 5},
    "file_patch": {
        "path": "dev_artifacts/tests/smoke_mcp_all_tools.py",
        "old_text": "MCP_URL = \"http://127.0.0.1:8766/mcp\"",
        "new_text": "MCP_URL = \"http://127.0.0.1:8766/mcp\"",
        "preview_only": True,
    },
    "foreground_ui_snapshot": {"include_tree": False},
    "frida_instrument": {"operation": "version", "confirm": True},
    "git_operations": {"operation": "status"},
    "glob_search": {"pattern": "*.py", "path": ".", "max_results": 5},
    "grep_content": {"regex": "ANA", "search_path": ".", "limit": 5},
    "grep_file": {"regex": "ANA", "search_path": ".", "limit": 5},
    "live_desktop_viewer": {"operation": "status"},
    "live_tool_healer": {"action": "test_health", "tool_name": "ana_identity", "verbose": False},
    "memory_cortex": {"action": "status"},
    "network_diag": {"operation": "ip_info", "target": "127.0.0.1"},
    "ocr_tool": {"action": "check"},
    "privacy_shield": {"operation": "status", "confirm": True},
    "proactive_interrupt": {"action": "status"},
    "project_navigator": {"operation": "list", "path": ".", "limit": 5},
    "qa_testing": {"operation": "edge_case_analysis", "target": "def add(a, b): return a + b"},
    "remote_control": {"action": "list"},
    "runtime_guard": {"action": "status"},
    "schema_diff": {"expected_schema": {"type": "object"}, "actual_response": {}},
    "security_audit": {"operation": "hash_gen", "target": "ana-smoke-test", "algo": "sha256"},
    "self_evolving_tool": {"action": "status", "confirm": True},
    "session_log_miner": {
        "action": "analyze",
        "path": "dev_artifacts/tests/smoke_mcp_all_tools.py",
        "limit": 3,
    },
    "session_rem_sleep": {"action": "latest"},
    "smart_search": {"action": "stats"},
    "swarm_orchestrator": {"action": "status"},
    "system_control": {"operation": "vitals"},
    "system_optimization": {"operation": "analyze"},
    "terminal": {"operation": "session_info", "session_id": "default", "confirm": True},
    "todowrite": {"operation": "list", "session_id": "smoke"},
    "tool_contract_validator": {"action": "validate_tool", "tool_name": "context_engine"},
    "tool_healthcheck": {"tool": "ana_identity"},
    "tool_router": {"task": "PowerShell command failed twice with encoding error", "max_tools": 4},
    "vector_memory": {"action": "stats"},
    "web_scraper": {"operation": "parse", "html": "<html><title>ana</title></html>"},
    "window_manager": {"action": "list"},
    "windows_deep_sight": {"operation": "top_cpu", "limit": 5},
    "windows_insight": {"operation": "get_events"},
    "windows_uia_bridge": {"action": "list_windows", "confirm": True},
    "workspace_situational_awareness": {
        "include_errors": False,
        "include_git": False,
        "include_uia": False,
    },
}


SKIP_REASONS: dict[str, str] = {
    "advanced_scanner": "security scanner needs an explicit target; skipped for safety",
    "apk_analyzer": "requires an APK path",
    "autonomous_engine": "autonomous execution has no dry-run/status operation",
    "bash_exec": "executes shell commands; covered by terminal echo instead",
    "desktop_control": "can move/click/type on desktop",
    "edit": "can edit files",
    "file_patch": "patch tools can modify files unless a safe validate mode exists",
    "hardware_scanner": "hardware/network scanner needs an explicit authorized target",
    "mitm_analyzer": "network interception analysis needs an explicit capture/target",
    "network_pentest": "pentest tool needs an explicit authorized target",
    "science_research": "requires a dataset or simulation parameters",
    "session_checkpoint": "creates checkpoint files; skipped in non-mutating smoke pass",
    "task": "planner can invoke the autonomous engine/model and exceeded smoke timeout",
    "uia_click": "clicks UI elements",
    "uia_type": "types into UI elements",
    "vision_fallback": "vision provider calls need API keys or live screen intent",
    "vision_find_element": "requires a template image path",
    "vision_region_capture": "captures screen pixels; skipped to avoid writing screenshots",
    "web_fetch": "network fetch skipped in restricted/offline smoke pass",
    "web_ai_bridge": "external AI provider calls skipped to avoid network/API use",
    "web_search": "network search skipped in restricted/offline smoke pass",
}


@dataclass
class CaseResult:
    name: str
    status: str
    elapsed_ms: int
    args: dict[str, Any] | None = None
    message: str | None = None
    error: str | None = None
    data_type: str | None = None


def rpc(method: str, params: dict[str, Any] | None = None, timeout: int = 12) -> dict[str, Any]:
    payload = {
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000) % 1_000_000,
        "method": method,
        "params": params or {},
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        MCP_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def extract_tool_payload(response: dict[str, Any]) -> dict[str, Any]:
    if "error" in response:
        return {"success": False, "error": response["error"], "message": "json-rpc error"}
    content = response.get("result", {}).get("content", [])
    if not content:
        return {"success": True, "data": response.get("result"), "message": "empty content"}
    text = content[0].get("text", "")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"success": True, "data": text, "message": "non-json text"}


def run_case(name: str, args: dict[str, Any]) -> CaseResult:
    started = time.perf_counter()
    try:
        response = rpc("tools/call", {"name": name, "arguments": args})
        elapsed = int((time.perf_counter() - started) * 1000)
        payload = extract_tool_payload(response)
        ok = bool(payload.get("success", True))
        return CaseResult(
            name=name,
            status="pass" if ok else "fail",
            elapsed_ms=elapsed,
            args=args,
            message=payload.get("message"),
            error=str(payload.get("error")) if payload.get("error") else None,
            data_type=type(payload.get("data")).__name__,
        )
    except socket.timeout as exc:
        return CaseResult(name=name, status="timeout", elapsed_ms=12000, args=args, error=str(exc))
    except (HTTPError, URLError, TimeoutError) as exc:
        elapsed = int((time.perf_counter() - started) * 1000)
        return CaseResult(name=name, status="error", elapsed_ms=elapsed, args=args, error=str(exc))
    except Exception as exc:  # noqa: BLE001 - smoke test should keep going
        elapsed = int((time.perf_counter() - started) * 1000)
        return CaseResult(name=name, status="error", elapsed_ms=elapsed, args=args, error=repr(exc))


def main() -> int:
    tools_response = rpc("tools/list", timeout=20)
    tools = tools_response["result"]["tools"]
    names = sorted(tool["name"] for tool in tools)

    results: list[CaseResult] = []
    for name in names:
        if name in SAFE_CASES:
            results.append(run_case(name, SAFE_CASES[name]))
        else:
            results.append(
                CaseResult(
                    name=name,
                    status="skipped_unsafe",
                    elapsed_ms=0,
                    message=SKIP_REASONS.get(name, "no safe smoke case defined yet"),
                )
            )

    summary: dict[str, int] = {}
    for result in results:
        summary[result.status] = summary.get(result.status, 0) + 1

    report = {
        "mcp_url": MCP_URL,
        "tool_count": len(names),
        "summary": dict(sorted(summary.items())),
        "results": [result.__dict__ for result in results],
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / f"mcp_smoke_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")

    print(json.dumps({"summary": report["summary"], "report": str(report_path)}, indent=2))
    for result in results:
        if result.status not in {"pass", "skipped_unsafe"}:
            print(f"{result.status.upper():7} {result.name}: {result.error or result.message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
