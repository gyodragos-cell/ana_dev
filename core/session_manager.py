"""Long-running session manager for ANA MAX v26 preparation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4


def _utc_now() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class SessionRecord:
    """Session state and memory."""

    session_id: str
    state: Mapping[str, Any] = field(default_factory=dict)
    memory: list[Mapping[str, Any]] = field(default_factory=list)
    ttl_seconds: float | None = None
    max_steps: int | None = None
    steps: int = 0
    created_at: str = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe session state."""
        return {
            "session_id": self.session_id,
            "state": dict(self.state),
            "memory": [dict(item) for item in self.memory],
            "ttl_seconds": self.ttl_seconds,
            "max_steps": self.max_steps,
            "steps": self.steps,
            "created_at": self.created_at,
        }


class SessionManager:
    """Create, resume, and isolate long-running sessions."""

    def __init__(self) -> None:
        """Initialize empty session store."""
        self.sessions: dict[str, SessionRecord] = {}

    def create_session(self, state: Mapping[str, Any] | None = None, ttl_seconds: float | None = None, max_steps: int | None = None) -> SessionRecord:
        """Create a new session."""
        record = SessionRecord(str(uuid4()), dict(state or {}), ttl_seconds=ttl_seconds, max_steps=max_steps)
        self.sessions[record.session_id] = record
        return record

    def resume_session(self, session_id: str) -> SessionRecord:
        """Resume an existing session."""
        if session_id not in self.sessions:
            raise KeyError(f"unknown session: {session_id}")
        return self.sessions[session_id]

    def is_expired(self, session_id: str) -> bool:
        """Return whether a session exceeded TTL."""
        record = self.resume_session(session_id)
        if record.ttl_seconds is None:
            return False
        created = datetime.fromisoformat(record.created_at)
        return (datetime.now(timezone.utc) - created).total_seconds() > record.ttl_seconds

    def step_allowed(self, session_id: str) -> bool:
        """Return whether a session can run another step."""
        record = self.resume_session(session_id)
        return record.max_steps is None or record.steps < record.max_steps

    def record_step(self, session_id: str) -> None:
        """Increment session step count if policy allows."""
        record = self.resume_session(session_id)
        if not self.step_allowed(session_id):
            raise PermissionError("session step policy exceeded")
        record.steps += 1

    def add_memory(self, session_id: str, memory: Mapping[str, Any]) -> None:
        """Attach session-bound memory."""
        self.resume_session(session_id).memory.append(dict(memory))

    def archive_session(self, session_id: str, archive_dir: str | Path) -> Path:
        """Archive session state to a dev-local JSON file."""
        import json

        record = self.resume_session(session_id)
        path = Path(archive_dir) / f"{session_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record.to_dict(), indent=2), encoding="utf-8")
        return path


__all__ = ["SessionManager", "SessionRecord"]
