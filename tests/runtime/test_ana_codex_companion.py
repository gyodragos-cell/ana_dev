from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "ana_codex_companion.py"


def load_script():
    script_dir = str(SCRIPT.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location("ana_codex_companion", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_debate_passes_when_ana_has_no_challenge():
    script = load_script()
    report = {
        "health": {"status": "online", "mcp_ready": True},
        "router": {"headline": "Use compact context."},
        "coach": {"severity": "ok", "headline": "Telemetry is calm.", "primary_tool": "code_context_pack"},
        "context": {"current_file_candidates": ["ANA_MAX/dev_artifacts/scripts/ana_codex_companion.py"]},
        "error_radar": {"count": 0},
    }

    debate = script.build_debate(report, planned_tool="code_context_pack")

    assert debate["status"] == "PASS"
    assert debate["challenges"] == []
    assert "[CODEX] I may proceed with one scoped action, then verify." in debate["lines"]


def test_build_debate_warns_when_codex_planned_tool_differs():
    script = load_script()
    report = {
        "health": {"status": "online", "mcp_ready": True},
        "router": {"headline": "Use runtime diagnostics.", "steps": ["Run tool_healthcheck."]},
        "coach": {
            "severity": "warn",
            "headline": "Agent may be looping.",
            "primary_tool": "tool_healthcheck",
            "signals": [{"type": "repeated_action"}],
            "next_action": "Call tool_healthcheck before more context.",
        },
        "context": {"current_file_candidates": ["ANA_MAX/dev_artifacts/scripts/ana_codex_companion.py"]},
        "error_radar": {"count": 1, "recommended_next_step": "Review dirty tree."},
    }

    debate = script.build_debate(report, planned_tool="code_context_pack")

    assert debate["status"] == "WARN"
    assert any("Codex planned code_context_pack" in item for item in debate["challenges"])
    assert any("Error Radar has 1 finding" in item for item in debate["challenges"])
    assert debate["next_action"] == "Call tool_healthcheck before more context."


def test_run_companion_compacts_mcp_tool_outputs(monkeypatch):
    script = load_script()

    monkeypatch.setattr(script, "json_request", lambda url, timeout=30: {"status": "online", "mcp_ready": True})
    seen_calls = []

    def fake_call_tool(mcp_url, name, arguments=None, timeout=30):
        seen_calls.append((name, arguments or {}))
        if name == "foreground_ui_snapshot":
            return {
                "success": True,
                "message": "snapshot",
                "data": {"active_app": "Code", "title": "Lab", "buttons": ["A", "B"]},
            }
        if name == "tool_router":
            return {
                "success": True,
                "message": "router",
                "data": {"mode": "project_state", "recommended_tools": ["code_context_pack"], "steps": ["Inspect context."]},
            }
        if name == "agent_coach":
            return {
                "success": True,
                "message": "coach",
                "data": {
                    "severity": "ok",
                    "headline": "coach ok",
                    "primary_tool": "code_context_pack",
                    "tool_stack": ["code_context_pack"],
                    "coach": {"signals": []},
                    "next_action": "Inspect the top candidate.",
                },
            }
        if name == "code_context_pack":
            return {
                "success": True,
                "message": "context",
                "data": {
                    "compressed_state": {
                        "current_file_candidates": ["ANA_MAX/dev_artifacts/scripts/ana_codex_companion.py"],
                        "evidence": ["foreground_ui_snapshot", "ana_code_map"],
                    },
                    "code_map": {"results": [{"file": "ANA_MAX/dev_artifacts/scripts/ana_codex_companion.py", "score": 4}]},
                    "graph_map": {"results": []},
                },
            }
        if name == "error_radar":
            return {"success": True, "message": "0 findings", "data": {"count": 0, "summary": {}}}
        raise AssertionError(name)

    monkeypatch.setattr(script, "call_tool", fake_call_tool)

    report = script.run_companion("test goal", planned_tool="code_context_pack")

    assert report["schema"] == "ana.codex_companion.v1"
    assert report["status"] == "PASS"
    assert report["context"]["current_file_candidates"] == ["ANA_MAX/dev_artifacts/scripts/ana_codex_companion.py"]
    assert report["tool_healthcheck"] is None
    snapshot_args = next(args for name, args in seen_calls if name == "foreground_ui_snapshot")
    assert snapshot_args["max_elements"] == "20"
