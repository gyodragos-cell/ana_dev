"""VS Code extension scaffold tests."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_extension_commands_declared():
    """Package manifest should expose v23 commands."""
    package = json.loads((ROOT / "vscode_extension" / "package.json").read_text(encoding="utf-8"))
    commands = {item["command"] for item in package["contributes"]["commands"]}

    assert "anaMax.executeTool" in commands
    assert "anaMax.inspectRuntime" in commands
    assert "anaMax.showRouterDecisions" in commands
    assert "anaMax.showObservability" in commands


def test_extension_safe_mode_ui_enforcement_present():
    """Extension source should keep safe-mode checks around tool execution."""
    source = (ROOT / "vscode_extension" / "extension.js").read_text(encoding="utf-8")

    assert "safeMode" in source
    assert "blocks tool execution" in source
    assert "requestJson" in source


def test_extension_confirmation_dialogs_present():
    """Extension should include explicit dangerous-action confirmations."""
    source = (ROOT / "vscode_extension" / "extension.js").read_text(encoding="utf-8")

    assert "Allow write?" in source
    assert "Allow subprocess?" in source
    assert "Allow network call?" in source
    assert "Allow tool execution?" in source
    assert "confirmDangerousAction" in source
