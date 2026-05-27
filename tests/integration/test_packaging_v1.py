"""Packaging v1 tests."""

from core.packaging_manager import PackagingManager


def test_packaging_manifests_validators_and_release_text():
    """Packaging manager should generate deterministic dev-only artifacts."""
    packaging = PackagingManager("1.0.0-dev", "dev")
    assert packaging.runtime_manifest()["version"] == "1.0.0-dev"
    assert packaging.module_manifest(["b", "a"]) == {"modules": ["a", "b"], "count": 2}
    assert packaging.protocol_manifest(["event.publish"])["protocols"] == ["event.publish"]
    assert packaging.validate_environment()["success"] is True
    assert packaging.validate_config({"mode": "safe"})["success"] is True
    assert "ANA MAX OS" in packaging.release_notes()
    assert "public release build" in packaging.changelog_entry()
