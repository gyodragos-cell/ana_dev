"""Tests for the Linux Mate readiness checker."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "ana_linux_readiness.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("ana_linux_readiness", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_classifies_windows_profile_files():
    checker = load_checker()

    assert checker.classify_path("ANA_MAX/tools/windows_uia_bridge.py") == "windows_profile"
    assert checker.classify_path("ANA_MAX/dev_artifacts/scripts/ana_mcp.ps1") == "windows_profile"
    assert checker.classify_path("ANA_MAX/tools/code_context_pack_tool.py") == "core_candidate"


def test_summarize_counts_core_blocker_files_once():
    checker = load_checker()
    findings = [
        checker.Finding("powershell", "ANA_MAX/tools/coreish.py", 1, "PowerShell dependency", "powershell"),
        checker.Finding("windows_path", "ANA_MAX/tools/coreish.py", 2, "Windows path", "C:\\Temp"),
        checker.Finding("powershell", "ANA_MAX/tools/windows_uia_bridge.py", 1, "PowerShell dependency", "powershell"),
    ]

    summary = checker.summarize(findings, [])

    assert summary["core_blocker_files"] == 1
    assert summary["windows_profile_files"] == 1
    assert summary["by_profile"]["core_candidate"] == 2
    assert summary["by_profile"]["windows_profile"] == 1


def test_run_readiness_returns_expected_schema_for_small_path():
    checker = load_checker()

    report = checker.run_readiness(["ANA_MAX/dev_artifacts/scripts/ana_linux_readiness.py"])

    assert report["schema"] == "ana.linux_readiness.v1"
    assert "summary" in report
    assert "recommendations" in report
    assert isinstance(report["top_findings"], list)
