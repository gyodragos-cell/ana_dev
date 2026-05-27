"""Internal reasoning graph for ANA MAX v26.

This module stores only brief reasoning summaries and decision metadata. It is
not a chain-of-thought logger and should not be exported to public audit logs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping
from uuid import uuid4


@dataclass(frozen=True)
class ReasoningStep:
    """One private reasoning summary step."""

    step_id: str
    summary: str
    kind: str = "analysis"
    links: tuple[str, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_public_dict(self) -> dict[str, Any]:
        """Return safe metadata without private reasoning content."""
        return {"step_id": self.step_id, "kind": self.kind, "links": list(self.links)}


class ReasoningEngine:
    """Build an in-memory reasoning graph for planner/router/repair hooks."""

    def __init__(self) -> None:
        """Initialize empty private reasoning graph."""
        self.steps: dict[str, ReasoningStep] = {}

    def add_step(self, summary: str, kind: str = "analysis", links: tuple[str, ...] = ()) -> ReasoningStep:
        """Add a private reasoning summary step."""
        step = ReasoningStep(str(uuid4()), summary, kind, links)
        self.steps[step.step_id] = step
        return step

    def influence_planning(self, task: str) -> dict[str, Any]:
        """Return compact planning hints derived from private steps."""
        hints = [step.kind for step in self.steps.values() if task.lower() in step.summary.lower()]
        return {"hint_count": len(hints), "kinds": hints[-5:]}

    def public_trace(self) -> list[dict[str, Any]]:
        """Return a redacted trace suitable for audit metadata."""
        return [step.to_public_dict() for step in self.steps.values()]


__all__ = ["ReasoningEngine", "ReasoningStep"]
