from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "ana_voice_inbox.py"


def load_script():
    script_dir = str(SCRIPT.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location("ana_voice_inbox", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_mock_voice_inbox_no_write_returns_text():
    script = load_script()
    args = argparse.Namespace(
        duration=8,
        language="",
        copy=False,
        auto_submit=False,
        press_enter=False,
        submit_prefix=["codex", "ana"],
        allowed_title=["Visual Studio Code", "Code", "Codex", "ChatGPT"],
        no_write=True,
        mock_text="Codex continua cu ANA tools",
    )

    payload = script.run(args)

    assert payload["schema"] == "ana.voice_inbox.v1"
    assert payload["success"] is True
    assert payload["data"]["record"]["source"] == "mock"
    assert payload["data"]["record"]["text"] == "Codex continua cu ANA tools"


def test_voice_inbox_skips_sensitive_text():
    script = load_script()
    record = script.build_record(
        "my token is secret",
        confidence=1.0,
        source="mock",
        copied=False,
    )

    assert record["success"] is False
    assert record["text"] == ""
    assert record["sensitive_skipped"] is True


def test_voice_inbox_prefix_and_allowed_title_helpers():
    script = load_script()

    should_submit, body = script.strip_submit_prefix("Codex continua cu ANA", ["codex", "ana"])
    assert should_submit is True
    assert body == "continua cu ANA"

    should_submit, body = script.strip_submit_prefix("Salut colegu", ["codex", "ana"])
    assert should_submit is False
    assert body == "Salut colegu"

    assert script.title_allowed("Untitled (Workspace) - Visual Studio Code", ["Visual Studio Code"]) is True
    assert script.title_allowed("Calculator", ["Visual Studio Code"]) is False


def test_voice_inbox_record_can_store_submit_evidence():
    script = load_script()
    record = script.build_record(
        "Codex test",
        confidence=1.0,
        source="mock",
        copied=True,
        submitted=True,
        submit_title="Untitled (Workspace) - Visual Studio Code",
    )

    assert record["submitted_to_focused_window"] is True
    assert "Visual Studio Code" in record["submit_title"]


def test_voice_inbox_save_record_writes_conversation_audit(tmp_path: Path, monkeypatch):
    script = load_script()
    captured = []
    monkeypatch.setattr(script, "MEMORY_DIR", tmp_path)
    monkeypatch.setattr(script, "INBOX_JSONL", tmp_path / "voice_inbox.jsonl")
    monkeypatch.setattr(script, "LATEST_TXT", tmp_path / "voice_inbox_latest.txt")
    monkeypatch.setattr(script, "append_conversation_audit", lambda *args, **kwargs: captured.append((args, kwargs)))

    record = script.build_record(
        "Codex audit test",
        confidence=1.0,
        source="mock",
        copied=True,
        submitted=True,
        submit_title="Untitled (Workspace) - Visual Studio Code",
    )
    script.save_record(record)

    assert script.INBOX_JSONL.exists()
    assert script.LATEST_TXT.read_text(encoding="utf-8") == "Codex audit test"
    assert captured[0][0] == ("voice_inbox", "Codex audit test")
    assert captured[0][1]["copied"] is True
    assert captured[0][1]["submitted"] is True
