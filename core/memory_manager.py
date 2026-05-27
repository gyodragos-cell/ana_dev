"""Semantic and episodic memory manager for ANA MAX v24."""

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
class MemoryEntry:
    """One semantic or episodic memory entry."""

    key: str
    value: str
    kind: str
    metadata: Mapping[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe memory entry."""
        return {
            "key": self.key,
            "value": self.value,
            "kind": self.kind,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


class MemoryManager:
    """Store semantic tool patterns and episodic recent-task memories."""

    def __init__(self, storage_path: str | Path | None = None) -> None:
        """Initialize memory stores and optional JSON persistence path."""
        self.storage_path = Path(storage_path).resolve() if storage_path else None
        self.semantic: dict[str, MemoryEntry] = {}
        self.episodic: list[MemoryEntry] = []

    def save_semantic(self, key: str, value: str, metadata: Mapping[str, Any] | None = None) -> MemoryEntry:
        """Save semantic memory such as tool behavior or patterns."""
        entry = MemoryEntry(key=key, value=value, kind="semantic", metadata=dict(metadata or {}))
        self.semantic[key] = entry
        return entry

    def save_episode(self, task: str, outcome: str, metadata: Mapping[str, Any] | None = None) -> MemoryEntry:
        """Save episodic memory for a recent task."""
        entry = MemoryEntry(key=f"episode-{len(self.episodic) + 1}", value=outcome, kind="episodic", metadata={"task": task, **dict(metadata or {})})
        self.episodic.append(entry)
        return entry

    def inject_context(self, task: str) -> dict[str, Any]:
        """Return memory context that can influence routing."""
        task_lower = task.lower()
        semantic_hits = [
            entry.to_dict()
            for key, entry in self.semantic.items()
            if key.lower() in task_lower or entry.value.lower() in task_lower
        ]
        return {
            "semantic_hits": semantic_hits,
            "recent_episodes": [entry.to_dict() for entry in self.episodic[-5:]],
        }

    def save(self) -> None:
        """Persist memory to the configured JSON path."""
        if self.storage_path is None:
            raise ValueError("storage_path is not configured")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    def load(self) -> None:
        """Load memory from the configured JSON path."""
        if self.storage_path is None:
            raise ValueError("storage_path is not configured")
        data = json.loads(self.storage_path.read_text(encoding="utf-8"))
        self.semantic = {
            key: MemoryEntry(**value) for key, value in data.get("semantic", {}).items()
        }
        self.episodic = [MemoryEntry(**value) for value in data.get("episodic", [])]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe memory snapshot."""
        return {
            "semantic": {key: entry.to_dict() for key, entry in self.semantic.items()},
            "episodic": [entry.to_dict() for entry in self.episodic],
        }


__all__ = ["MemoryEntry", "MemoryManager"]
