"""ANA MAX v22 AI engine abstraction scaffolding.

This module separates orchestration decisions from any specific reasoning
backend. The first version provides small, deterministic placeholders for Codex,
local engines, and cloud engines so later modules can depend on a stable shape
without pulling in provider SDKs or network behavior.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol
from urllib import request as url_request


DEFAULT_SUMMARY_BUDGET = 1200


@dataclass(frozen=True)
class EnginePlan:
    """Compact plan returned by an AI engine before tool routing."""

    engine: str
    steps: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    rationale: str = ""
    confidence: float = 0.25

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation of the planned steps."""
        return {
            "engine": self.engine,
            "steps": [dict(step) for step in self.steps],
            "rationale": self.rationale,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class CritiqueResult:
    """Safety-aware review of a proposed plan."""

    approved: bool
    reason: str
    revised_plan: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe critique payload."""
        return {
            "approved": self.approved,
            "reason": self.reason,
            "revised_plan": dict(self.revised_plan) if self.revised_plan else None,
        }


class ModelBackend(Protocol):
    """Protocol for text generation backends."""

    name: str

    def generate(self, prompt: str, context: Mapping[str, Any] | None = None) -> str:
        """Generate text from a prompt and compact context."""


class EngineAdapter(Protocol):
    """Protocol implemented by concrete AI engine adapters."""

    name: str

    def plan(self, task_envelope: Any, context: Any) -> EnginePlan:
        """Create candidate steps for a task and compact context."""

    def critique(self, plan: Any, safety_context: Any) -> CritiqueResult:
        """Review a plan against safety and policy context."""

    def summarize(self, tool_result: Any, budget: int) -> str:
        """Condense a tool result to fit a context budget."""


class BaseEngine:
    """Small deterministic base adapter used by v22 placeholder engines."""

    name = "base"

    def __init__(
        self,
        endpoint: str | None = None,
        timeout_seconds: float = 10.0,
        model_name: str | None = None,
        backend: ModelBackend | None = None,
    ) -> None:
        """Store optional connector settings for real local or cloud adapters."""
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self.model_name = model_name or "default"
        self.backend = backend

    def generate(self, prompt: str, context: Mapping[str, Any] | None = None) -> str:
        """Generate text through an injected backend or deterministic fallback."""
        if self.backend is not None:
            return self.backend.generate(prompt, context or {})
        return f"{self.name}:{self.model_name}: {prompt}"

    def plan(self, task_envelope: Any, context: Any) -> EnginePlan:
        """Create a minimal observation-first placeholder plan."""
        connector_plan = self._plan_with_connector(task_envelope, context)
        if connector_plan is not None:
            return connector_plan

        task = self._read_value(task_envelope, "task", "unspecified task")
        summary = self._read_value(context, "summary", "context unavailable")
        step = {
            "id": "observe-1",
            "intent": "build_context",
            "description": f"Use compact context before acting on: {task}",
            "context_summary": summary,
            "requires_tool_routing": True,
        }
        return EnginePlan(
            engine=self.name,
            steps=(step,),
            rationale="deterministic observation-first plan",
            confidence=0.45,
        )

    def critique(self, plan: Any, safety_context: Any) -> CritiqueResult:
        """Approve placeholder read-only plans and flag unsafe context later."""
        blocked = bool(self._read_value(safety_context, "blocked", False))
        if blocked:
            reason = str(self._read_value(safety_context, "reason", "blocked by safety context"))
            return CritiqueResult(approved=False, reason=reason)
        # TODO(v22): inspect mutating steps, policy tiers, and confirmation needs.
        return CritiqueResult(approved=True, reason="placeholder critique passed")

    def summarize(self, tool_result: Any, budget: int = DEFAULT_SUMMARY_BUDGET) -> str:
        """Return a compact string summary within the requested budget."""
        text = self._result_to_text(tool_result)
        if budget <= 0:
            return ""
        if len(text) <= budget:
            return text
        # TODO(v22): replace truncation with structured summarization.
        return text[: max(0, budget - 15)].rstrip() + "... [truncated]"

    def _plan_with_connector(self, task_envelope: Any, context: Any) -> EnginePlan | None:
        """Call an optional JSON HTTP connector and parse an EnginePlan."""
        if not self.endpoint:
            return None

        payload = json.dumps(
            {
                "task": self._read_value(task_envelope, "task", ""),
                "context": self._read_value(context, "summary", ""),
                "engine": self.name,
            }
        ).encode("utf-8")
        req = url_request.Request(
            self.endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with url_request.urlopen(req, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8", errors="replace")
            data = json.loads(body)
        except Exception:
            return None

        steps = data.get("steps") if isinstance(data, Mapping) else None
        if not isinstance(steps, list):
            return None
        return EnginePlan(
            engine=str(data.get("engine", self.name)),
            steps=tuple(dict(step) for step in steps if isinstance(step, Mapping)),
            rationale=str(data.get("rationale", "connector plan")),
            confidence=float(data.get("confidence", 0.55)),
        )

    @staticmethod
    def _read_value(obj: Any, name: str, default: Any = None) -> Any:
        """Read a named field from a mapping or object."""
        if isinstance(obj, Mapping):
            return obj.get(name, default)
        return getattr(obj, name, default)

    @staticmethod
    def _result_to_text(tool_result: Any) -> str:
        """Convert a placeholder tool result to text for compact summaries."""
        if tool_result is None:
            return ""
        if isinstance(tool_result, str):
            return tool_result
        if isinstance(tool_result, Mapping):
            summary = tool_result.get("summary")
            if isinstance(summary, str):
                return summary
            return str(dict(tool_result))
        return str(tool_result)


class CodexEngine(BaseEngine):
    """Placeholder adapter for Codex as the primary coding engine."""

    name = "codex"

    # TODO(v22): wire Codex-specific cost profile, limits, and streaming hooks.


class LocalEngine(BaseEngine):
    """Placeholder adapter for offline or local LLM backends."""

    name = "local"

    def generate(self, prompt: str, context: Mapping[str, Any] | None = None) -> str:
        """Generate text with an injected local backend or safe placeholder."""
        return super().generate(prompt, context)


class CloudEngine(BaseEngine):
    """Placeholder adapter for policy-controlled cloud/provider engines."""

    name = "cloud"

    # TODO(v22): add provider cost profiles, auth policy, and streaming behavior.


class HybridEngine(BaseEngine):
    """Adapter that tries local generation first and falls back to cloud."""

    name = "hybrid"

    def __init__(self, local: BaseEngine | None = None, cloud: BaseEngine | None = None, **kwargs: Any) -> None:
        """Initialize local and cloud branches."""
        super().__init__(**kwargs)
        self.local = local or LocalEngine()
        self.cloud = cloud or CloudEngine()

    def generate(self, prompt: str, context: Mapping[str, Any] | None = None) -> str:
        """Generate using local first, then cloud on failure."""
        try:
            return self.local.generate(prompt, context)
        except Exception:
            return self.cloud.generate(prompt, context)


class AIEngine:
    """Facade that exposes a stable AI engine interface to the orchestrator."""

    def __init__(
        self,
        engine_name: str = "codex",
        endpoint: str | None = None,
        model_name: str | None = None,
        backend: ModelBackend | None = None,
        fallback_backend: ModelBackend | None = None,
    ) -> None:
        """Initialize the requested engine adapter by name."""
        self.engine_name = engine_name
        self.model_name = model_name or os.environ.get("LOCAL_MODEL_NAME") or "default"
        self.endpoint = endpoint or self._endpoint_from_env(engine_name)
        if (engine_name or "").strip().lower() == "hybrid":
            self.adapter = HybridEngine(
                local=LocalEngine(model_name=self.model_name, backend=backend),
                cloud=CloudEngine(model_name=self.model_name, backend=fallback_backend),
                endpoint=self.endpoint,
                model_name=self.model_name,
            )
        else:
            self.adapter = self._create_adapter(engine_name, self.endpoint, self.model_name, backend)
        self.fallback_engine = CloudEngine(backend=fallback_backend)

    def plan(self, task_envelope: Any, context: Any) -> EnginePlan:
        """Create candidate steps for a normalized task and compact context."""
        try:
            return self.adapter.plan(task_envelope, context)
        except Exception:
            return self.fallback_engine.plan(task_envelope, context)

    def critique(self, plan: Any, safety_context: Any) -> CritiqueResult:
        """Review a plan against safety context before routing or execution."""
        return self.adapter.critique(plan, safety_context)

    def summarize(self, tool_result: Any, budget: int = DEFAULT_SUMMARY_BUDGET) -> str:
        """Summarize a tool result for reuse inside a bounded context window."""
        return self.adapter.summarize(tool_result, budget)

    def generate(self, prompt: str, context: Mapping[str, Any] | None = None) -> str:
        """Generate text with fallback from local or hybrid backends to cloud."""
        try:
            generator = getattr(self.adapter, "generate")
            return generator(prompt, context or {})
        except Exception:
            return self.fallback_engine.generate(prompt, context or {})

    @staticmethod
    def _create_adapter(
        engine_name: str,
        endpoint: str | None = None,
        model_name: str | None = None,
        backend: ModelBackend | None = None,
    ) -> EngineAdapter:
        """Create a placeholder adapter for a supported engine name."""
        normalized = (engine_name or "codex").strip().lower()
        adapters: dict[str, type[BaseEngine]] = {
            "codex": CodexEngine,
            "local": LocalEngine,
            "cloud": CloudEngine,
            "hybrid": HybridEngine,
        }
        adapter_class = adapters.get(normalized)
        if adapter_class is None:
            raise ValueError(f"unsupported engine: {engine_name}")
        return adapter_class(endpoint=endpoint, model_name=model_name, backend=backend)

    @staticmethod
    def _endpoint_from_env(engine_name: str) -> str | None:
        """Return an optional engine endpoint from environment variables."""
        normalized = (engine_name or "codex").strip().upper()
        return os.environ.get(f"ANA_MAX_{normalized}_ENGINE_URL") or os.environ.get("ANA_MAX_ENGINE_URL")
