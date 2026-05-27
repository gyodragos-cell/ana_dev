"""VS Code extension scaffold tests."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def extension_source_path() -> Path:
    src_path = ROOT / "vscode_extension" / "src" / "extension.js"
    if src_path.exists():
        return src_path
    return ROOT / "vscode_extension" / "extension.js"


def test_extension_commands_declared():
    """Package manifest should expose v23 commands."""
    package = json.loads((ROOT / "vscode_extension" / "package.json").read_text(encoding="utf-8"))
    commands = {item["command"] for item in package["contributes"]["commands"]}

    assert "anaMax.executeTool" in commands
    assert "anaMax.inspectRuntime" in commands
    assert "anaMax.showRouterDecisions" in commands
    assert "anaMax.wakeSession" in commands
    assert "anaMax.previewRest" in commands
    assert "anaMax.showObservability" in commands


def test_extension_exposes_antigravity_visible_start_ui():
    """VS Code-compatible IDEs should get a visible ANA MAX runtime surface."""
    package = json.loads((ROOT / "vscode_extension" / "package.json").read_text(encoding="utf-8"))
    contributes = package["contributes"]

    assert "anaMax" in contributes["viewsContainers"]["activitybar"][0]["id"]
    assert contributes["views"]["anaMax"][0]["id"] == "anaMax.actions"

    view_title_commands = {
        item["command"]
        for item in contributes["menus"]["view/title"]
        if item.get("when") == "view == anaMax.actions"
    }
    editor_title_commands = {item["command"] for item in contributes["menus"]["editor/title"]}

    assert "anaMax.startRuntime" in view_title_commands
    assert "anaMax.wakeSession" in view_title_commands
    assert "anaMax.previewRest" in view_title_commands
    assert "anaMax.startRuntime" in editor_title_commands

    palette_commands = {item["command"] for item in contributes["menus"]["commandPalette"]}
    assert "anaMax.wakeSession" in palette_commands
    assert "anaMax.previewRest" in palette_commands
    assert "anaMax.runRemSleep" in palette_commands


def test_extension_safe_mode_ui_enforcement_present():
    """Extension source should keep safe-mode checks around tool execution."""
    source = extension_source_path().read_text(encoding="utf-8")

    assert "safeMode" in source
    assert "blocks tool execution" in source
    assert "requestJson" in source
    assert "Start Runtime" in source
    assert "Beginner Flow" in source
    assert "Start here" in source
    assert "Daily work" in source
    assert "Rest Preview" in source
    assert "registerTreeDataProvider" in source


def test_extension_confirmation_dialogs_present():
    """Extension should include explicit dangerous-action confirmations."""
    source = extension_source_path().read_text(encoding="utf-8")

    assert "Allow write?" in source
    assert "Allow subprocess?" in source
    assert "Allow network call?" in source
    assert "Allow tool execution?" not in source
    assert "confirmDangerousAction" in source
    assert "readOnlyTools" in source
    assert '"tool_router"' in source
    assert '"agent_coach"' in source
    assert '"session_lifecycle"' in source


def test_extension_uses_lifecycle_for_wake_and_rest():
    """Cockpit should use session_lifecycle for wake/rest flows."""
    source = extension_source_path().read_text(encoding="utf-8")

    assert "session_lifecycle" in source
    assert 'action: "wake"' in source
    assert 'consolidate: false' in source
    assert 'consolidate: true' in source
