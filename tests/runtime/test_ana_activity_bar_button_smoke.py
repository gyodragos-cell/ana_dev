from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "ana_activity_bar_button_smoke.py"


def load_script():
    script_dir = str(SCRIPT.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location("ana_activity_bar_button_smoke", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_extract_activity_buttons_from_extension_source():
    script = load_script()

    buttons = script.extract_activity_buttons(
        '''
        actionItem("Health JSON", "anaMax.showHealthJson", "json", "Show raw ANA MAX health JSON."),
        actionItem("Open Dashboard", "anaMax.openDashboard", "dashboard", "Open the ANA dashboard URL.")
        '''
    )

    assert buttons == [
        {
            "label": "Health JSON",
            "command": "anaMax.showHealthJson",
            "icon": "json",
            "tooltip": "Show raw ANA MAX health JSON.",
        },
        {
            "label": "Open Dashboard",
            "command": "anaMax.openDashboard",
            "icon": "dashboard",
            "tooltip": "Open the ANA dashboard URL.",
        },
    ]


def test_activity_bar_button_list_matches_current_extension():
    script = load_script()

    buttons = script.extract_activity_buttons()
    labels = {button["label"] for button in buttons}
    commands = {button["command"] for button in buttons}

    assert len(buttons) >= 30
    assert "Nucleus Smoke" in labels
    assert "Codex Companion" in labels
    assert "Voice Inbox" in labels
    assert "Conversation Audit" in labels
    assert "Live Conversation Audit" in labels
    assert "Voice Operator Smoke" in labels
    assert "Refresh Context Maps" in labels
    assert "anaMax.operatorStatus" in commands
    assert "anaMax.codexCompanion" in commands
    assert "anaMax.voiceInbox" in commands
    assert "anaMax.conversationAudit" in commands
    assert "anaMax.liveConversationAudit" in commands
    assert "anaMax.voiceOperatorSmoke" in commands
    assert "anaMax.refreshCodeMap" in commands


def test_button_probe_fails_when_command_is_not_declared():
    script = load_script()
    button = {"label": "Missing", "command": "anaMax.missing", "icon": "", "tooltip": ""}

    result = script.run_button_probe(
        button,
        "http://127.0.0.1:8766/mcp",
        command_set=set(),
        names=set(),
        include_heavy=False,
        include_writes=False,
        include_refresh=False,
        include_external=False,
        timeout=1,
    )

    assert result["status"] == "FAIL"
    assert result["probe"] == "command_registration"


def test_button_probe_skips_write_heavy_refresh_and_external_by_default():
    script = load_script()
    command_set = {
        "anaMax.checkpoint",
        "anaMax.noReloadGate",
        "anaMax.refreshCodeMap",
        "anaMax.openDashboard",
        "anaMax.voiceInbox",
        "anaMax.voiceOperatorSmoke",
    }

    cases = [
        ("anaMax.checkpoint", "write_gated"),
        ("anaMax.noReloadGate", "heavy_gated"),
        ("anaMax.refreshCodeMap", "refresh_gated"),
        ("anaMax.openDashboard", "external_gated"),
        ("anaMax.voiceInbox", "interactive_gated"),
        ("anaMax.voiceOperatorSmoke", "interactive_gated"),
    ]
    for command, expected_probe in cases:
        result = script.run_button_probe(
            {"label": command, "command": command, "icon": "", "tooltip": ""},
            "http://127.0.0.1:8766/mcp",
            command_set=command_set,
            names=set(),
            include_heavy=False,
            include_writes=False,
            include_refresh=False,
            include_external=False,
            timeout=1,
        )
        assert result["status"] == "SKIP"
        assert result["probe"] == expected_probe


def test_write_gated_buttons_have_real_include_writes_probes(monkeypatch):
    script = load_script()
    tool_calls = []
    process_calls = []

    def fake_call_tool(mcp_url, name, arguments, timeout=30):
        tool_calls.append((name, arguments))
        return {"success": True, "message": f"{name} ok"}

    def fake_run_process(args, timeout=120):
        process_calls.append(args)
        return True, "checkpoint saved"

    monkeypatch.setattr(script, "call_tool", fake_call_tool)
    monkeypatch.setattr(script, "run_process", fake_run_process)
    command_set = {
        "anaMax.wakeSession",
        "anaMax.checkpoint",
        "anaMax.runRemSleep",
        "anaMax.generateSessionAudit",
    }

    cases = [
        ("anaMax.wakeSession", "session_lifecycle_wake"),
        ("anaMax.checkpoint", "local_checkpoint"),
        ("anaMax.runRemSleep", "session_lifecycle_rest_consolidate"),
        ("anaMax.generateSessionAudit", "session_audit_generate"),
    ]

    for command, expected_probe in cases:
        result = script.run_button_probe(
            {"label": command, "command": command, "icon": "", "tooltip": ""},
            "http://127.0.0.1:8766/mcp",
            command_set=command_set,
            names=set(),
            include_heavy=False,
            include_writes=True,
            include_refresh=False,
            include_external=False,
            timeout=1,
        )
        assert result["status"] == "PASS"
        assert result["probe"] == expected_probe

    assert ("session_lifecycle", {"action": "wake"}) in tool_calls
    assert any(call[0] == "session_lifecycle" and call[1].get("consolidate") is True for call in tool_calls)
    assert any(call[0] == "session_audit" and call[1]["action"] == "generate" for call in tool_calls)
    assert any("ana_local_checkpoint.py" in item for item in process_calls[0])


def test_start_runtime_probe_passes_when_mcp_is_ready(monkeypatch):
    script = load_script()
    button = {"label": "Start", "command": "anaMax.startRuntime", "icon": "", "tooltip": ""}
    monkeypatch.setattr(script, "json_request", lambda url, timeout=1: {"mcp_ready": True, "tools_count": 90})

    result = script.run_button_probe(
        button,
        "http://127.0.0.1:8766/mcp",
        command_set={"anaMax.startRuntime"},
        names=set(),
        include_heavy=False,
        include_writes=False,
        include_refresh=False,
        include_external=False,
        timeout=1,
    )

    assert result["status"] == "PASS"
    assert result["probe"] == "health_running"


def test_conversation_audit_button_runs_summary_script(monkeypatch):
    script = load_script()
    process_calls = []

    def fake_run_process(args, timeout=120):
        process_calls.append(args)
        return True, "ANA Conversation Audit: PASS events=2 spoken=2"

    monkeypatch.setattr(script, "run_process", fake_run_process)
    result = script.run_button_probe(
        {"label": "Conversation Audit", "command": "anaMax.conversationAudit", "icon": "", "tooltip": ""},
        "http://127.0.0.1:8766/mcp",
        command_set={"anaMax.conversationAudit"},
        names=set(),
        include_heavy=False,
        include_writes=False,
        include_refresh=False,
        include_external=False,
        timeout=1,
    )

    assert result["status"] == "PASS"
    assert result["probe"] == "conversation_audit"
    assert any("ana_conversation_audit.py" in item for item in process_calls[0])


def test_codex_companion_button_runs_companion_script(monkeypatch):
    script = load_script()
    seen = {}

    def fake_run_process(args, timeout=120):
        seen["args"] = args
        return True, "ANA Codex Companion: PASS goal=button smoke"

    monkeypatch.setattr(script, "run_process", fake_run_process)

    result = script.run_button_probe(
        {"label": "Codex Companion", "command": "anaMax.codexCompanion", "icon": "", "tooltip": ""},
        "http://127.0.0.1:8766/mcp",
        command_set={"anaMax.codexCompanion"},
        names=set(),
        include_heavy=False,
        include_writes=False,
        include_refresh=False,
        include_external=False,
        timeout=1,
    )

    assert result["status"] == "PASS"
    assert result["probe"] == "codex_companion"
    assert any("ana_codex_companion.py" in item for item in seen["args"])
    assert "--no-write" in seen["args"]


def test_result_from_process_preserves_warning_status():
    script = load_script()
    button = {"label": "Nucleus", "command": "anaMax.nucleusSmoke", "icon": "", "tooltip": ""}

    result = script.result_from_process(button, "nucleus_smoke", True, "ANA Nucleus: WARN (9 pass / 1 warn / 0 fail)")

    assert result["status"] == "WARN"


def test_result_from_process_does_not_treat_zero_warn_counter_as_warning():
    script = load_script()
    button = {"label": "Nucleus", "command": "anaMax.nucleusSmoke", "icon": "", "tooltip": ""}

    result = script.result_from_process(button, "nucleus_smoke", True, "ANA Nucleus: PASS (10 pass / 0 warn / 0 fail)")

    assert result["status"] == "PASS"
