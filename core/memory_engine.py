"""Advanced semantic and episodic memory engine for ANA MAX v25."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping


EmbeddingBackend = Callable[[str], list[float]]


def _utc_now() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fake_embedding(text: str) -> list[float]:
    """Return a deterministic tiny embedding for tests."""
    buckets = [0.0, 0.0, 0.0, 0.0]
    for index, char in enumerate(text.lower()):
        buckets[index % len(buckets)] += ord(char) / 255.0
    length = math.sqrt(sum(value * value for value in buckets)) or 1.0
    return [round(value / length, 6) for value in buckets]


@dataclass
class MemoryRecord:
    """One advanced memory record."""

    key: str
    text: str
    kind: str
    score: float = 1.0
    metadata: Mapping[str, Any] = field(default_factory=dict)
    embedding: list[float] = field(default_factory=list)
    created_at: str = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe memory record."""
        return {
            "key": self.key,
            "text": self.text,
            "kind": self.kind,
            "score": self.score,
            "metadata": dict(self.metadata),
            "embedding": list(self.embedding),
            "created_at": self.created_at,
        }


class MemoryEngine:
    """Long-term memory with fake embedding similarity search."""

    def __init__(self, storage_path: str | Path | None = None, embedding_backend: EmbeddingBackend = fake_embedding) -> None:
        """Initialize memory stores and embedding backend."""
        self.storage_path = Path(storage_path).resolve() if storage_path else None
        self.embedding_backend = embedding_backend
        self.semantic: dict[str, MemoryRecord] = {}
        self.episodic: list[MemoryRecord] = []

    def add_semantic(self, key: str, text: str, metadata: Mapping[str, Any] | None = None) -> MemoryRecord:
        """Store semantic memory for tool and routing patterns."""
        record = MemoryRecord(key, text, "semantic", metadata=dict(metadata or {}), embedding=self.embedding_backend(text))
        self.semantic[key] = record
        return record

    def add_episode(self, task: str, outcome: str, metadata: Mapping[str, Any] | None = None) -> MemoryRecord:
        """Store episodic memory for task history."""
        record = MemoryRecord(
            key=f"episode-{len(self.episodic) + 1}",
            text=outcome,
            kind="episodic",
            metadata={"task": task, **dict(metadata or {})},
            embedding=self.embedding_backend(f"{task} {outcome}"),
        )
        self.episodic.append(record)
        return record

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Search memory by fake embedding similarity."""
        query_embedding = self.embedding_backend(query)
        records = list(self.semantic.values()) + list(self.episodic)
        scored = sorted(
            ((self._similarity(query_embedding, record.embedding) * record.score, record) for record in records),
            key=lambda item: item[0],
            reverse=True,
        )
        return [{"similarity": round(score, 6), **record.to_dict()} for score, record in scored[:limit]]

    def router_score(self, tool_name: str, task: str) -> float:
        """Return a small router influence score from memory hits."""
        hits = self.search(f"{tool_name} {task}", limit=3)
        return min(0.2, sum(hit["similarity"] for hit in hits if tool_name in hit["text"] or tool_name == hit["key"]) / 10)

    def prune(self, min_score: float = 0.2, max_episodes: int = 100) -> None:
        """Apply memory decay and remove weak or old memories."""
        for record in list(self.semantic.values()) + list(self.episodic):
            record.score = round(record.score * 0.95, 6)
        self.semantic = {key: item for key, item in self.semantic.items() if item.score >= min_score}
        self.episodic = [item for item in self.episodic if item.score >= min_score][-max_episodes:]

    def save(self) -> None:
        """Persist memory to JSON."""
        if self.storage_path is None:
            raise ValueError("storage_path is not configured")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    def load(self) -> None:
        """Load memory from JSON."""
        if self.storage_path is None:
            raise ValueError("storage_path is not configured")
        data = json.loads(self.storage_path.read_text(encoding="utf-8"))
        self.semantic = {key: MemoryRecord(**value) for key, value in data.get("semantic", {}).items()}
        self.episodic = [MemoryRecord(**value) for value in data.get("episodic", [])]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe memory snapshot."""
        return {
            "semantic": {key: value.to_dict() for key, value in self.semantic.items()},
            "episodic": [value.to_dict() for value in self.episodic],
        }

    @staticmethod
    def _similarity(left: list[float], right: list[float]) -> float:
        """Return cosine similarity for two vectors."""
        if not left or not right:
            return 0.0
        return sum(a * b for a, b in zip(left, right))


__all__ = ["MemoryEngine", "MemoryRecord", "fake_embedding"]
