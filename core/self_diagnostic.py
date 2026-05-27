"""Self-diagnostic engine for ANA MAX v25."""

from __future__ import annotations

from typing import Any, Mapping


class SelfDiagnosticEngine:
    """Detect slow tools, anomalies, policy violations, and repeated failures."""

    def diagnose(self, snapshot: Mapping[str, Any]) -> dict[str, Any]:
        """Return diagnostic triggers from a runtime snapshot."""
        issues: list[dict[str, Any]] = []
        for tool, stats in snapshot.get("tool_stats", {}).items():
            if stats.get("avg_latency_ms", 0) > 1000:
                issues.append({"kind": "slow_tool", "tool": tool})
            if stats.get("failure_streak", 0) >= 3:
                issues.append({"kind": "repeated_failures", "tool": tool})
        for event in snapshot.get("policy_events", []):
            if event.get("allowed") is False:
                issues.append({"kind": "policy_violation", "event": event})
        if snapshot.get("routing_anomaly"):
            issues.append({"kind": "routing_anomaly", "detail": snapshot["routing_anomaly"]})
        return {"status": "degraded" if issues else "ok", "issues": issues}


__all__ = ["SelfDiagnosticEngine"]
