"""Tests for live tool surface drift checker."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "ana_live_tool_surface_check.py"


def load_script():
    script_dir = str(SCRIPT.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location("ana_live_tool_surface_check", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_live_tool_surface_check_pass(monkeypatch, capsys):
    script = load_script()
    monkeypatch.setattr(script.ana_operator_status, "live_tool_surface", lambda mcp_url: {
        "status": "PASS",
        "live_count": 90,
        "manifest_count": 90,
        "extra_live": [],
        "missing_live": [],
    })

    code = script.main([])

    assert code == 0
    assert "PASS(live=90,manifest=90,extra=0,missing=0)" in capsys.readouterr().out


def test_live_tool_surface_check_warns_on_extra_live(monkeypatch, capsys):
    script = load_script()
    monkeypatch.setattr(script.ana_operator_status, "live_tool_surface", lambda mcp_url: {
        "status": "WARN",
        "live_count": 91,
        "manifest_count": 90,
        "extra_live": ["stale_tool"],
        "missing_live": [],
    })

    code = script.main([])

    output = capsys.readouterr().out
    assert code == 1
    assert "WARN(live=91,manifest=90,extra=1,missing=0)" in output
    assert "extra_live=stale_tool" in output
