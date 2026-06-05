"""Tests for the short ANA MCP CLI wrapper."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "ana_mcp_call.py"


def load_script():
    spec = importlib.util.spec_from_file_location("ana_mcp_call", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_unwrap_tool_response_preserves_normalized_tool_error():
    script = load_script()

    response = {
        "result": {
            "content": [
                {
                    "type": "text",
                    "text": '{"success": false, "data": null, "message": "", "error": "Unknown tool: demo"}',
                }
            ]
        }
    }

    assert script.unwrap_tool_response(response) == {
        "success": False,
        "data": None,
        "message": "",
        "error": "Unknown tool: demo",
    }


def test_unwrap_tool_response_reports_non_json_content():
    script = load_script()

    response = {"result": {"content": [{"type": "text", "text": "not json"}]}}

    payload = script.unwrap_tool_response(response)

    assert payload["success"] is False
    assert payload["error"] == "non-JSON tool response"
    assert payload["text"] == "not json"


def test_call_tool_returns_failure_exit_for_normalized_failure(monkeypatch, capsys):
    script = load_script()

    def fake_rpc(mcp_url, method, params=None, timeout=20):
        assert method == "tools/call"
        assert params == {"name": "definitely_missing_tool", "arguments": {}}
        return {
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": '{"success": false, "data": null, "message": "", "error": "Unknown tool: definitely_missing_tool"}',
                    }
                ]
            }
        }

    monkeypatch.setattr(script, "rpc", fake_rpc)

    exit_code = script.call_tool(
        "http://127.0.0.1:8766/mcp",
        20,
        "definitely_missing_tool",
        {},
        raw=False,
    )

    output = capsys.readouterr().out
    assert exit_code == 2
    assert "Unknown tool: definitely_missing_tool" in output


def test_show_schema_returns_named_tool(monkeypatch, capsys):
    script = load_script()

    def fake_rpc(mcp_url, method, params=None, timeout=20):
        assert method == "tools/list"
        return {
            "result": {
                "tools": [
                    {
                        "name": "input_api_probe",
                        "description": "demo",
                        "inputSchema": {"type": "object", "properties": {"operation": {"type": "string"}}},
                    }
                ]
            }
        }

    monkeypatch.setattr(script, "rpc", fake_rpc)

    exit_code = script.show_schema("http://127.0.0.1:8766/mcp", 20, "input_api_probe")

    output = capsys.readouterr().out
    assert exit_code == 0
    assert '"name": "input_api_probe"' in output
    assert '"operation"' in output


def test_show_schema_returns_failure_for_missing_tool(monkeypatch, capsys):
    script = load_script()

    def fake_rpc(mcp_url, method, params=None, timeout=20):
        assert method == "tools/list"
        return {"result": {"tools": [{"name": "tool_router"}]}}

    monkeypatch.setattr(script, "rpc", fake_rpc)

    exit_code = script.show_schema("http://127.0.0.1:8766/mcp", 20, "definitely_missing_tool")

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "tool not found: definitely_missing_tool" in output
