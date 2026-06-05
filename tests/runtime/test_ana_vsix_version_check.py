"""Tests for active VSIX version consistency checks."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "ana_vsix_version_check.py"


def load_script():
    spec = importlib.util.spec_from_file_location("ana_vsix_version_check", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_find_versions_extracts_unique_versions():
    script = load_script()

    assert script.find_versions("x 1.0.45 y 1.0.46 1.0.45") == ["1.0.45", "1.0.46"]


def test_report_uses_package_version_and_required_files():
    script = load_script()
    report = script.build_report()

    assert report["schema"] == "ana.vsix_version_check.v1"
    assert report["expected_version"]
    checked = {item["path"] for item in report["files"]}
    assert "vscode_extension/README.md" in checked
    assert "docs/examples/OPERATOR_STATUS_EXAMPLE.md" in checked
