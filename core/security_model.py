"""Security model v2 for ANA MAX distributed mode."""

from __future__ import annotations

from typing import Any, Mapping


class SecurityModel:
    """Node authentication plus allow/deny enforcement for dev mode."""

    def __init__(
        self,
        trusted_nodes: set[str] | None = None,
        permissions: Mapping[str, set[str]] | None = None,
        denied_tools: set[str] | None = None,
    ) -> None:
        """Initialize trusted nodes and permissions."""
        self.trusted_nodes = set(trusted_nodes or set())
        self.permissions = {node: set(values) for node, values in dict(permissions or {}).items()}
        self.denied_tools = set(denied_tools or set())

    def authenticate_node(self, node_id: str) -> bool:
        """Return whether a node is trusted."""
        return node_id in self.trusted_nodes

    def sign_message(self, node_id: str, payload: Mapping[str, Any]) -> str:
        """Return a fake signature."""
        return f"sig:{node_id}:{len(str(dict(payload)))}"

    def enforce(self, node_id: str, permission: str) -> dict[str, Any]:
        """Enforce node permission."""
        if not self.authenticate_node(node_id):
            return {"allowed": False, "reason": "invalid node"}
        allowed = permission in self.permissions.get(node_id, set())
        return {"allowed": allowed, "reason": "allowed" if allowed else "permission denied"}

    def enforce_tool(self, node_id: str, tool_name: str) -> dict[str, Any]:
        """Enforce tool access for a trusted node."""
        if tool_name in self.denied_tools:
            return {"allowed": False, "reason": "tool denied"}
        return self.enforce(node_id, f"tool:{tool_name}")


__all__ = ["SecurityModel"]
