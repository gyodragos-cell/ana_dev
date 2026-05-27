"""Human feedback hooks for ANA MAX v26."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from core.policy_engine import PolicyEngine


@dataclass(frozen=True)
class FeedbackRecord:
    """One human feedback record."""

    target: str
    rating: float
    note: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe feedback."""
        return {"target": self.target, "rating": self.rating, "note": self.note, "metadata": dict(self.metadata)}


class HumanFeedback:
    """Record feedback and expose router/tuning influence."""

    def __init__(self, policy_engine: PolicyEngine | None = None) -> None:
        """Initialize feedback store."""
        self.policy_engine = policy_engine or PolicyEngine()
        self.records: list[FeedbackRecord] = []

    def record(self, target: str, rating: float, note: str = "") -> FeedbackRecord:
        """Record bounded human feedback."""
        rating = max(-1.0, min(1.0, float(rating)))
        record = FeedbackRecord(target, rating, note)
        self.records.append(record)
        return record

    def routing_feedback(self, target: str) -> dict[str, float]:
        """Return score adjustment for a target."""
        hits = [item.rating for item in self.records if item.target == target]
        avg = sum(hits) / len(hits) if hits else 0.0
        return {"score_boost": max(0.0, avg * 0.1), "score_penalty": max(0.0, -avg * 0.1)}


__all__ = ["FeedbackRecord", "HumanFeedback"]
