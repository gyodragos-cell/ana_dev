"""Tests for ANA tool profile report generation."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "ana_tool_profile_report.py"


def load_reporter():
    spec = importlib.util.spec_from_file_location("ana_tool_profile_report", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_build_report_counts_profiles():
    reporter = load_reporter()
    manifest = {
        "global_settings": {"active_profiles": ["core"]},
        "tools": {
            "tool_router": {"tier": "internal", "profile": "core", "readonly": True},
            "desktop_control": {
                "tier": "dangerous",
                "profile": "windows",
                "readonly": False,
                "requires_confirmation": True,
            },
            "docs_generator": {"tier": "internal", "profiles": ["core", "public_safe"], "readonly": True},
        },
    }

    report = reporter.build_report(manifest)

    assert report["schema"] == "ana.tool_profile_report.v1"
    assert report["summary"]["tools_total"] == 3
    assert report["summary"]["profile_counts"]["core"] == 2
    assert report["summary"]["profile_counts"]["windows"] == 1
    assert report["summary"]["confirmation_required_tools"] == 1
    assert report["summary"]["inactive_tools"] == 1
    assert report["unprofiled_tools"] == []


def test_markdown_report_includes_tool_rows():
    reporter = load_reporter()
    report = reporter.build_report({
        "global_settings": {"active_profiles": ["core"]},
        "tools": {
            "tool_router": {"tier": "internal", "profile": "core", "readonly": True},
        },
    })

    markdown = reporter.markdown_report(report)

    assert "# ANA Tool Profile Report" in markdown
    assert "| `tool_router` | `internal` | `core` | yes | yes | no | yes |" in markdown
