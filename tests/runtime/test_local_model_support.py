"""Local model backend tests are mock-only."""

import os

import pytest

from core.ai_engine import AIEngine
from core.runtime_config import RuntimeConfig


class FakeBackend:
    """Fake backend that returns text."""

    name = "fake"

    def generate(self, prompt, context=None):
        """Return deterministic fake output."""
        return f"fake:{prompt}:{bool(context)}"


class BrokenBackend:
    """Fake backend that fails."""

    name = "broken"

    def generate(self, prompt, context=None):
        """Raise a deterministic backend failure."""
        raise RuntimeError("backend failed")


def test_fake_local_backend_generates_text():
    """AIEngine should use injected local backend without real model calls."""
    engine = AIEngine("local", backend=FakeBackend())

    assert engine.generate("hello", {"a": 1}) == "fake:hello:True"


def test_local_falls_back_to_cloud_on_failure():
    """AIEngine should fall back when a local backend fails."""
    engine = AIEngine("local", backend=BrokenBackend(), fallback_backend=FakeBackend())

    assert engine.generate("hello", {}) == "fake:hello:False"


def test_ai_backend_config_validation(monkeypatch):
    """RuntimeConfig should validate AI_BACKEND values."""
    monkeypatch.setenv("AI_BACKEND", "local")
    config = RuntimeConfig("dev").get_ai_backend_config()
    assert config["backend"] == "local"

    monkeypatch.setenv("AI_BACKEND", "unknown")
    with pytest.raises(ValueError):
        RuntimeConfig("dev").get_ai_backend_config()
