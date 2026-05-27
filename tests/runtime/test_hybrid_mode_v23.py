"""Hybrid AI engine v23 tests."""

from core.ai_engine import AIEngine


class GoodBackend:
    """Fake successful backend."""

    name = "good"

    def generate(self, prompt, context=None):
        """Return deterministic text."""
        return f"good:{prompt}"


class FailingBackend:
    """Fake failing backend."""

    name = "failing"

    def generate(self, prompt, context=None):
        """Raise deterministic failure."""
        raise RuntimeError("local failed")


def test_hybrid_local_success():
    """Hybrid mode should use local backend first when it succeeds."""
    engine = AIEngine("hybrid", backend=GoodBackend(), fallback_backend=FailingBackend())

    assert engine.generate("task") == "good:task"


def test_hybrid_local_failure_cloud_fallback():
    """Hybrid mode should fall back to cloud backend when local fails."""
    engine = AIEngine("hybrid", backend=FailingBackend(), fallback_backend=GoodBackend())

    assert engine.generate("task") == "good:task"
