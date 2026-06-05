"""Tests for the guarded lab VSIX install helper."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "install_latest_lab_vsix.ps1"


def test_install_helper_is_dry_run_by_default():
    text = SCRIPT.read_text(encoding="utf-8")

    assert "param(" in text
    assert "[switch]$Apply" in text
    assert "Dry run only" in text
    assert "exit 0" in text
    assert "Developer: Reload Window" in text
    assert "Reload Consistency" in text
    assert "Autonomy Pass" in text


def test_install_helper_requires_packaged_vsix_and_uses_version():
    text = SCRIPT.read_text(encoding="utf-8")

    assert "vscode_extension\\package.json" in text
    assert "$Package.version" in text
    assert "ana-codex-cockpit-{0}.vsix" in text
    assert "Run package_cockpit_vsix.py first" in text
    assert "--install-extension" in text
    assert "--force" in text
