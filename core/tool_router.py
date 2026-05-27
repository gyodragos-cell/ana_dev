"""ANA MAX v22 tool router scaffolding.

The tool router chooses the smallest useful tool for a planned step. This first
version is intentionally deterministic and lightweight: it exposes the scoring
shape, confirmation checks, and rationale builder without calling live tools or
hard-coding public release behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


DEFAULT_WEIGHTS = {
    "relevance": 0.4,
    "risk": -0.25,
    "cost": -0.15,
    "context_fit": 0.15,
    "latency": -0.05,
    "reliability": 0.2,
    "noise": -0.1,
    "scenario_fit": 0.1,
}

DEFAULT_RISKY_TOOLS = {
    "terminal",
    "bash_exec",
    "desktop_control",
    "desktop_control_tool",
    "uia_click",
    "uia_type",
    "git_operations",
    "file_operations",
    "file_patch",
    "network_pentest",
    "mitm_analyzer",
}

DEFAULT_READ_ONLY_HINTS = (
    "read",
    "grep",
    "search",
    "list",
    "inspect",
    "snapshot",
    "health",
    "radar",
    "navigator",
)


@dataclass(frozen=True)
class ToolScore:
    """Scoring details for one candidate tool."""

    tool: str
    relevance: float
    risk: float
    cost: float
    context_fit: float
    latency: float
    reliability: float
    noise: float
    scenario_fit: float
    total: float
    requires_confirmation: bool
    rationale: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe score payload."""
        return {
            "tool": self.tool,
            "relevance": self.relevance,
            "risk": self.risk,
            "cost": self.cost,
            "context_fit": self.context_fit,
            "latency": self.latency,
            "reliability": self.reliability,
            "noise": self.noise,
            "scenario_fit": self.scenario_fit,
            "total": self.total,
            "requires_confirmation": self.requires_confirmation,
            "rationale": self.rationale,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class ToolRouteDecision:
    """Selected tool and ranked alternatives for a planned step."""

    selected_tool: str | None
    selected_score: ToolScore | None
    candidates: tuple[ToolScore, ...] = field(default_factory=tuple)
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe route decision."""
        return {
            "selected_tool": self.selected_tool,
            "selected_score": self.selected_score.to_dict() if self.selected_score else None,
            "candidates": [score.to_dict() for score in self.candidates],
            "rationale": self.rationale,
        }


class ToolRouter:
    """Score and select ANA MAX tools for v22 orchestrator steps."""

    def __init__(
        self,
        policies: Mapping[str, Any] | None = None,
        scoring_config: Mapping[str, float] | None = None,
        health_monitor: Any = None,
    ) -> None:
        """Initialize router policies and scoring weights."""
        self.policies = dict(policies or {})
        self.weights = dict(DEFAULT_WEIGHTS)
        if scoring_config:
            self.weights.update(scoring_config)
        self.risky_tools = set(self.policies.get("risky_tools", DEFAULT_RISKY_TOOLS))
        self.confirmation_threshold = float(self.policies.get("confirmation_threshold", 0.55))
        self.tool_feedback = dict(self.policies.get("tool_feedback", {}))
        self.health_monitor = health_monitor
        self.routing_memory: list[dict[str, Any]] = []
        self.scenario_effectiveness: dict[str, dict[str, float]] = {}
        # TODO(v22): load dynamic scoring weights from observability metrics.
        # TODO(v22): add premium/internal tool gating from license policy.

    def score_tool(self, tool_name: str, task_envelope: Any, context: Any) -> ToolScore:
        """Score one candidate tool for a task and compact context."""
        normalized = self._normalize_tool_name(tool_name)
        relevance = self._score_relevance(normalized, task_envelope, context)
        risk = self._score_risk(normalized, task_envelope, context)
        cost = self._score_cost(normalized, task_envelope, context)
        context_fit = self._score_context_fit(normalized, task_envelope, context)
        latency = self._estimate_latency(normalized)
        reliability = self._score_reliability(normalized)
        noise = self._score_noise(normalized)
        scenario_fit = self._score_scenario_fit(normalized, task_envelope, context)
        feedback_adjustment = self._score_observability_feedback(normalized)
        total = self._weighted_total(
            relevance, risk, cost, context_fit, latency, reliability, noise, scenario_fit
        ) + feedback_adjustment
        needs_confirmation = self.requires_confirmation(normalized, risk)
        score_data = {
            "relevance": relevance,
            "risk": risk,
            "cost": cost,
            "context_fit": context_fit,
            "latency": latency,
            "reliability": reliability,
            "noise": noise,
            "scenario_fit": scenario_fit,
            "feedback_adjustment": feedback_adjustment,
            "total": total,
            "requires_confirmation": needs_confirmation,
        }
        rationale = self.build_rationale(normalized, score_data)
        return ToolScore(
            tool=normalized,
            relevance=relevance,
            risk=risk,
            cost=cost,
            context_fit=context_fit,
            latency=latency,
            reliability=reliability,
            noise=noise,
            scenario_fit=scenario_fit,
            total=total,
            requires_confirmation=needs_confirmation,
            rationale=rationale,
            metadata={"scoring": "placeholder", "feedback_adjustment": feedback_adjustment},
        )

    def select_tool(self, candidate_tools: Sequence[str], task_envelope: Any, context: Any) -> ToolRouteDecision:
        """Select the highest-scoring tool from candidate tools."""
        scores = tuple(
            sorted(
                (self.score_tool(tool, task_envelope, context) for tool in candidate_tools),
                key=lambda item: item.total,
                reverse=True,
            )
        )
        if not scores:
            return ToolRouteDecision(
                selected_tool=None,
                selected_score=None,
                candidates=(),
                rationale="no candidate tools provided",
            )
        selected = scores[0]
        self._remember_decision(selected.tool, task_envelope, context, selected.total)
        return ToolRouteDecision(
            selected_tool=selected.tool,
            selected_score=selected,
            candidates=scores,
            rationale=f"selected {selected.tool}: {selected.rationale}",
        )

    def requires_confirmation(self, tool_name: str, risk_score: float) -> bool:
        """Return whether a candidate requires confirmation before execution."""
        normalized = self._normalize_tool_name(tool_name)
        if normalized in self.risky_tools:
            return True
        return risk_score >= self.confirmation_threshold

    def build_rationale(self, tool_name: str, score_data: Mapping[str, Any]) -> str:
        """Build a compact human-readable rationale for a route score."""
        total = float(score_data.get("total", 0.0))
        relevance = float(score_data.get("relevance", 0.0))
        risk = float(score_data.get("risk", 0.0))
        cost = float(score_data.get("cost", 0.0))
        context_fit = float(score_data.get("context_fit", 0.0))
        feedback = float(score_data.get("feedback_adjustment", 0.0))
        reliability = float(score_data.get("reliability", 0.0))
        noise = float(score_data.get("noise", 0.0))
        scenario_fit = float(score_data.get("scenario_fit", 0.0))
        return (
            f"total={total:.2f}, relevance={relevance:.2f}, risk={risk:.2f}, "
            f"cost={cost:.2f}, context_fit={context_fit:.2f}, "
            f"reliability={reliability:.2f}, noise={noise:.2f}, "
            f"scenario_fit={scenario_fit:.2f}, feedback={feedback:.2f}"
        )

    def record_routing_result(self, tool_name: str, success: bool, scenario: str | None = None) -> None:
        """Record outcome feedback for recent adaptive routing decisions."""
        normalized = self._normalize_tool_name(tool_name)
        for item in reversed(self.routing_memory):
            if item["tool"] == normalized and "success" not in item:
                item["success"] = bool(success)
                break
        if scenario:
            stats = self.scenario_effectiveness.setdefault(scenario, {"calls": 0.0, "successes": 0.0})
            stats["calls"] += 1.0
            stats["successes"] += 1.0 if success else 0.0

    def _score_relevance(self, tool_name: str, task_envelope: Any, context: Any) -> float:
        """Placeholder relevance score using task text and tool-name hints."""
        task = str(self._read_value(task_envelope, "task", "")).lower()
        if not task:
            return 0.25
        if tool_name in task or any(part and part in task for part in tool_name.split("_")):
            return 0.75
        if any(hint in tool_name for hint in DEFAULT_READ_ONLY_HINTS):
            return 0.55
        return 0.4

    def _score_risk(self, tool_name: str, task_envelope: Any, context: Any) -> float:
        """Placeholder risk score based on known mutating or powerful tools."""
        if tool_name in self.risky_tools:
            return 0.75
        if any(term in tool_name for term in ("control", "write", "patch", "exec", "pentest")):
            return 0.65
        return 0.2

    def _score_cost(self, tool_name: str, task_envelope: Any, context: Any) -> float:
        """Placeholder cost score for expected token and runtime expense."""
        if any(term in tool_name for term in ("desktop", "vision", "scraper", "search")):
            return 0.45
        return 0.2

    def _score_context_fit(self, tool_name: str, task_envelope: Any, context: Any) -> float:
        """Placeholder context-fit score from available context confidence."""
        confidence = self._read_value(context, "confidence", 0.35)
        try:
            base = float(confidence)
        except (TypeError, ValueError):
            base = 0.35
        if any(hint in tool_name for hint in DEFAULT_READ_ONLY_HINTS):
            return min(0.95, base + 0.2)
        return min(0.95, base + 0.05)

    def _estimate_latency(self, tool_name: str) -> float:
        """Placeholder latency estimate normalized from 0.0 fast to 1.0 slow."""
        if any(term in tool_name for term in ("desktop", "vision", "browser", "web", "network")):
            return 0.55
        return 0.2

    def _score_observability_feedback(self, tool_name: str) -> float:
        """Return a small score adjustment from placeholder observability data."""
        feedback = self.tool_feedback.get(tool_name, {})
        if not feedback and self.health_monitor is not None and hasattr(self.health_monitor, "get_tool_feedback"):
            feedback = self.health_monitor.get_tool_feedback(tool_name)
        if not isinstance(feedback, Mapping):
            return 0.0

        failure_rate = self._safe_float(feedback.get("failure_rate"), 0.0)
        avg_output = self._safe_float(feedback.get("avg_output_bytes"), 0.0)
        avg_latency = self._safe_float(feedback.get("avg_latency_ms"), 0.0)
        scenario_success_rate = self._safe_float(feedback.get("scenario_success_rate"), 0.0)
        noisy_tool_score = self._safe_float(feedback.get("noisy_tool_score"), 0.0)
        score_boost = self._safe_float(feedback.get("score_boost"), 0.0)
        score_penalty = self._safe_float(feedback.get("score_penalty"), 0.0)
        recent_success = feedback.get("recent_success")

        adjustment = score_boost - score_penalty
        adjustment -= min(0.12, failure_rate * 0.12)
        adjustment -= min(0.08, avg_output / 200_000)
        adjustment -= min(0.08, noisy_tool_score * 0.08)
        adjustment -= min(0.05, avg_latency / 20_000)
        adjustment += min(0.08, scenario_success_rate * 0.08)
        if recent_success is True:
            adjustment += 0.05
        elif recent_success is False:
            adjustment -= 0.05
        return adjustment

    def _score_reliability(self, tool_name: str) -> float:
        """Return reliability from health or observability feedback."""
        feedback = self.tool_feedback.get(tool_name, {})
        if not feedback and self.health_monitor is not None and hasattr(self.health_monitor, "get_tool_feedback"):
            feedback = self.health_monitor.get_tool_feedback(tool_name)
        if isinstance(feedback, Mapping):
            return self._safe_float(feedback.get("reliability_score"), 0.5)
        return 0.5

    def _score_noise(self, tool_name: str) -> float:
        """Return noisy-tool pressure from health or observability feedback."""
        feedback = self.tool_feedback.get(tool_name, {})
        if not feedback and self.health_monitor is not None and hasattr(self.health_monitor, "get_tool_feedback"):
            feedback = self.health_monitor.get_tool_feedback(tool_name)
        if isinstance(feedback, Mapping):
            return self._safe_float(feedback.get("noisy_tool_score"), 0.0)
        return 0.0

    def _score_scenario_fit(self, tool_name: str, task_envelope: Any, context: Any) -> float:
        """Score tool fit based on scenario history and task hints."""
        scenario = self._read_value(task_envelope, "scenario", None) or self._read_value(context, "scenario", None)
        if scenario and scenario in self.scenario_effectiveness:
            stats = self.scenario_effectiveness[scenario]
            calls = max(1.0, stats.get("calls", 0.0))
            return min(1.0, stats.get("successes", 0.0) / calls)
        recent = [item for item in self.routing_memory[-50:] if item["tool"] == tool_name and "success" in item]
        if not recent:
            return 0.5
        return sum(1 for item in recent if item["success"]) / len(recent)

    def _weighted_total(
        self,
        relevance: float,
        risk: float,
        cost: float,
        context_fit: float,
        latency: float,
        reliability: float,
        noise: float,
        scenario_fit: float,
    ) -> float:
        """Combine score components using current router weights."""
        return (
            relevance * self.weights["relevance"]
            + risk * self.weights["risk"]
            + cost * self.weights["cost"]
            + context_fit * self.weights["context_fit"]
            + latency * self.weights["latency"]
            + reliability * self.weights.get("reliability", 0.0)
            + noise * self.weights.get("noise", 0.0)
            + scenario_fit * self.weights.get("scenario_fit", 0.0)
        )

    def _remember_decision(self, tool_name: str, task_envelope: Any, context: Any, score: float) -> None:
        """Store the latest routing decision in a bounded in-memory window."""
        self.routing_memory.append(
            {
                "tool": tool_name,
                "task": str(self._read_value(task_envelope, "task", ""))[:120],
                "confidence": self._safe_float(self._read_value(context, "confidence", 0.0), 0.0),
                "score": score,
            }
        )
        if len(self.routing_memory) > 50:
            del self.routing_memory[:-50]

    @staticmethod
    def _safe_float(value: Any, default: float) -> float:
        """Convert a value to float for scoring, falling back safely."""
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _normalize_tool_name(tool_name: str) -> str:
        """Normalize a tool name for consistent scoring."""
        if not isinstance(tool_name, str) or not tool_name.strip():
            raise ValueError("tool_name must be a non-empty string")
        return tool_name.strip().lower()

    @staticmethod
    def _read_value(obj: Any, name: str, default: Any = None) -> Any:
        """Read a named field from a mapping or object."""
        if isinstance(obj, Mapping):
            return obj.get(name, default)
        return getattr(obj, name, default)
