"""Audit trail system for ANA MAX v25."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


def _utc_now() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class AuditEvent:
    """One audit event."""

    event_type: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe audit event."""
        return {"event_type": self.event_type, "payload": dict(self.payload), "created_at": self.created_at}


class AuditTrail:
    """Record and persist compact audit events."""

    def __init__(self, path: str | Path | None = None, safe_mode: bool = True) -> None:
        """Initialize audit trail."""
        self.path = Path(path).resolve() if path else None
        self.safe_mode = safe_mode
        self.events: list[AuditEvent] = []

    def record(self, event_type: str, payload: Mapping[str, Any] | None = None) -> AuditEvent:
        """Record an event with simple redaction hooks."""
        event = AuditEvent(event_type, self._redact(dict(payload or {})))
        self.events.append(event)
        return event

    def save(self) -> None:
        """Persist audit events if a path is configured."""
        if self.path is None:
            raise ValueError("audit path is not configured")
        if self.safe_mode and "ANA_MAX_GitHub_Release" in str(self.path):
            raise PermissionError("safe-mode blocks audit writes to public release")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps([event.to_dict() for event in self.events], indent=2), encoding="utf-8")

    def load(self) -> list[dict[str, Any]]:
        """Load audit events from disk."""
        if self.path is None:
            raise ValueError("audit path is not configured")
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _redact(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Redact obvious secret-like fields."""
        return {key: ("[redacted]" if key.lower() in {"token", "secret", "password", "api_key"} else value) for key, value in payload.items()}


__all__ = ["AuditEvent", "AuditTrail"]
