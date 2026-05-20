#!/usr/bin/env python3
"""
ANA MAX - MCP stdio wrapper.

Exposes a focused set of ANA tools over stdin/stdout for MCP clients.
"""

from __future__ import annotations

import io
import json
import logging
import os
import sys
from pathlib import Path

os.environ["ANA_MCP_MODE"] = "1"

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

log_dir = BASE_DIR / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.ERROR, filename=str(log_dir / "mcp_stdio.log"))

from tools.base import registry  # noqa: E402

_tools_loaded = False


def load_tools():
    """Load the focused MCP stdio tool set."""
    from tools.ana_context_tool import AnaContextTool
    from tools.browser_control import BrowserControlTool
    from tools.code import CodeTool
    from tools.code_search import CodeSearchTool
    from tools.debugger_tool import DebuggerTool
    from tools.desktop_capture import DesktopCaptureTool
    from tools.desktop_control_tool import DesktopControlTool
    from tools.edit_tool import EditTool
    from tools.files import FilesTool
    from tools.foreground_ui_snapshot import ForegroundUISnapshotTool
    from tools.frida_automation import FridaTool
    from tools.git_tool import GitTool
    from tools.live_desktop_viewer import LiveDesktopViewerTool
    from tools.memory_tool import MemoryTool
    from tools.security_tool import SecurityTool
    from tools.smart_search_tool import SmartSearchTool
    from tools.system import SystemTool
    from tools.task_tool import TaskTool
    from tools.terminal_tool import TerminalTool
    from tools.web import WebTool
    from tools.windows_deep_sight import WindowsDeepSightTool
    from tools.windows_insight_tool import WindowsInsightTool
    from tools.windows_uia_bridge import WindowsUiaBridgeTool

    tools = [
        FilesTool(),
        SystemTool(),
        CodeTool(),
        WebTool(),
        GitTool(),
        MemoryTool(),
        SmartSearchTool(),
        AnaContextTool(),
        DesktopCaptureTool(),
        WindowsUiaBridgeTool(),
        ForegroundUISnapshotTool(),
        FridaTool(),
        WindowsDeepSightTool(),
        SecurityTool(),
        TerminalTool(),
        DebuggerTool(),
        EditTool(),
        TaskTool(),
        CodeSearchTool(),
        BrowserControlTool(),
        LiveDesktopViewerTool(),
        DesktopControlTool(),
        WindowsInsightTool(),
    ]

    for tool in tools:
        registry.register(tool)

    return len(tools)


def _ensure_tools_loaded():
    global _tools_loaded
    if not _tools_loaded:
        load_tools()
        _tools_loaded = True


def _tool_schema(tool):
    definition = tool.get_definition()
    properties = {}
    required = []

    for param in definition.parameters:
        prop_schema = {"type": param.type, "description": param.description}
        if getattr(param, "choices", None):
            prop_schema["enum"] = param.choices
        if getattr(param, "default", None) is not None:
            prop_schema["default"] = param.default
        properties[param.name] = prop_schema
        if param.required:
            required.append(param.name)

    return {
        "name": definition.name,
        "description": definition.description,
        "inputSchema": {
            "type": "object",
            "properties": properties,
            "required": required,
        },
    }


def handle_request(request):
    """Handle one MCP JSON-RPC request."""
    _ensure_tools_loaded()

    method = request.get("method")
    params = request.get("params", {})
    req_id = request.get("id", 1)

    try:
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {"name": "ANA MAX", "version": "1.0"},
                    "capabilities": {
                        "tools": {"listChanged": True},
                        "resources": {"listChanged": True},
                    },
                },
            }

        if method == "tools/list":
            tools = []
            for name in registry.list_tools():
                tool = registry.get(name)
                if tool:
                    tools.append(_tool_schema(tool))
            return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools}}

        if method == "tools/call":
            tool_name = params.get("name")
            args = params.get("arguments", {})
            try:
                result = registry.execute(tool_name, **args)
                payload = {
                    "success": result.is_success,
                    "data": result.data,
                    "message": result.message,
                    "error": result.error,
                }
            except Exception as exc:
                payload = {
                    "success": False,
                    "data": None,
                    "message": f"Tool execution error: {exc}",
                    "error": str(exc),
                }

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(payload, default=str),
                        }
                    ]
                },
            }

        if method == "resources/list":
            return {"jsonrpc": "2.0", "id": req_id, "result": {"resources": []}}

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }
    except Exception as exc:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32603, "message": str(exc)},
        }


def main():
    """Run the stdio JSON-RPC loop."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
            response = handle_request(request)
            print(json.dumps(response), flush=True)
        except json.JSONDecodeError as exc:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {exc}"},
            }
            print(json.dumps(error_response), flush=True)
        except Exception as exc:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": str(exc)},
            }
            print(json.dumps(error_response), flush=True)


if __name__ == "__main__":
    main()
