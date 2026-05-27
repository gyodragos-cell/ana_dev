"""Distributed runtime core for ANA MAX v27."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping
from uuid import uuid4

from core.cluster_manager import ClusterManager
from core.distributed_memory import DistributedMemory
from core.remote_execution import RemoteExecution


Transport = Callable[[str, Mapping[str, Any]], Mapping[str, Any]]


@dataclass(frozen=True)
class DistributedNode:
    """One distributed runtime node."""

    node_id: str
    role: str
    healthy: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MessageEnvelope:
    """Message envelope for fake distributed routing."""

    message_id: str
    source: str
    target: str
    kind: str
    payload: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe message."""
        return {
            "message_id": self.message_id,
            "source": self.source,
            "target": self.target,
            "kind": self.kind,
            "payload": dict(self.payload),
        }


class DistributedRuntime:
    """Register nodes, pass messages, and route tasks between nodes."""

    VALID_ROLES = {"planner", "executor", "memory", "gateway"}

    def __init__(
        self,
        transport: Transport | None = None,
        cluster_manager: ClusterManager | None = None,
        remote_execution: RemoteExecution | None = None,
        distributed_memory: DistributedMemory | None = None,
    ) -> None:
        """Initialize distributed runtime."""
        self.nodes: dict[str, DistributedNode] = {}
        self.transport = transport or (lambda target, payload: {"success": True, "target": target, "payload": dict(payload)})
        self.cluster_manager = cluster_manager or ClusterManager()
        self.remote_execution = remote_execution or RemoteExecution()
        self.distributed_memory = distributed_memory or DistributedMemory()

    def register_node(self, node_id: str, role: str, metadata: Mapping[str, Any] | None = None) -> DistributedNode:
        """Register a distributed node."""
        if role not in self.VALID_ROLES:
            raise ValueError(f"unsupported node role: {role}")
        node = DistributedNode(node_id, role, True, dict(metadata or {}))
        self.nodes[node_id] = node
        self.cluster_manager.join(node_id, {"role": role})
        return node

    def send_message(self, source: str, target: str, kind: str, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """Send a fake message to a registered node."""
        if source not in self.nodes or target not in self.nodes:
            return {"success": False, "error": "unknown source or target"}
        envelope = MessageEnvelope(str(uuid4()), source, target, kind, dict(payload or {}))
        try:
            return dict(self.transport(target, envelope.to_dict()))
        except Exception as error:
            return {"success": False, "error": str(error), "target": target}

    def route_task(self, tool_name: str, arguments: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """Route a tool task to an available node and fallback locally on failure."""
        node_id = self.cluster_manager.choose_node()
        if node_id is None:
            return {"success": False, "error": "no healthy nodes", "tool": tool_name}
        result = self.remote_execution.call(node_id, tool_name, arguments or {})
        result["routed_node"] = node_id
        self.distributed_memory.write(f"last_task:{tool_name}", result, node_id=node_id)
        return result


__all__ = ["DistributedNode", "DistributedRuntime", "MessageEnvelope"]
