"""Auto-tuning engine for ANA MAX v25 router parameters."""

from __future__ import annotations

from typing import Any, Mapping

from core.policy_engine import PolicyEngine


class AutoTuningEngine:
    """Tune router weights from metrics while respecting policy constraints."""

    def __init__(self, policy_engine: PolicyEngine | None = None) -> None:
        """Initialize optional policy integration."""
        self.policy_engine = policy_engine or PolicyEngine()

    def tune(self, weights: Mapping[str, float], metrics: Mapping[str, Any]) -> dict[str, float]:
        """Return adjusted weights without mutating input config."""
        tuned = dict(weights)
        if metrics.get("failure_rate", 0.0) > 0.2:
            tuned["reliability"] = min(0.5, tuned.get("reliability", 0.2) + 0.05)
        if metrics.get("noise", 0.0) > 0.3:
            tuned["noise"] = max(-0.5, tuned.get("noise", -0.1) - 0.05)
        if metrics.get("latency_ms", 0.0) > 1000:
            tuned["latency"] = max(-0.3, tuned.get("latency", -0.05) - 0.03)
        tuned["scenario_fit"] = min(0.3, tuned.get("scenario_fit", 0.1) + 0.02)
        if self.policy_engine.safe_mode:
            tuned["risk"] = min(tuned.get("risk", -0.25), -0.25)
        return tuned


__all__ = ["AutoTuningEngine"]
