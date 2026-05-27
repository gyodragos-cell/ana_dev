"""AI OS network model stub."""

from __future__ import annotations


class OSNetworkStub:
    """Virtual channels and routing rules with bandwidth simulation."""

    def __init__(self, bandwidth: int = 1024) -> None:
        """Initialize virtual network."""
        self.bandwidth = bandwidth
        self.routes: dict[str, str] = {}

    def add_route(self, source: str, target: str) -> None:
        """Add a virtual route."""
        self.routes[source] = target

    def send(self, source: str, payload: str) -> dict[str, str | int | bool]:
        """Send a payload over a virtual route."""
        target = self.routes.get(source)
        if not target:
            return {"success": False, "error": "no route"}
        return {"success": True, "target": target, "bytes": min(len(payload.encode("utf-8")), self.bandwidth)}


__all__ = ["OSNetworkStub"]
