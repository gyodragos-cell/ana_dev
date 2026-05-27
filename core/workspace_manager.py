"""Multi-workspace manager for ANA MAX v25."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class WorkspaceRecord:
    """Registered workspace state."""

    workspace_id: str
    root: str
    config: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe workspace record."""
        return {"workspace_id": self.workspace_id, "root": self.root, "config": dict(self.config)}


class WorkspaceManager:
    """Register, switch, and isolate multiple workspaces."""

    def __init__(self) -> None:
        """Initialize empty workspace registry."""
        self.workspaces: dict[str, WorkspaceRecord] = {}
        self.active_workspace_id: str | None = None
        self.workspace_memory: dict[str, dict[str, Any]] = {}

    def register_workspace(self, workspace_id: str, root: str | Path, config: Mapping[str, Any] | None = None) -> WorkspaceRecord:
        """Register a workspace root."""
        resolved = str(Path(root).resolve())
        record = WorkspaceRecord(workspace_id, resolved, dict(config or {}))
        self.workspaces[workspace_id] = record
        self.workspace_memory.setdefault(workspace_id, {})
        if self.active_workspace_id is None:
            self.active_workspace_id = workspace_id
        return record

    def switch_workspace(self, workspace_id: str) -> WorkspaceRecord:
        """Switch active workspace by id."""
        if workspace_id not in self.workspaces:
            raise KeyError(f"unknown workspace: {workspace_id}")
        self.active_workspace_id = workspace_id
        return self.workspaces[workspace_id]

    def enforce_isolation(self, path: str | Path, workspace_id: str | None = None) -> bool:
        """Return whether a path stays inside a workspace root."""
        record = self.workspaces[workspace_id or self.active_workspace_id or ""]
        target = Path(path).resolve()
        root = Path(record.root).resolve()
        return str(target).startswith(str(root))

    def route_context(self) -> dict[str, Any]:
        """Return active workspace context for routing."""
        if self.active_workspace_id is None:
            return {"workspace": None}
        record = self.workspaces[self.active_workspace_id]
        return {"workspace": record.to_dict(), "memory": dict(self.workspace_memory.get(record.workspace_id, {}))}


__all__ = ["WorkspaceManager", "WorkspaceRecord"]
