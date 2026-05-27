"""Remote agent stub for distributed ANA MAX design."""

from __future__ import annotations

from typing import Any, Callable, Mapping


class RemoteAgentStub:
    """Fake remote agent client with injectable transport."""

    def __init__(self, transport: Callable[[str, Mapping[str, Any]], Mapping[str, Any]] | None = None) -> None:
        """Initialize fake transport."""
        self.transport = transport or (lambda target, payload: {"success": True, "target": target, "payload": dict(payload)})

    def call(self, target: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        """Call a fake remote agent and normalize failures."""
        try:
            result = self.transport(target, payload)
            return dict(result)
        except Exception as error:
            return {"success": False, "error": str(error), "target": target}


__all__ = ["RemoteAgentStub"]
