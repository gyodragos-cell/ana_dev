"""Goal-driven execution manager for ANA MAX v26."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


@dataclass
class Goal:
    """A high-level goal mapped to tasks."""

    goal_id: str
    description: str
    tasks: list[str] = field(default_factory=list)
    completed: set[str] = field(default_factory=set)

    def progress(self) -> float:
        """Return completion progress from 0.0 to 1.0."""
        return len(self.completed) / len(self.tasks) if self.tasks else 0.0

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe goal state."""
        return {
            "goal_id": self.goal_id,
            "description": self.description,
            "tasks": list(self.tasks),
            "completed": sorted(self.completed),
            "progress": self.progress(),
            "done": self.progress() >= 1.0,
        }


class GoalManager:
    """Define goals, decompose them into tasks, and track progress."""

    def __init__(self) -> None:
        """Initialize empty goal registry."""
        self.goals: dict[str, Goal] = {}

    def define_goal(self, description: str, tasks: list[str] | None = None) -> Goal:
        """Create a goal with optional tasks."""
        task_list = tasks or [f"observe {description}", f"execute {description}", f"verify {description}"]
        goal = Goal(str(uuid4()), description, task_list)
        self.goals[goal.goal_id] = goal
        return goal

    def mark_complete(self, goal_id: str, task: str) -> Goal:
        """Mark a goal task complete."""
        goal = self.goals[goal_id]
        if task in goal.tasks:
            goal.completed.add(task)
        return goal


__all__ = ["Goal", "GoalManager"]
