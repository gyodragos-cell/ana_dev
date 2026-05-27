"""Recommend the smallest useful ANA MAX tool set for a task or failure."""

from __future__ import annotations

import re
from typing import Any, Dict, List

from tools.base import Tool, ToolDefinition, ToolParameter, ToolResult, ToolStatus


PLAYBOOKS: Dict[str, Dict[str, Any]] = {
    "project_state": {
        "headline": "Understand the current project state before editing.",
        "tools": [
            "workspace_situational_awareness",
            "project_navigator",
            "git_operations",
            "error_radar",
        ],
        "steps": [
            "Capture compact workspace/git/error context.",
            "Open only the relevant docs or files.",
            "Decide the smallest next action.",
        ],
    },
    "failure": {
        "headline": "Diagnose the first real failure and avoid retry loops.",
        "tools": [
            "error_radar",
            "agent_coach",
            "ana_memory",
            "debugger",
            "tool_healthcheck",
        ],
        "steps": [
            "Read the normalized error and auto_guidance if present.",
            "Search known fixes before another retry.",
            "Retry once with changed input, then verify.",
        ],
    },
    "code_change": {
        "headline": "Make a scoped code change and verify it.",
        "tools": [
            "project_navigator",
            "code_search",
            "file_patch",
            "edit",
            "qa_testing",
            "tool_healthcheck",
        ],
        "steps": [
            "Inspect surrounding code and docs.",
            "Patch the smallest safe surface.",
            "Run compile/tests or targeted healthcheck.",
        ],
    },
    "ui_desktop": {
        "headline": "Observe the UI before acting on it.",
        "tools": [
            "foreground_ui_snapshot",
            "windows_uia_bridge",
            "desktop_capture",
            "ocr_tool",
            "window_manager",
            "uia_click",
            "uia_type",
        ],
        "steps": [
            "Read visible UI state first.",
            "Choose one target and one action.",
            "Verify with a fresh snapshot after acting.",
        ],
        "guardrail": "UI mutation tools require explicit confirmation.",
    },
    "runtime_deep": {
        "headline": "Use under-the-hood diagnostics only when normal evidence is not enough.",
        "tools": [
            "tool_healthcheck",
            "event_stream",
            "windows_deep_sight",
            "windows_insight",
            "frida_instrument",
        ],
        "steps": [
            "Start with health and logs.",
            "Inspect runtime/process state if the issue is below source-level visibility.",
            "Use Frida only for authorized runtime instrumentation.",
        ],
        "guardrail": "Frida and deep diagnostics are controlled lab tools.",
    },
    "release_sync": {
        "headline": "Keep the public release clean and synced only when ship-safe.",
        "tools": [
            "privacy_shield",
            "git_operations",
            "tool_healthcheck",
            "session_checkpoint",
        ],
        "steps": [
            "Decide ship-safe vs lab-only.",
            "Remove private paths, logs, memory, screenshots, and secrets.",
            "Update README/setup/changelog/project map and tests.",
        ],
    },
    "memory_handoff": {
        "headline": "Persist useful context without saving raw private chat.",
        "tools": [
            "session_checkpoint",
            "session_rem_sleep",
            "conversation_learning",
            "ana_memory",
            "session_log_miner",
        ],
        "steps": [
            "Write a compact handoff or lesson.",
            "Include current goal, files changed, validation, risks, and sync status.",
            "Avoid private raw logs unless explicitly needed.",
        ],
    },
}


KEYWORDS = [
    ("ui_desktop", r"\b(ui|window|screen|desktop|click|type|ocr|screenshot|vision|button|fereastra|ecran)\b"),
    ("runtime_deep", r"\b(frida|hook|process|module|runtime|watchdog|under.?the.?hood|sub capota|deep)\b"),
    ("release_sync", r"\b(release|github|public|sync|ship|publish|export|changelog)\b"),
    ("memory_handoff", r"\b(memory|handoff|checkpoint|lesson|istoric|history|remember|rem|sleep|somn|recalibrate|retrospective)\b"),
    ("failure", r"\b(error|failed|failure|traceback|exception|bug|blocked|timeout|eroare|fail)\b"),
    ("code_change", r"\b(code|edit|patch|fix|implement|test|compile|refactor|fisier|file)\b"),
]


class ToolRouterTool(Tool):
    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="tool_router",
            description=(
                "Recommend a compact ANA MAX MCP tool stack for a task, error, "
                "or context. Read-only. Helps agents avoid using all tools blindly."
            ),
            parameters=[
                ToolParameter("task", "Task, goal, or problem description", "string", False, ""),
                ToolParameter("error", "Optional error text or failed tool result", "string", False, ""),
                ToolParameter(
                    "mode",
                    "auto, project_state, failure, code_change, ui_desktop, runtime_deep, release_sync, memory_handoff",
                    "string",
                    False,
                    "auto",
                    choices=[
                        "auto",
                        "project_state",
                        "failure",
                        "code_change",
                        "ui_desktop",
                        "runtime_deep",
                        "release_sync",
                        "memory_handoff",
                    ],
                ),
                ToolParameter("max_tools", "Maximum recommended tools", "integer", False, 5),
            ],
            category="ai_core",
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        task = str(kwargs.get("task") or "")
        error = str(kwargs.get("error") or "")
        mode = str(kwargs.get("mode") or "auto")
        max_tools = max(1, min(int(kwargs.get("max_tools") or 5), 10))

        selected_mode = mode if mode != "auto" else self._classify(task, error)
        playbook = PLAYBOOKS.get(selected_mode, PLAYBOOKS["project_state"])
        tools = playbook["tools"][:max_tools]

        data = {
            "schema": "ana.tool_router.v1",
            "mode": selected_mode,
            "headline": playbook["headline"],
            "recommended_tools": tools,
            "steps": playbook["steps"],
            "guardrail": playbook.get("guardrail", ""),
            "why_not_all_tools": "Use the smallest useful stack; escalate only when evidence requires it.",
        }
        return ToolResult(
            status=ToolStatus.SUCCESS,
            data=data,
            message=f"Recommended {len(tools)} tools for {selected_mode}.",
        )

    def _classify(self, task: str, error: str) -> str:
        text = f"{task}\n{error}".lower()
        if error.strip():
            return "failure"
        for mode, pattern in KEYWORDS:
            if re.search(pattern, text, re.IGNORECASE):
                return mode
        return "project_state"
