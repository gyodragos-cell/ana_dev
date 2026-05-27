"""Cluster manager stub for v27 concept runtime."""

from __future__ import annotations


class ClusterManagerStub:
    """In-memory cluster membership manager."""

    def __init__(self) -> None:
        """Initialize empty cluster."""
        self.members: set[str] = set()

    def join(self, node_id: str) -> None:
        """Add a node."""
        self.members.add(node_id)

    def leave(self, node_id: str) -> None:
        """Remove a node."""
        self.members.discard(node_id)

    def snapshot(self) -> dict[str, list[str]]:
        """Return cluster membership."""
        return {"members": sorted(self.members)}


__all__ = ["ClusterManagerStub"]
