"""Safe auto-repair planning for ANA MAX v23.

AutoRepairEngine suggests recovery actions for failures. It never applies
patches or mutates files; code patch output is text-only by design.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class RepairPlan:
    """Text-only repair plan for a failure event."""

    strategy: str
    action: str
    reason: str
    safe_to_apply: bool = False
    patch_suggestion: str | None = None
    diagnostics: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe repair plan."""
        return {
            "strategy": self.strategy,
            "action": self.action,
            "reason": self.reason,
            "safe_to_apply": self.safe_to_apply,
            "patch_suggestion": self.patch_suggestion,
            "diagnostics": list(self.diagnostics),
        }


class AutoRepairEngine:
    """Create safe repair suggestions from normalized failure events."""

    def __init__(self, max_chain_failures: int = 3) -> None:
        """Initialize repair limits."""
        self.max_chain_failures = max_chain_failures
        self.history: list[RepairPlan] = []
        self.disabled_tools: set[str] = set()

    def plan_repair(self, failure_event: Mapping[str, Any]) -> RepairPlan:
        """Return a repair plan for a tool, timeout, output, or test failure."""
        error = str(failure_event.get("error") or failure_event.get("summary") or "").lower()
        failures = int(failure_event.get("failure_count", 1) or 1)
        backup_tool = failure_event.get("backup_tool")
        tool_name = str(failure_event.get("tool") or "").strip()

        if failures >= self.max_chain_failures:
            if tool_name:
                self.disabled_tools.add(tool_name)
            plan = RepairPlan(
                strategy="disable_tool",
                action=f"temporarily disable broken tool: {tool_name or 'unknown'}",
                reason="failure chain limit reached",
                diagnostics=("inspect latest normalized error", "avoid runaway retries"),
            )
        elif "misroute" in error or failure_event.get("misrouted"):
            plan = RepairPlan(
                strategy="switch_tool",
                action=f"switch to backup tool: {backup_tool or 'best alternate candidate'}",
                reason="router selected a poor tool for the scenario",
                diagnostics=("record router correction", "update scenario effectiveness"),
            )
        elif "timeout" in error:
            plan = RepairPlan(
                strategy="retry",
                action="retry with shorter output budget or switch to fallback",
                reason="timeout may be transient or caused by large output",
                diagnostics=("check latency budget", "prefer compact read-only tool"),
            )
        elif "invalid" in error or "shape" in error:
            plan = RepairPlan(
                strategy="suggest_patch",
                action="normalize tool output before returning to runtime",
                reason="tool returned an invalid response shape",
                patch_suggestion="Ensure tool results include success, data or summary, and optional error.",
                diagnostics=("validate response schema", "add regression test for invalid output"),
            )
        elif backup_tool:
            plan = RepairPlan(
                strategy="switch_tool",
                action=f"switch to backup tool: {backup_tool}",
                reason="primary tool failed and a backup is configured",
                diagnostics=("preserve original error", "record fallback attempt"),
            )
        else:
            plan = RepairPlan(
                strategy="diagnose",
                action="collect compact logs and return diagnostic hints",
                reason="failure is not repairable automatically",
                diagnostics=("inspect error field", "check tool health snapshot"),
            )
        self.history.append(plan)
        return plan

    def is_disabled(self, tool_name: str) -> bool:
        """Return whether a tool is temporarily disabled by repair policy."""
        return tool_name in self.disabled_tools


__all__ = ["AutoRepairEngine", "RepairPlan"]
