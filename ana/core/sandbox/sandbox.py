from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from ana.core.error_model.errors import SandboxViolation, ValidationError


SandboxCallable = Callable[[Mapping[str, Any]], Mapping[str, Any]]


@dataclass(frozen=True)
class SandboxPolicy:
    allowed_capabilities: frozenset[str]
    max_input_keys: int = 32
    allow_external_effects: bool = False


@dataclass(frozen=True)
class SandboxResult:
    ok: bool
    output: Mapping[str, Any]
    audit: Mapping[str, Any] = field(default_factory=dict)


class DeterministicSandbox:
    def __init__(self, policy: SandboxPolicy) -> None:
        self.policy = policy

    def execute(
        self,
        capability: str,
        handler: SandboxCallable,
        payload: Mapping[str, Any] | None = None,
        *,
        trace_id: str,
    ) -> SandboxResult:
        if capability not in self.policy.allowed_capabilities:
            raise SandboxViolation(
                f"capability is not allowed: {capability}",
                source="sandbox",
                details={"capability": capability},
            )
        safe_payload = dict(payload or {})
        if len(safe_payload) > self.policy.max_input_keys:
            raise ValidationError(
                "payload exceeds sandbox input key limit",
                source="sandbox",
                details={"limit": self.policy.max_input_keys},
            )
        output = dict(handler(safe_payload))
        return SandboxResult(
            ok=True,
            output=output,
            audit={
                "trace_id": trace_id,
                "capability": capability,
                "external_effects": self.policy.allow_external_effects,
            },
        )
