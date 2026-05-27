"""ANA MAX runtime tool health monitor.

The health monitor keeps compact per-tool reliability signals for routing. It
does not execute tools; it consumes execution outcomes and exposes feedback
that ToolRouter can use to prefer reliable, quiet, low-latency tools.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _utc_now() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class HealthRecord:
    """Aggregated health data for one tool."""

    tool_name: str
    calls: int = 0
    successes: int = 0
    failures: int = 0
    failure_streak: int = 0
    total_latency_ms: float = 0.0
    total_output_bytes: int = 0
    last_success: bool | None = None
    last_seen_at: str | None = None
    latency_samples: list[float] = field(default_factory=list)

    def record(self, latency_ms: float, output_bytes: int, success: bool) -> None:
        """Add one tool execution outcome."""
        self.calls += 1
        self.successes += 1 if success else 0
        self.failures += 0 if success else 1
        self.failure_streak = 0 if success else self.failure_streak + 1
        safe_latency = max(0.0, float(latency_ms))
        self.total_latency_ms += safe_latency
        self.latency_samples.append(safe_latency)
        self.total_output_bytes += max(0, int(output_bytes))
        self.last_success = bool(success)
        self.last_seen_at = _utc_now()

    def to_dict(self) -> dict[str, Any]:
        """Return router-friendly health feedback."""
        avg_latency = self.total_latency_ms / self.calls if self.calls else 0.0
        avg_output = self.total_output_bytes / self.calls if self.calls else 0.0
        failure_rate = self.failures / self.calls if self.calls else 0.0
        noise = min(1.0, round((failure_rate + min(1.0, avg_output / 16384)) / 2, 4))
        reliability = max(0.0, round((1.0 - failure_rate) - noise * 0.2 - min(0.2, self.failure_streak * 0.05), 4))
        return {
            "tool_name": self.tool_name,
            "calls": self.calls,
            "successes": self.successes,
            "failures": self.failures,
            "failure_streak": self.failure_streak,
            "success_rate": self.successes / self.calls if self.calls else 0.0,
            "failure_rate": failure_rate,
            "avg_latency_ms": avg_latency,
            "avg_output_bytes": avg_output,
            "noisy_tool_score": noise,
            "reliability_score": reliability,
            "recent_success": self.last_success,
            "last_seen_at": self.last_seen_at,
        }


class ToolHealthMonitor:
    """Track tool health and expose snapshots for router scoring."""

    def __init__(self) -> None:
        """Initialize empty health state."""
        self.created_at = _utc_now()
        self.records: dict[str, HealthRecord] = {}

    def record_tool_result(self, tool_name: str, latency_ms: float, output_bytes: int, success: bool) -> HealthRecord:
        """Record one tool result and return the updated record."""
        normalized = self._normalize_tool_name(tool_name)
        record = self.records.setdefault(normalized, HealthRecord(tool_name=normalized))
        record.record(latency_ms=latency_ms, output_bytes=output_bytes, success=success)
        return record

    def get_tool_feedback(self, tool_name: str) -> dict[str, Any]:
        """Return router scoring feedback for one tool."""
        normalized = self._normalize_tool_name(tool_name)
        return self.records.get(normalized, HealthRecord(tool_name=normalized)).to_dict()

    def get_health_snapshot(self) -> dict[str, Any]:
        """Return a compact all-tool health snapshot."""
        tools = {name: record.to_dict() for name, record in self.records.items()}
        return {
            "created_at": self.created_at,
            "snapshot_at": _utc_now(),
            "tool_count": len(tools),
            "tools": tools,
            "status": "degraded" if any(item["failure_streak"] >= 3 for item in tools.values()) else "ok",
        }

    @staticmethod
    def _normalize_tool_name(tool_name: str) -> str:
        """Normalize tool names for stable health keys."""
        if not isinstance(tool_name, str) or not tool_name.strip():
            raise ValueError("tool_name must be a non-empty string")
        return tool_name.strip().lower()


__all__ = ["HealthRecord", "ToolHealthMonitor"]
