"""In-memory self-optimization loop for ANA MAX v23.

The optimizer computes routing feedback from metrics. It does not persist
configuration or rewrite policies; callers can export reports as text.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping


def _utc_now() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class OptimizationSnapshot:
    """Computed routing adjustments from runtime feedback."""

    tool_stats: Mapping[str, Mapping[str, Any]]
    scenario_stats: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    routing_adjustments: Mapping[str, Mapping[str, float]] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe optimization snapshot."""
        return {
            "tool_stats": {name: dict(stats) for name, stats in self.tool_stats.items()},
            "scenario_stats": {name: dict(stats) for name, stats in self.scenario_stats.items()},
            "routing_adjustments": {name: dict(values) for name, values in self.routing_adjustments.items()},
            "created_at": self.created_at,
        }


class SelfOptimizationEngine:
    """Compute in-memory routing improvements from tool and scenario metrics."""

    def __init__(self) -> None:
        """Initialize empty optimization state."""
        self.latest_snapshot: OptimizationSnapshot | None = None

    def compute_snapshot(
        self,
        tool_stats: Mapping[str, Mapping[str, Any]],
        scenario_stats: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> OptimizationSnapshot:
        """Compute reliability, noise, and score adjustments."""
        adjustments: dict[str, dict[str, float]] = {}
        for tool_name, stats in tool_stats.items():
            success_rate = self._float(stats.get("success_rate"), 1.0 - self._float(stats.get("failure_rate"), 0.0))
            failure_rate = self._float(stats.get("failure_rate"), 0.0)
            latency = self._float(stats.get("avg_latency_ms"), 0.0)
            noise = self._float(stats.get("noisy_tool_score"), 0.0)
            latency_penalty = min(0.15, latency / 20_000)
            boost = max(0.0, min(0.2, success_rate * 0.15 - latency_penalty - noise * 0.1))
            penalty = max(0.0, min(0.3, failure_rate * 0.2 + noise * 0.15 + latency_penalty))
            reliability = max(0.0, min(1.0, success_rate - penalty))
            adjustments[tool_name] = {
                "score_boost": round(boost, 4),
                "score_penalty": round(penalty, 4),
                "reliability_score": round(reliability, 4),
                "noisy_tool_score": round(noise, 4),
            }
        snapshot = OptimizationSnapshot(
            tool_stats=tool_stats,
            scenario_stats=scenario_stats or {},
            routing_adjustments=adjustments,
        )
        self.latest_snapshot = snapshot
        return snapshot

    def get_tool_feedback(self, tool_name: str) -> dict[str, Any]:
        """Return router-compatible feedback for one tool."""
        if self.latest_snapshot is None:
            return {}
        stats = dict(self.latest_snapshot.tool_stats.get(tool_name, {}))
        adjustment = dict(self.latest_snapshot.routing_adjustments.get(tool_name, {}))
        stats.update(adjustment)
        return stats

    def report_text(self) -> str:
        """Return a compact text report without writing files."""
        if self.latest_snapshot is None:
            return "No optimization snapshot computed."
        lines = ["ANA MAX optimization snapshot:"]
        for tool, adjustment in self.latest_snapshot.routing_adjustments.items():
            lines.append(
                f"- {tool}: boost={adjustment['score_boost']}, "
                f"penalty={adjustment['score_penalty']}, reliability={adjustment['reliability_score']}"
            )
        return "\n".join(lines)

    @staticmethod
    def _float(value: Any, default: float) -> float:
        """Parse a float with a safe default."""
        try:
            return float(value)
        except (TypeError, ValueError):
            return default


__all__ = ["OptimizationSnapshot", "SelfOptimizationEngine"]
