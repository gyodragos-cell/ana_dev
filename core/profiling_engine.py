"""Auto-profiling engine for ANA MAX v25."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass
class ProfileBucket:
    """Performance samples for one runtime area."""

    samples: list[float] = field(default_factory=list)

    def add(self, value: float) -> None:
        """Add a non-negative sample."""
        self.samples.append(max(0.0, float(value)))

    def snapshot(self) -> dict[str, float]:
        """Return compact histogram-like stats."""
        if not self.samples:
            return {"count": 0, "avg": 0.0, "max": 0.0}
        return {"count": len(self.samples), "avg": sum(self.samples) / len(self.samples), "max": max(self.samples)}


class ProfilingEngine:
    """Track tool latency, routing overhead, scenario cost, and mocked system use."""

    def __init__(self) -> None:
        """Initialize empty profile buckets."""
        self.tool_latency: dict[str, ProfileBucket] = {}
        self.routing_overhead = ProfileBucket()
        self.scenario_cost: dict[str, ProfileBucket] = {}
        self.system_usage = {"cpu_percent": 0.0, "memory_mb": 0.0}

    def record_tool_latency(self, tool_name: str, latency_ms: float) -> None:
        """Record latency for a tool."""
        self.tool_latency.setdefault(tool_name, ProfileBucket()).add(latency_ms)

    def record_routing_overhead(self, latency_ms: float) -> None:
        """Record router overhead."""
        self.routing_overhead.add(latency_ms)

    def record_scenario_cost(self, scenario: str, cost: float) -> None:
        """Record scenario cost."""
        self.scenario_cost.setdefault(scenario, ProfileBucket()).add(cost)

    def snapshot(self) -> dict[str, Any]:
        """Return profiling snapshot."""
        return {
            "tool_latency": {name: bucket.snapshot() for name, bucket in self.tool_latency.items()},
            "routing_overhead": self.routing_overhead.snapshot(),
            "scenario_cost": {name: bucket.snapshot() for name, bucket in self.scenario_cost.items()},
            "system_usage": dict(self.system_usage),
        }

    def optimization_feedback(self) -> dict[str, Mapping[str, float]]:
        """Return latency feedback for optimization."""
        return {name: {"avg_latency_ms": bucket.snapshot()["avg"]} for name, bucket in self.tool_latency.items()}


__all__ = ["ProfileBucket", "ProfilingEngine"]
