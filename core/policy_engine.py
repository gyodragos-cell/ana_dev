"""Governance and policy engine for ANA MAX v25."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class PolicyDecision:
    """Allow/deny policy result."""

    allowed: bool
    reason: str
    requires_confirmation: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe policy decision."""
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "requires_confirmation": self.requires_confirmation,
            "metadata": dict(self.metadata),
        }


class PolicyEngine:
    """Evaluate safe-mode, dev-mode, and tool-level restrictions."""

    def __init__(self, safe_mode: bool = True, dev_mode: bool = False, rules: Mapping[str, Any] | None = None) -> None:
        """Initialize policy flags and optional rules."""
        self.safe_mode = safe_mode
        self.dev_mode = dev_mode
        self.rules = dict(rules or {})

    def evaluate(self, tool_name: str, capabilities: Mapping[str, bool] | None = None) -> PolicyDecision:
        """Evaluate a tool against current policy."""
        caps = dict(capabilities or {})
        denied = set(self.rules.get("deny_tools", ()))
        if tool_name in denied and not self.dev_mode:
            return PolicyDecision(False, f"tool denied by policy: {tool_name}")
        if self.dev_mode:
            return PolicyDecision(True, "dev-mode override", requires_confirmation=False)
        if self.safe_mode:
            if caps.get("safe_write"):
                return PolicyDecision(False, "safe-mode blocks writes", requires_confirmation=True)
            if caps.get("network_allowed"):
                return PolicyDecision(False, "safe-mode blocks network", requires_confirmation=True)
            if caps.get("subprocess_allowed"):
                return PolicyDecision(False, "safe-mode blocks subprocess", requires_confirmation=True)
        if caps.get("safe_write") or caps.get("network_allowed") or caps.get("subprocess_allowed"):
            return PolicyDecision(True, "allowed with confirmation", requires_confirmation=True)
        return PolicyDecision(True, "allowed")


__all__ = ["PolicyDecision", "PolicyEngine"]
