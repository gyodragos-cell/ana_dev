"""Tests for active identity surface checker."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "ana_identity_surface_check.py"


def load_script():
    spec = importlib.util.spec_from_file_location("ana_identity_surface_check", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_identity_surface_passes_current_active_files():
    script = load_script()

    report = script.build_report()

    assert report["status"] == "PASS"
    assert report["violations"] == []
    assert report["missing_required"] == []


def test_identity_surface_flags_external_tool_promotion(tmp_path: Path, monkeypatch):
    script = load_script()
    monkeypatch.setattr(script, "REPO_ROOT", tmp_path)
    doc = tmp_path / "doc.md"
    doc.write_text("ANA MAX for Codex vs AdaL promotion\n", encoding="utf-8")

    report = script.build_report(["doc.md"])

    assert report["status"] == "FAIL"
    assert {item["rule"] for item in report["violations"]} >= {
        "comparative_codex_vs",
        "comparative_vs_adal",
        "external_tool_adal",
    }


def test_identity_surface_allows_retired_tool_context(tmp_path: Path, monkeypatch):
    script = load_script()
    monkeypatch.setattr(script, "REPO_ROOT", tmp_path)
    doc = tmp_path / "doc.md"
    doc.write_text("ANA MAX Codex note: adal_integration is retired from active registration.\n", encoding="utf-8")

    report = script.build_report(["doc.md"])

    assert report["status"] == "PASS"
    assert report["violations"] == []
