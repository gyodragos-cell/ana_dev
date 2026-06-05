"""Smoke test ANA MAX Activity Bar buttons without clicking the UI.

The VS Code API cannot be driven reliably from a plain lab shell, so this script
tests the same backing paths the buttons use: package command registration,
MCP calls, and local helper scripts. Write-heavy or interactive buttons are
reported as SKIP by default instead of mutating the lab.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any
import urllib.request


REPO_ROOT = Path(__file__).resolve().parents[3]
ANA_ROOT = REPO_ROOT / "ANA_MAX"
REPORT_DIR = ANA_ROOT / "dev_artifacts" / "reports"
PACKAGE_JSON = REPO_ROOT / "vscode_extension" / "package.json"
EXTENSION_JS = REPO_ROOT / "vscode_extension" / "extension.js"
DEFAULT_MCP_URL = "http://127.0.0.1:8766/mcp"

ACTION_ITEM_RE = re.compile(
    r'actionItem\("(?P<label>[^"]+)",\s*"(?P<command>[^"]+)",\s*"(?P<icon>[^"]+)",\s*"(?P<tooltip>[^"]*)"\)'
)

WRITE_GATED = {
    "anaMax.wakeSession": "may write first-run session memory",
    "anaMax.checkpoint": "writes a checkpoint",
    "anaMax.runRemSleep": "consolidates REM/session memory",
    "anaMax.generateSessionAudit": "generates an audit report",
}

INTERACTIVE_GATED = {
    "anaMax.executeTool": "requires operator input",
    "anaMax.binaryMap": "requires a binary path",
    "anaMax.voiceInbox": "requires microphone input",
    "anaMax.voiceOperatorSmoke": "speaks an operator smoke phrase",
}

EXTERNAL_GATED = {
    "anaMax.openDashboard": "opens a browser/local HTML file",
}

HEAVY_GATED = {
    "anaMax.autonomyPass": "runs a multi-step autonomy pass",
    "anaMax.labQualityGate": "runs the broader lab quality gate",
    "anaMax.noReloadGate": "runs the no-reload packaging gate",
}

REFRESH_GATED = {
    "anaMax.refreshCodeMap": "refreshes Code Map and Graph Map files",
}


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def health_url(mcp_url: str) -> str:
    return mcp_url.rstrip("/").removesuffix("/mcp") + "/health"


def json_request(url: str, payload: dict[str, Any] | None = None, timeout: int = 20) -> dict[str, Any]:
    data = None
    method = "GET"
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        method = "POST"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def rpc(mcp_url: str, method: str, params: dict[str, Any] | None = None, timeout: int = 20) -> dict[str, Any]:
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


def call_tool(mcp_url: str, name: str, arguments: dict[str, Any], timeout: int = 30) -> dict[str, Any]:
    response = rpc(
        mcp_url,
        "tools/call",
        {"name": name, "arguments": arguments},
        timeout=timeout,
    )
    content = response.get("result", {}).get("content", [])
    if not content:
        return {"success": False, "error": "missing MCP content"}
    text = str(content[0].get("text") or "")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {"success": False, "error": "non-JSON MCP content", "text": text[:500]}
    return parsed if isinstance(parsed, dict) else {"success": False, "data": parsed}


def extract_activity_buttons(source: str | None = None) -> list[dict[str, str]]:
    text = source if source is not None else EXTENSION_JS.read_text(encoding="utf-8")
    buttons: list[dict[str, str]] = []
    for match in ACTION_ITEM_RE.finditer(text):
        buttons.append(match.groupdict())
    return buttons


def declared_commands(package: dict[str, Any] | None = None) -> set[str]:
    payload = package if package is not None else json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
    commands = payload.get("contributes", {}).get("commands", [])
    return {
        str(item.get("command"))
        for item in commands
        if isinstance(item, dict) and item.get("command")
    }


def run_process(args: list[str], timeout: int = 120) -> tuple[bool, str]:
    result = subprocess.run(
        args,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    output = (result.stdout or result.stderr or "").strip()
    first_line = output.splitlines()[0] if output else ""
    return result.returncode == 0, first_line


def pass_result(button: dict[str, str], probe: str, detail: str = "") -> dict[str, Any]:
    return {**button, "status": "PASS", "probe": probe, "detail": detail}


def skip_result(button: dict[str, str], probe: str, reason: str) -> dict[str, Any]:
    return {**button, "status": "SKIP", "probe": probe, "detail": reason}


def fail_result(button: dict[str, str], probe: str, detail: str) -> dict[str, Any]:
    return {**button, "status": "FAIL", "probe": probe, "detail": detail}


def warn_result(button: dict[str, str], probe: str, detail: str) -> dict[str, Any]:
    return {**button, "status": "WARN", "probe": probe, "detail": detail}


def result_from_process(button: dict[str, str], probe: str, ok: bool, detail: str) -> dict[str, Any]:
    if not ok:
        return fail_result(button, probe, detail)
    if detail_has_warn(detail):
        return warn_result(button, probe, detail)
    return pass_result(button, probe, detail)


def result_from_tool_payload(button: dict[str, str], probe: str, payload: dict[str, Any]) -> dict[str, Any]:
    detail = str(payload.get("message") or payload.get("error") or "")
    if payload.get("success"):
        return pass_result(button, probe, detail)
    return fail_result(button, probe, detail or str(payload)[:500])


def detail_has_warn(detail: str) -> bool:
    text = str(detail or "").upper()
    return (
        ": WARN" in text
        or "STATUS=WARN" in text
        or "RELOAD=WARN" in text
        or "NUCLEUS=WARN" in text
        or "STALE(" in text
        or " FRESH=FALSE" in text
    )


def tools_list(mcp_url: str, timeout: int) -> list[dict[str, Any]]:
    response = rpc(mcp_url, "tools/list", {}, timeout=timeout)
    tools = response.get("result", {}).get("tools", [])
    return tools if isinstance(tools, list) else []


def tool_names(mcp_url: str, timeout: int) -> set[str]:
    return {
        str(tool.get("name"))
        for tool in tools_list(mcp_url, timeout)
        if isinstance(tool, dict) and tool.get("name")
    }


def run_button_probe(
    button: dict[str, str],
    mcp_url: str,
    command_set: set[str],
    names: set[str],
    include_heavy: bool,
    include_writes: bool,
    include_refresh: bool,
    include_external: bool,
    timeout: int,
) -> dict[str, Any]:
    command = button["command"]
    if command not in command_set:
        return fail_result(button, "command_registration", "command missing from package.json")

    if command in WRITE_GATED and not include_writes:
        return skip_result(button, "write_gated", WRITE_GATED[command])
    if command in INTERACTIVE_GATED:
        tool = "binary_map" if command == "anaMax.binaryMap" else ""
        if tool and tool in names:
            return skip_result(button, "interactive_gated", f"{INTERACTIVE_GATED[command]}; tool_present=True")
        return skip_result(button, "interactive_gated", INTERACTIVE_GATED[command])
    if command in EXTERNAL_GATED and not include_external:
        return skip_result(button, "external_gated", EXTERNAL_GATED[command])
    if command in HEAVY_GATED and not include_heavy:
        return skip_result(button, "heavy_gated", HEAVY_GATED[command])
    if command in REFRESH_GATED and not include_refresh:
        return skip_result(button, "refresh_gated", REFRESH_GATED[command])

    try:
        if command == "anaMax.wakeSession":
            payload = call_tool(mcp_url, "session_lifecycle", {"action": "wake"}, timeout=timeout)
            return result_from_tool_payload(button, "session_lifecycle_wake", payload)
        if command == "anaMax.checkpoint":
            ok, detail = run_process([
                sys.executable,
                "ANA_MAX/dev_artifacts/scripts/ana_local_checkpoint.py",
                "--title",
                "Activity Bar button smoke checkpoint",
                "--summary",
                "Activity Bar button smoke verified the write-gated checkpoint path.",
                "--current-goal",
                "Verify ANA MAX Activity Bar button backing paths.",
                "--next-steps",
                "Continue with safe no-write button smoke by default; use include-writes only with operator intent.",
                "--files-changed",
                "ANA_MAX/dev_artifacts/scripts/ana_activity_bar_button_smoke.py",
                "--validation",
                "Activity Bar button smoke include-writes checkpoint probe executed.",
                "--risks",
                "This probe writes a checkpoint and should only run when include-writes is explicitly set.",
                "--sync-status",
                "Mother lab only.",
                "--no-include-git",
            ], timeout=max(timeout, 120))
            return result_from_process(button, "local_checkpoint", ok, detail)
        if command == "anaMax.runRemSleep":
            payload = call_tool(
                mcp_url,
                "session_lifecycle",
                {"action": "rest", "consolidate": True, "save_memory": True},
                timeout=max(timeout, 120),
            )
            return result_from_tool_payload(button, "session_lifecycle_rest_consolidate", payload)
        if command == "anaMax.generateSessionAudit":
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            payload = call_tool(
                mcp_url,
                "session_audit",
                {"action": "generate", "run_id": f"activity-bar-button-smoke-{stamp}", "hours": 1, "limit": 120},
                timeout=timeout,
            )
            return result_from_tool_payload(button, "session_audit_generate", payload)
        if command == "anaMax.openLiveConsole":
            return pass_result(button, "static", "output channel command registered")
        if command == "anaMax.startRuntime":
            health = json_request(health_url(mcp_url), timeout=timeout)
            if health.get("mcp_ready"):
                return pass_result(button, "health_running", f"server already ready tools={health.get('tools_count')}")
            return warn_result(button, "health_running", "server not ready; button would attempt start")
        if command == "anaMax.showHealth":
            ok, detail = run_process([
                sys.executable,
                "ANA_MAX_Launcher/mcp_readiness_check.py",
                "--mcp-url",
                mcp_url,
            ], timeout=max(timeout, 30))
            return result_from_process(button, "smart_readiness", ok, detail)
        if command == "anaMax.showHealthJson":
            health = json_request(health_url(mcp_url), timeout=timeout)
            return pass_result(button, "health_json", f"status={health.get('status')} tools={health.get('tools_count')}")
        if command == "anaMax.listTools":
            return pass_result(button, "tools_list", f"tools={len(names)}")
        if command == "anaMax.liveDebug":
            health = json_request(health_url(mcp_url), timeout=timeout)
            return pass_result(button, "live_debug", f"ready={health.get('mcp_ready')} tools={len(names)}")
        if command == "anaMax.codexCompanion":
            ok, detail = run_process([
                sys.executable,
                "ANA_MAX/dev_artifacts/scripts/ana_codex_companion.py",
                "--mcp-url",
                mcp_url,
                "--goal",
                "Activity Bar button smoke asks ANA to challenge Codex before work.",
                "--no-write",
            ], timeout=max(timeout, 90))
            return result_from_process(button, "codex_companion", ok, detail)
        if command == "anaMax.nucleusSmoke":
            ok, detail = run_process([
                sys.executable,
                "ANA_MAX/dev_artifacts/scripts/ana_nucleus_smoke.py",
                "--mcp-url",
                mcp_url,
                "--no-write",
            ], timeout=max(timeout, 120))
            return result_from_process(button, "nucleus_smoke", ok, detail)
        if command == "anaMax.autonomyPass":
            ok, detail = run_process([
                sys.executable,
                "ANA_MAX/dev_artifacts/scripts/ana_autonomy_runner.py",
                "--mcp-url",
                mcp_url,
                "--no-write",
            ], timeout=max(timeout, 180))
            return result_from_process(button, "autonomy_pass", ok, detail)
        if command == "anaMax.labQualityGate":
            ok, detail = run_process([sys.executable, "ANA_MAX/dev_artifacts/scripts/lab_quality_gate.py"], timeout=max(timeout, 300))
            return result_from_process(button, "lab_quality_gate", ok, detail)
        if command == "anaMax.noReloadGate":
            ok, detail = run_process([
                sys.executable,
                "ANA_MAX/dev_artifacts/scripts/no_reload_quality_gate.py",
                "--mcp-url",
                mcp_url,
            ], timeout=max(timeout, 300))
            return result_from_process(button, "no_reload_gate", ok, detail)
        if command == "anaMax.operatorStatus":
            ok, detail = run_process([
                sys.executable,
                "ANA_MAX/dev_artifacts/scripts/ana_operator_status.py",
                "--mcp-url",
                mcp_url,
            ], timeout=max(timeout, 90))
            return result_from_process(button, "operator_status", ok, detail)
        if command == "anaMax.reviewBatchPlan":
            ok, detail = run_process([
                sys.executable,
                "ANA_MAX/dev_artifacts/scripts/ana_review_batch_runner.py",
                "--all-batches",
                "--no-write",
            ], timeout=max(timeout, 60))
            return result_from_process(button, "review_batch_plan", ok, detail)
        if command == "anaMax.liveBehavior":
            ok, detail = run_process([
                sys.executable,
                "ANA_MAX/dev_artifacts/scripts/ana_live_behavior_check.py",
            ], timeout=max(timeout, 90))
            return result_from_process(button, "live_behavior", ok, detail)
        if command == "anaMax.reloadReadiness":
            ok, detail = run_process([
                sys.executable,
                "ANA_MAX/dev_artifacts/scripts/ana_reload_readiness.py",
                "--mcp-url",
                mcp_url,
                "--no-write",
            ], timeout=max(timeout, 60))
            return result_from_process(button, "reload_readiness", ok, detail)
        if command == "anaMax.reloadConsistency":
            ok, detail = run_process([
                sys.executable,
                "ANA_MAX/dev_artifacts/scripts/ana_reload_consistency_check.py",
                "--mcp-url",
                mcp_url,
                "--no-write",
            ], timeout=max(timeout, 90))
            return result_from_process(button, "reload_consistency", ok, detail)
        if command == "anaMax.postReloadVerify":
            ok, detail = run_process([
                sys.executable,
                "ANA_MAX/dev_artifacts/scripts/ana_post_reload_verify.py",
                "--mcp-url",
                mcp_url,
                "--no-write",
            ], timeout=max(timeout, 120))
            return result_from_process(button, "post_reload_verify", ok, detail)
        if command == "anaMax.showRouterDecisions":
            payload = call_tool(mcp_url, "agent_coach", {
                "action": "recommend",
                "task": "Activity Bar button smoke asks for next tool",
                "max_tools": 5,
                "include_prompt": False,
            }, timeout=timeout)
            if payload.get("success") and payload.get("data", {}).get("primary_tool"):
                if payload.get("data", {}).get("severity") not in (None, "ok"):
                    return warn_result(button, "agent_coach_recommend", str(payload.get("message") or "recommended"))
                return pass_result(button, "agent_coach_recommend", str(payload.get("message") or "recommended"))
            return fail_result(button, "agent_coach_recommend", str(payload.get("error") or payload.get("message") or payload))
        if command == "anaMax.profileStatus":
            payload = call_tool(mcp_url, "tool_router", {"mode": "profile_status"}, timeout=timeout)
            if payload.get("success") and payload.get("data", {}).get("schema") == "ana.tool_router.profile_status.v1":
                return pass_result(button, "profile_status", f"tools={payload.get('data', {}).get('tools_total')}")
            return fail_result(button, "profile_status", str(payload.get("error") or payload.get("message") or payload))
        if command == "anaMax.previewRest":
            payload = call_tool(mcp_url, "session_lifecycle", {"action": "rest", "consolidate": False}, timeout=timeout)
            return pass_result(button, "rest_preview", str(payload.get("message") or "")) if payload.get("success") else fail_result(button, "rest_preview", str(payload.get("error") or payload.get("message")))
        if command == "anaMax.refreshCodeMap":
            ok, detail = run_process([sys.executable, "ANA_MAX/dev_artifacts/scripts/ana_refresh_context_maps.py"], timeout=max(timeout, 120))
            return result_from_process(button, "refresh_context_maps", ok, detail)
        if command == "anaMax.showTrustScore":
            payload = call_tool(mcp_url, "session_audit", {"action": "trust", "hours": 1, "limit": 100}, timeout=timeout)
            score = payload.get("data", {}).get("trust", {}).get("score")
            return pass_result(button, "trust_score", f"score={score}") if payload.get("success") else fail_result(button, "trust_score", str(payload.get("error") or payload.get("message")))
        if command == "anaMax.conversationAudit":
            ok, detail = run_process([
                sys.executable,
                "ANA_MAX/dev_artifacts/scripts/ana_conversation_audit.py",
                "--hours",
                "1",
                "--limit",
                "120",
            ], timeout=max(timeout, 30))
            return result_from_process(button, "conversation_audit", ok, detail)
        if command == "anaMax.liveConversationAudit":
            return pass_result(button, "conversation_audit_tail", "live tail command registered; auto-starts with Live Console")
        if command == "anaMax.identity":
            payload = call_tool(mcp_url, "ana_identity", {}, timeout=timeout)
            return pass_result(button, "identity", str(payload.get("message") or "identity")) if payload.get("success") else fail_result(button, "identity", str(payload.get("error") or payload.get("message")))
        if command == "ana.showCodexMcpConfig":
            return pass_result(button, "static", "MCP config command registered")
        if command == "anaMax.inspectRuntime":
            payload = call_tool(mcp_url, "ana_runtime_inspector", {"action": "snapshot"}, timeout=timeout)
            return pass_result(button, "runtime_inspector", str(payload.get("message") or "snapshot")) if payload.get("success") else fail_result(button, "runtime_inspector", str(payload.get("error") or payload.get("message")))
        if command == "anaMax.openDashboard":
            payload = call_tool(mcp_url, "tool_healthcheck", {"scope": "safe"}, timeout=timeout)
            return pass_result(button, "dashboard_backing", str(payload.get("message") or "tool_healthcheck")) if payload.get("success") else fail_result(button, "dashboard_backing", str(payload.get("error") or payload.get("message")))
        return pass_result(button, "static", "command registered; no non-interactive probe configured")
    except subprocess.TimeoutExpired:
        return fail_result(button, "timeout", "probe timed out")
    except Exception as exc:  # noqa: BLE001 - smoke should continue per button
        return fail_result(button, "exception", repr(exc))


def run_button_smoke(
    mcp_url: str = DEFAULT_MCP_URL,
    include_heavy: bool = False,
    include_writes: bool = False,
    include_refresh: bool = False,
    include_external: bool = False,
    timeout: int = 30,
) -> dict[str, Any]:
    buttons = extract_activity_buttons()
    command_set = declared_commands()
    try:
        names = tool_names(mcp_url, timeout=timeout)
    except Exception:
        names = set()
    results = [
        run_button_probe(
            button,
            mcp_url,
            command_set,
            names,
            include_heavy,
            include_writes,
            include_refresh,
            include_external,
            timeout,
        )
        for button in buttons
    ]
    counts = {
        status.lower(): sum(1 for item in results if item.get("status") == status)
        for status in ("PASS", "SKIP", "WARN", "FAIL")
    }
    return {
        "schema": "ana.activity_bar_button_smoke.v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "mcp_url": mcp_url,
        "policy": {
            "include_heavy": include_heavy,
            "include_writes": include_writes,
            "include_refresh": include_refresh,
            "include_external": include_external,
        },
        "summary": {
            "buttons": len(results),
            **counts,
            "status": "FAIL" if counts["fail"] else ("WARN" if counts["warn"] else "PASS"),
        },
        "results": results,
    }


def write_report(report: dict[str, Any]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"activity_bar_button_smoke_{stamp}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def print_human(report: dict[str, Any], report_path: Path | None = None) -> None:
    summary = report.get("summary", {})
    print(
        "ANA Activity Bar Button Smoke: "
        f"{summary.get('status')} "
        f"buttons={summary.get('buttons')} "
        f"pass={summary.get('pass')} "
        f"skip={summary.get('skip')} "
        f"warn={summary.get('warn')} "
        f"fail={summary.get('fail')}"
    )
    for item in report.get("results") or []:
        detail = item.get("detail") or ""
        print(f"[{item.get('status')}] {item.get('label')} -> {item.get('probe')} {detail}".rstrip())
    if report_path:
        print(f"report={report_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Smoke test ANA MAX Activity Bar button backing paths.")
    parser.add_argument("--mcp-url", default=DEFAULT_MCP_URL)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--include-heavy", action="store_true", help="Run heavy gate buttons.")
    parser.add_argument("--include-writes", action="store_true", help="Allow write/consolidation buttons.")
    parser.add_argument("--include-refresh", action="store_true", help="Allow Refresh Context Maps to mutate maps.")
    parser.add_argument("--include-external", action="store_true", help="Allow external/browser-style probes.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-write", action="store_true", help="Do not write a JSON report.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = run_button_smoke(
        mcp_url=args.mcp_url,
        include_heavy=args.include_heavy,
        include_writes=args.include_writes,
        include_refresh=args.include_refresh,
        include_external=args.include_external,
        timeout=args.timeout,
    )
    report_path = None if args.no_write else write_report(report)
    if args.json:
        print(json.dumps({**report, "report": str(report_path) if report_path else None}, indent=2, ensure_ascii=False))
    else:
        print_human(report, report_path)
    return 1 if report.get("summary", {}).get("fail") else 0


if __name__ == "__main__":
    raise SystemExit(main())
