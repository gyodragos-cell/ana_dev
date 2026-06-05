from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from ana.core.error_model.errors import ANAError, FatalANAError, packet_from_exception


FallbackCallable = Callable[[Mapping[str, Any]], Mapping[str, Any]]


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 1

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")


@dataclass(frozen=True)
class FallbackStep:
    name: str
    handler: FallbackCallable


class FallbackEngine:
    def __init__(self, policy: RetryPolicy | None = None) -> None:
        self.policy = policy or RetryPolicy()

    def run(
        self,
        primary: FallbackCallable,
        payload: Mapping[str, Any],
        *,
        fallbacks: list[FallbackStep] | None = None,
    ) -> dict[str, Any]:
        errors: list[dict[str, Any]] = []
        steps = [FallbackStep("primary", primary)] + list(fallbacks or [])
        for step in steps:
            for attempt in range(1, self.policy.max_attempts + 1):
                try:
                    result = dict(step.handler(dict(payload)))
                    result.setdefault("fallback", step.name != "primary")
                    result.setdefault("step", step.name)
                    result.setdefault("attempt", attempt)
                    if errors:
                        result["errors"] = errors
                    return result
                except Exception as exc:
                    packet = packet_from_exception(exc, source=f"fallback.{step.name}")
                    errors.append(packet.to_dict() | {"attempt": attempt})
                    if isinstance(exc, ANAError) and not exc.recoverable:
                        raise
        raise FatalANAError(
            "all fallback steps failed",
            source="fallback",
            details={"errors": errors},
        )
