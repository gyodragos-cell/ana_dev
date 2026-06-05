from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "ana_input_probe_spec.py"


def load_module():
    spec = importlib.util.spec_from_file_location("ana_input_probe_spec", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_input_probe_spec_is_lab_only_and_aggregate_only() -> None:
    module = load_module()
    spec = module.build_spec("authorized_test_app.exe", "GetAsyncKeyState", duration=60, sample_limit=9999)

    assert spec["schema"] == "ana.input_probe_spec.v1"
    assert spec["mode"] == "lab-only"
    assert spec["duration_sec_max"] == 10
    assert spec["sample_limit_max"] == 200
    assert spec["policy"]["no_raw_key_storage"] is True
    assert spec["policy"]["no_character_decoding"] is True
    assert spec["policy"]["aggregate_counts_only"] is True
    assert spec["policy"]["public_release"] == "forbidden"
    assert "String.fromCharCode" not in spec["frida_template"]
    assert "top_codes" in spec["frida_template"]


def test_raw_input_probe_does_not_touch_key_codes() -> None:
    module = load_module()
    spec = module.build_spec("authorized_test_app.exe", "RegisterRawInputDevices", duration=5, sample_limit=50)

    assert spec["risk"] == "medium"
    assert "args[0].toInt32" not in spec["frida_template"]
    assert "calls_total" in spec["allowed_output"]
