from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
ANA_MAX_DIR = ROOT / "ANA_MAX"
SCRIPT = ANA_MAX_DIR / "dev_artifacts" / "scripts" / "ana_voice_operator_smoke.py"
if str(ANA_MAX_DIR) not in sys.path:
    sys.path.insert(0, str(ANA_MAX_DIR))

from tools.conversation_audit import append_conversation_audit


def load_script():
    script_dir = str(SCRIPT.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location("ana_voice_operator_smoke", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_voice_operator_smoke_builds_unique_phrase():
    script = load_script()

    phrase = script.build_phrase("test-one")

    assert "ANA voice operator smoke test-one" in phrase
    assert "O singura voce principala" in phrase


def test_voice_operator_smoke_finds_voice_queue_audit(tmp_path: Path):
    script = load_script()
    audit_path = tmp_path / "conversation_audit.jsonl"
    phrase = script.build_phrase("unit")

    append_conversation_audit("voice_queue", phrase, spoken=True, path=audit_path)

    found = script.find_audit_phrase(phrase, audit_path)

    assert found is not None
    assert found["source"] == "voice_queue"
    assert found["spoken"] is True
