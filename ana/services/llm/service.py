from __future__ import annotations

from typing import Any, Mapping

from ana.core.error_model.errors import RoutingFailure, ValidationError


class DeterministicLLMService:
    def __init__(self) -> None:
        self._responses: dict[str, str] = {}

    def register(self, prompt: str, response: str) -> None:
        self._responses[prompt] = response

    def complete(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        prompt = payload.get("prompt")
        if not isinstance(prompt, str) or not prompt:
            raise ValidationError("prompt is required", source="llm")
        if prompt not in self._responses:
            raise RoutingFailure(
                "prompt is not registered for deterministic llm execution",
                source="llm",
                details={"prompt": prompt},
            )
        return {"text": self._responses[prompt], "model": "deterministic-fake"}
