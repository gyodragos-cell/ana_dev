"""Safe optimization snapshot persistence for ANA MAX v24.

Snapshots are written only under an explicitly provided dev workspace root.
Public release paths are rejected by default.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


def _utc_now() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class OptimizationSnapshotRecord:
    """Persistable optimization snapshot payload."""

    reliability: Mapping[str, float] = field(default_factory=dict)
    noise: Mapping[str, float] = field(default_factory=dict)
    latency: Mapping[str, float] = field(default_factory=dict)
    failure_streak: Mapping[str, int] = field(default_factory=dict)
    scenario_effectiveness: Mapping[str, Mapping[str, float]] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe snapshot record."""
        return {
            "reliability": dict(self.reliability),
            "noise": dict(self.noise),
            "latency": dict(self.latency),
            "failure_streak": dict(self.failure_streak),
            "scenario_effectiveness": {
                name: dict(values) for name, values in self.scenario_effectiveness.items()
            },
            "created_at": self.created_at,
        }


class OptimizationSnapshotManager:
    """Save and load optimization snapshots inside the dev workspace."""

    def __init__(self, workspace_root: str | Path, safe_mode: bool = True) -> None:
        """Initialize the snapshot directory with safe-mode guards."""
        self.workspace_root = Path(workspace_root).resolve()
        self.safe_mode = safe_mode
        self.snapshot_dir = self.workspace_root / ".ana_max" / "optimization"

    def save_snapshot(self, name: str, snapshot: OptimizationSnapshotRecord | Mapping[str, Any]) -> Path:
        """Persist a snapshot JSON file under the dev workspace."""
        self._ensure_safe_path()
        payload = snapshot.to_dict() if isinstance(snapshot, OptimizationSnapshotRecord) else dict(snapshot)
        path = self._snapshot_path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path

    def load_snapshot(self, name: str) -> dict[str, Any]:
        """Load a snapshot JSON file from the dev workspace."""
        path = self._snapshot_path(name)
        return json.loads(path.read_text(encoding="utf-8"))

    def _snapshot_path(self, name: str) -> Path:
        """Return the validated snapshot path for a name."""
        safe_name = "".join(ch for ch in name if ch.isalnum() or ch in {"-", "_"}).strip("_")
        if not safe_name:
            raise ValueError("snapshot name must contain safe characters")
        path = (self.snapshot_dir / f"{safe_name}.json").resolve()
        if not str(path).startswith(str(self.workspace_root)):
            raise ValueError("snapshot path escapes workspace root")
        return path

    def _ensure_safe_path(self) -> None:
        """Reject obvious public release paths while safe-mode is active."""
        if self.safe_mode and "ANA_MAX_GitHub_Release" in str(self.workspace_root):
            raise PermissionError("safe-mode blocks optimization snapshots in public release")


__all__ = ["OptimizationSnapshotManager", "OptimizationSnapshotRecord"]
