"""Parallel orchestrator and scheduler for ANA MAX v24."""

from __future__ import annotations

import concurrent.futures
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping
from uuid import uuid4


TaskCallable = Callable[[Mapping[str, Any]], Any]


@dataclass(order=True)
class ScheduledTask:
    """Priority queue task for orchestrator execution."""

    priority: int
    task_id: str = field(compare=False)
    name: str = field(compare=False)
    payload: Mapping[str, Any] = field(default_factory=dict, compare=False)
    timeout_seconds: float = field(default=5.0, compare=False)


class Orchestrator:
    """Run queued tasks with priority, timeout, and parallel execution."""

    def __init__(self, handlers: Mapping[str, TaskCallable] | None = None, max_workers: int = 4) -> None:
        """Initialize handlers and task queue."""
        self.handlers = dict(handlers or {})
        self.max_workers = max_workers
        self.queue: list[ScheduledTask] = []
        self.cancelled: set[str] = set()
        self.dependencies: dict[str, set[str]] = {}
        self.completed: set[str] = set()

    def add_task(
        self,
        name: str,
        payload: Mapping[str, Any] | None = None,
        priority: int = 10,
        timeout_seconds: float = 5.0,
    ) -> ScheduledTask:
        """Add a scheduled task to the queue."""
        task = ScheduledTask(priority=priority, task_id=str(uuid4()), name=name, payload=dict(payload or {}), timeout_seconds=timeout_seconds)
        self.queue.append(task)
        self.queue.sort()
        return task

    def add_dependency(self, task_id: str, depends_on: str) -> None:
        """Declare that one task depends on another."""
        self.dependencies.setdefault(task_id, set()).add(depends_on)

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a queued task."""
        self.cancelled.add(task_id)
        before = len(self.queue)
        self.queue = [task for task in self.queue if task.task_id != task_id]
        return len(self.queue) != before

    def run_next(self) -> dict[str, Any]:
        """Run the highest-priority queued task."""
        if not self.queue:
            return {"success": False, "error": "queue is empty"}
        for index, task in enumerate(self.queue):
            if self._dependencies_met(task):
                self.queue.pop(index)
                result = self._run_task(task)
                if result.get("success"):
                    self.completed.add(task.task_id)
                return result
        return {"success": False, "error": "dependencies are not met"}

    def run_parallel(self) -> list[dict[str, Any]]:
        """Run all queued tasks in priority order with a thread pool."""
        tasks = list(self.queue)
        self.queue.clear()
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self._run_task, task) for task in tasks if self._dependencies_met(task)]
            results = [future.result() for future in futures]
            self.completed.update(result["task_id"] for result in results if result.get("success"))
            return results

    def run_async(self, task: ScheduledTask) -> threading.Thread:
        """Run one task asynchronously in a daemon thread."""
        thread = threading.Thread(target=self._run_task, args=(task,), daemon=True)
        thread.start()
        return thread

    def schedule_across_nodes(self, tasks: list[str], nodes: list[str]) -> dict[str, list[str]]:
        """Schedule tasks across nodes round-robin."""
        if not nodes:
            return {}
        plan = {node: [] for node in nodes}
        for index, task in enumerate(tasks):
            plan[nodes[index % len(nodes)]].append(task)
        return plan

    def distributed_cancel(self, task_id: str, node_id: str) -> dict[str, str | bool]:
        """Record distributed cancellation intent."""
        cancelled = self.cancel_task(task_id)
        return {"success": cancelled, "task_id": task_id, "node_id": node_id}

    def _run_task(self, task: ScheduledTask) -> dict[str, Any]:
        """Run one task with timeout enforcement."""
        handler = self.handlers.get(task.name)
        if task.task_id in self.cancelled:
            return {"success": False, "task_id": task.task_id, "error": "task cancelled"}
        if handler is None:
            return {"success": False, "task_id": task.task_id, "error": f"no handler for {task.name}"}
        started = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(handler, task.payload)
            try:
                result = future.result(timeout=task.timeout_seconds)
            except concurrent.futures.TimeoutError:
                return {"success": False, "task_id": task.task_id, "error": "task timed out"}
        return {
            "success": True,
            "task_id": task.task_id,
            "name": task.name,
            "result": result,
            "latency_ms": round((time.perf_counter() - started) * 1000, 3),
        }

    def _dependencies_met(self, task: ScheduledTask) -> bool:
        """Return whether all dependencies for a task are completed."""
        return self.dependencies.get(task.task_id, set()).issubset(self.completed)


__all__ = ["Orchestrator", "ScheduledTask"]
