import pytest

from ana.core.error_model.errors import RecoverableANAError, SandboxViolation
from ana.core.fallback.fallback import FallbackEngine, FallbackStep
from ana.core.sandbox.sandbox import DeterministicSandbox, SandboxPolicy


def test_fallback_uses_registered_degrade_path():
    def primary(payload):
        raise RecoverableANAError("try fallback", source="test")

    def fallback(payload):
        return {"value": payload["value"], "source": "fallback"}

    result = FallbackEngine().run(
        primary,
        {"value": 7},
        fallbacks=[FallbackStep("safe", fallback)],
    )

    assert result["fallback"] is True
    assert result["step"] == "safe"
    assert result["value"] == 7
    assert result["errors"][0]["recoverable"] is True


def test_sandbox_blocks_unregistered_capability():
    sandbox = DeterministicSandbox(
        SandboxPolicy(allowed_capabilities=frozenset({"fs.read"}))
    )

    with pytest.raises(SandboxViolation):
        sandbox.execute("shell.run", lambda payload: payload, {}, trace_id="t1")
