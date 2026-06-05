from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "ana_conversation_audit_tail.py"


def load_script():
    script_dir = str(SCRIPT.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location("ana_conversation_audit_tail", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_tail_formats_conversation_entry():
    script = load_script()
    line = json.dumps(
        {
            "ts": "2026-06-02T03:00:00Z",
            "source": "voice_queue",
            "spoken": True,
            "text": "ANA guard ready",
        }
    )

    assert script.parse_line(line) == "2026-06-02T03:00:00Z source=voice_queue spoken=yes text=ANA guard ready"


def test_tail_marks_skipped_entry():
    script = load_script()
    line = json.dumps(
        {
            "ts": "2026-06-02T03:00:00Z",
            "source": "clipboard_chat_skipped",
            "spoken": False,
            "text": "",
            "sensitive_skipped": True,
        }
    )

    output = script.parse_line(line)

    assert "source=clipboard_chat_skipped" in output
    assert "spoken=no skipped=yes" in output
    assert "text=[skipped]" in output
