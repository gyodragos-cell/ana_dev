"""Distributed memory stub for ANA MAX distributed design."""

from __future__ import annotations

from typing import Any


class DistributedMemoryStub:
    """Fake distributed memory backend."""

    def __init__(self, fail: bool = False) -> None:
        """Initialize memory store."""
        self.fail = fail
        self.store: dict[str, Any] = {}

    def write(self, key: str, value: Any) -> dict[str, Any]:
        """Write a fake distributed memory value."""
        if self.fail:
            return {"success": False, "error": "distributed memory unavailable"}
        self.store[key] = value
        return {"success": True, "key": key}

    def read(self, key: str) -> dict[str, Any]:
        """Read a fake distributed memory value."""
        if self.fail:
            return {"success": False, "error": "distributed memory unavailable"}
        return {"success": key in self.store, "key": key, "value": self.store.get(key)}


__all__ = ["DistributedMemoryStub"]
