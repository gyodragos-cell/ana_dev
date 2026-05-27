"""Lightweight dashboard API data provider for ANA MAX Control Center."""

from __future__ import annotations

from typing import Any, Mapping


class DashboardAPI:
    """Expose safe in-memory snapshots for dashboard clients."""

    def __init__(self, providers: Mapping[str, Any] | None = None, safe_mode: bool = True) -> None:
        """Initialize dashboard providers."""
        self.providers = dict(providers or {})
        self.safe_mode = safe_mode

    def get_nodes(self) -> dict[str, Any]:
        """Return cluster node data."""
        cluster = self.providers.get("cluster")
        nodes = cluster.snapshot() if hasattr(cluster, "snapshot") else {}
        return {"safe_mode": self.safe_mode, "nodes": nodes}

    def get_services(self) -> dict[str, Any]:
        """Return service registry data."""
        manager = self.providers.get("services")
        services = {}
        if hasattr(manager, "services"):
            services = {
                name: {
                    "running": record.running,
                    "restart_count": getattr(record, "restart_count", 0),
                }
                for name, record in manager.services.items()
            }
        return {"safe_mode": self.safe_mode, "services": services}

    def get_events(self) -> dict[str, Any]:
        """Return safe event data."""
        observability = self.providers.get("observability")
        if hasattr(observability, "filtered_events"):
            events = observability.filtered_events(safe_mode=self.safe_mode)
        else:
            events = []
        return {"safe_mode": self.safe_mode, "events": events}

    def snapshot(self) -> dict[str, Any]:
        """Return a combined dashboard snapshot."""
        return {
            "nodes": self.get_nodes(),
            "services": self.get_services(),
            "events": self.get_events(),
            "tools": {"safe_mode": self.safe_mode, "items": []},
            "agents": {"safe_mode": self.safe_mode, "items": []},
            "sessions": {"safe_mode": self.safe_mode, "items": []},
        }


__all__ = ["DashboardAPI"]
