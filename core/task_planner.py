"""Task graph planner for ANA MAX v26 preparation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping
from uuid import uuid4


@dataclass(frozen=True)
class PlanNode:
    """One task graph node."""

    node_id: str
    description: str
    role: str = "analysis"
    dependencies: tuple[str, ...] = field(default_factory=tuple)
    checkpoint: bool = False
    completed: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe plan node."""
        return {
            "node_id": self.node_id,
            "description": self.description,
            "role": self.role,
            "dependencies": list(self.dependencies),
            "checkpoint": self.checkpoint,
            "completed": self.completed,
        }


class TaskPlanner:
    """Decompose tasks and assign them to agents or tools."""

    def decompose(self, task: str) -> list[PlanNode]:
        """Break a task into simple observe/execute/verify nodes."""
        observe = PlanNode(str(uuid4()), f"observe: {task}", "observer")
        execute = PlanNode(str(uuid4()), f"execute: {task}", "executor", (observe.node_id,))
        verify = PlanNode(str(uuid4()), f"verify: {task}", "critic", (execute.node_id,))
        return [observe, execute, verify]

    def long_horizon(self, task: str, phases: int = 3) -> list[PlanNode]:
        """Create a checkpointed long-horizon task graph."""
        nodes: list[PlanNode] = []
        previous = ""
        for index in range(phases):
            node = PlanNode(str(uuid4()), f"phase {index + 1}: {task}", "executor", (previous,) if previous else (), checkpoint=True)
            nodes.append(node)
            previous = node.node_id
        return nodes

    def resume_from_checkpoint(self, nodes: list[PlanNode], completed_ids: set[str]) -> list[PlanNode]:
        """Return incomplete nodes after a checkpoint resume."""
        return [node for node in nodes if node.node_id not in completed_ids]

    def build_graph(self, task: str) -> dict[str, Any]:
        """Build a task graph mapping."""
        nodes = self.decompose(task)
        return {"nodes": [node.to_dict() for node in nodes]}

    def assign(self, nodes: list[PlanNode], agent_manager: Any) -> list[dict[str, Any]]:
        """Assign plan nodes to agents."""
        return [agent_manager.spawn_agent(node.role, node.description).to_dict() for node in nodes]


__all__ = ["PlanNode", "TaskPlanner"]
