from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ANA_MAX_DIR = ROOT / "ANA_MAX"
SCRIPT = ANA_MAX_DIR / "dev_artifacts" / "scripts" / "ana_conversation_audit.py"
if str(ANA_MAX_DIR) not in sys.path:
    sys.path.insert(0, str(ANA_MAX_DIR))

from tools.conversation_audit import append_conversation_audit, summarize_conversation_audit


def load_script():
    script_dir = str(SCRIPT.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location("ana_conversation_audit", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_conversation_audit_appends_and_summarizes(tmp_path: Path):
    path = tmp_path / "conversation_audit.jsonl"

    entry = append_conversation_audit(
        "voice_queue",
        "ANA guard ready",
        spoken=True,
        path=path,
    )
    append_conversation_audit(
        "clipboard_chat",
        "copied Codex answer",
        spoken=True,
        path=path,
    )

    summary = summarize_conversation_audit(path=path, hours=1, limit=10)

    assert entry["schema"] == "ana.conversation_audit.entry.v1"
    assert summary["status"] == "PASS"
    assert summary["events"] == 2
    assert summary["spoken_events"] == 2
    assert summary["sources"] == {"clipboard_chat": 1, "voice_queue": 1}


def test_conversation_audit_skips_sensitive_text(tmp_path: Path):
    path = tmp_path / "conversation_audit.jsonl"

    entry = append_conversation_audit(
        "clipboard_chat",
        "my api key is abc",
        spoken=False,
        path=path,
    )
    summary = summarize_conversation_audit(path=path, hours=1, limit=10)

    assert entry["text"] == ""
    assert entry["text_digest"] == ""
    assert entry["sensitive_skipped"] is True
    assert summary["sensitive_skipped"] == 1


def test_conversation_audit_redacts_windows_user_paths(tmp_path: Path):
    path = tmp_path / "conversation_audit.jsonl"

    entry = append_conversation_audit(
        "voice_queue",
        r"Live behavior check start: c:\Users\billy\Desktop\ana_dev\ANA_MAX\dev_artifacts\scripts\ana_live_behavior_check.py",
        spoken=True,
        metadata={"script": r"C:\Users\billy\Desktop\ana_dev\ANA_MAX\dev_artifacts\scripts\ana_live_behavior_check.py"},
        path=path,
    )

    assert "local path" in entry["text"]
    assert "Users" not in entry["text"]
    assert "billy" not in entry["text"]
    assert entry["metadata"]["script"] == "local path"
    assert entry["sensitive_skipped"] is False


def test_conversation_audit_cli_uses_summary(monkeypatch, capsys):
    script = load_script()

    monkeypatch.setattr(
        script,
        "summarize_conversation_audit",
        lambda hours, limit: {
            "schema": "ana.conversation_audit.summary.v1",
            "status": "PASS",
            "path": "memory/conversation_audit.jsonl",
            "events": 1,
            "spoken_events": 1,
            "sensitive_skipped": 0,
            "sources": {"voice_inbox": 1},
            "message": "Conversation audit PASS: 1 events, 1 spoken.",
            "latest": [{"ts": "2026-06-02T00:00:00Z", "source": "voice_inbox", "text": "codex test"}],
        },
    )

    assert script.main(["--hours", "1", "--limit", "5"]) == 0
    output = capsys.readouterr().out
    assert "ANA Conversation Audit: PASS events=1 spoken=1" in output
    assert "voice_inbox=1" in output
