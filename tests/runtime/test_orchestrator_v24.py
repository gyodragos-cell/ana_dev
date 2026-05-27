"""Orchestrator v24 tests."""

import time

from core.orchestrator import Orchestrator


def test_parallel_execution():
    """Orchestrator should run multiple queued tasks."""
    orchestrator = Orchestrator({"double": lambda payload: payload["value"] * 2}, max_workers=2)
    orchestrator.add_task("double", {"value": 2})
    orchestrator.add_task("double", {"value": 3})

    results = orchestrator.run_parallel()

    assert sorted(item["result"] for item in results) == [4, 6]


def test_timeout_enforcement():
    """Orchestrator should report timeout failures."""
    def slow(payload):
        time.sleep(0.05)
        return "late"

    orchestrator = Orchestrator({"slow": slow})
    orchestrator.add_task("slow", timeout_seconds=0.001)

    result = orchestrator.run_next()

    assert result["success"] is False
    assert "timed out" in result["error"]


def test_priority_routing():
    """Lower priority number should execute first."""
    orchestrator = Orchestrator({"echo": lambda payload: payload["value"]})
    orchestrator.add_task("echo", {"value": "low"}, priority=10)
    orchestrator.add_task("echo", {"value": "high"}, priority=1)

    result = orchestrator.run_next()

    assert result["result"] == "high"
