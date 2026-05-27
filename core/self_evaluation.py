"""Self-evaluation and critic support for ANA MAX v26."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class EvaluationResult:
    """Critic evaluation result."""

    passed: bool
    issue: str = ""
    correction: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe evaluation."""
        return {"passed": self.passed, "issue": self.issue, "correction": self.correction}


class SelfEvaluation:
    """Evaluate plans and tool outputs with simple critic checks."""

    def evaluate_output(self, result: Mapping[str, Any]) -> EvaluationResult:
        """Catch obvious output issues."""
        if not result.get("success") and not result.get("error"):
            return EvaluationResult(False, "failed result lacks error", "include normalized error")
        if result.get("success") and result.get("data") is None and not result.get("summary"):
            return EvaluationResult(False, "successful result is empty", "include data or summary")
        return EvaluationResult(True)

    def evaluate_plan(self, plan: Mapping[str, Any]) -> EvaluationResult:
        """Catch obvious plan issues."""
        steps = plan.get("steps", [])
        if not steps:
            return EvaluationResult(False, "plan has no steps", "add observe/execute/verify steps")
        return EvaluationResult(True)

    def suggest_repair_event(self, evaluation: EvaluationResult) -> dict[str, Any]:
        """Convert a failed evaluation into an auto-repair event."""
        return {"error": evaluation.issue, "summary": evaluation.correction, "failure_count": 1}


__all__ = ["EvaluationResult", "SelfEvaluation"]
