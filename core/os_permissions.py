"""AI OS permissions for tools, memory, and nodes."""

from __future__ import annotations


class OSPermissions:
    """Permission sets with inheritance and enforcement."""

    def __init__(self) -> None:
        """Initialize permission registry."""
        self.permissions: dict[str, set[str]] = {}
        self.parents: dict[str, str] = {}

    def grant(self, subject: str, permission: str) -> None:
        """Grant permission."""
        self.permissions.setdefault(subject, set()).add(permission)

    def revoke(self, subject: str, permission: str) -> None:
        """Revoke permission if present."""
        self.permissions.setdefault(subject, set()).discard(permission)

    def inherit(self, child: str, parent: str) -> None:
        """Declare inheritance."""
        self.parents[child] = parent

    def has(self, subject: str, permission: str) -> bool:
        """Return whether a subject has permission."""
        if permission in self.permissions.get(subject, set()):
            return True
        parent = self.parents.get(subject)
        return self.has(parent, permission) if parent else False

    def enforce(self, subject: str, permission: str) -> dict[str, str | bool]:
        """Enforce permission."""
        allowed = self.has(subject, permission)
        return {"allowed": allowed, "reason": "allowed" if allowed else "permission denied"}

    def snapshot(self) -> dict[str, list[str]]:
        """Return a JSON-safe permission snapshot."""
        return {subject: sorted(values) for subject, values in self.permissions.items()}


__all__ = ["OSPermissions"]
