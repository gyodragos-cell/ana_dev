from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ANA_MAX" / "chat_voice_bridge.py"


def load_script():
    ana_root = str(ROOT / "ANA_MAX")
    if ana_root not in sys.path:
        sys.path.insert(0, ana_root)
    spec = importlib.util.spec_from_file_location("chat_voice_bridge", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_full_readout_speaks_long_text_in_chunks(monkeypatch):
    script = load_script()
    spoken = []
    monkeypatch.setattr(script, "speak", lambda text: spoken.append(text))

    text = " ".join(["ANA full voice"] * 80)

    assert script.should_speak(text, max_chars=40) is False
    assert script.speak_readout(
        text,
        max_chars=40,
        full_readout=True,
        full_max_chars=2000,
        chunk_chars=120,
    ) is True

    assert len(spoken) > 1
    assert "ANA full voice" in " ".join(spoken)


def test_full_readout_still_skips_sensitive_text(monkeypatch):
    script = load_script()
    spoken = []
    monkeypatch.setattr(script, "speak", lambda text: spoken.append(text))

    assert script.speak_readout(
        "my token is secret",
        max_chars=40,
        full_readout=True,
        full_max_chars=2000,
        chunk_chars=120,
    ) is False
    assert spoken == []


def test_single_instance_lock_refuses_live_existing_pid(tmp_path, monkeypatch):
    script = load_script()
    lock_file = tmp_path / "chat_voice_bridge.pid"
    lock_file.write_text("12345", encoding="utf-8")
    monkeypatch.setattr(script, "LOCK_FILE", lock_file)
    monkeypatch.setattr(script, "is_process_alive", lambda pid: pid == 12345)

    assert script.acquire_single_instance_lock() is False
    assert lock_file.read_text(encoding="utf-8") == "12345"


def test_single_instance_lock_replaces_stale_pid(tmp_path, monkeypatch):
    script = load_script()
    lock_file = tmp_path / "chat_voice_bridge.pid"
    lock_file.write_text("12345", encoding="utf-8")
    monkeypatch.setattr(script, "LOCK_FILE", lock_file)
    monkeypatch.setattr(script, "is_process_alive", lambda pid: False)

    assert script.acquire_single_instance_lock() is True
    assert lock_file.read_text(encoding="utf-8") == str(script.os.getpid())
    script.release_single_instance_lock()
    assert not lock_file.exists()
