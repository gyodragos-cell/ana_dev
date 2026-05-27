"""Auto-deployment preparation helpers for ANA MAX v25."""

from __future__ import annotations

from typing import Any, Mapping


class DeploymentPrep:
    """Export deployable runtime snapshots with safe-mode restrictions."""

    def __init__(self, safe_mode: bool = True) -> None:
        """Initialize deployment policy."""
        self.safe_mode = safe_mode

    def export_config(self, config: Mapping[str, Any]) -> dict[str, Any]:
        """Export public-safe config without secrets."""
        return {key: value for key, value in config.items() if key.lower() not in {"token", "secret", "api_key", "password"}}

    def export_runtime_snapshot(self, runtime_state: Mapping[str, Any]) -> dict[str, Any]:
        """Export runtime state."""
        return dict(runtime_state)

    def export_tool_registry(self, tools: Mapping[str, Any]) -> dict[str, Any]:
        """Export compact tool registry keys."""
        return {"tools": sorted(str(name) for name in tools.keys())}

    def export_policy(self, policy: Mapping[str, Any]) -> dict[str, Any]:
        """Export policy settings."""
        return dict(policy)

    def export_memory(self, memory: Mapping[str, Any]) -> dict[str, Any]:
        """Export memory only when safe-mode is disabled."""
        if self.safe_mode:
            raise PermissionError("safe-mode blocks memory export")
        return dict(memory)


__all__ = ["DeploymentPrep"]
