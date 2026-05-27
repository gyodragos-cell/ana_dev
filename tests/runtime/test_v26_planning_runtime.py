"""Tests for ANA MAX v26 planning-oriented modules."""

import time

from core.agent_manager import AgentManager
from core.orchestrator import Orchestrator
from core.scenario_simulator import ScenarioSimulator
from core.session_manager import SessionManager
from core.task_planner import TaskPlanner


def test_multi_agent_roles_messages_and_lifecycle():
    """Agent manager should coordinate planner/executor/critic style agents."""
    manager = AgentManager()
    planner = manager.spawn_agent("planner", "plan")
    critic = manager.spawn_agent("critic", "review")
    message = manager.send_message(planner.agent_id, critic.agent_id, "check this")
    assert message["message"] == "check this"
    assert manager.resolve_conflict([planner.agent_id, critic.agent_id]) == critic.agent_id
    assert manager.cleanup_agent(planner.agent_id) is True


def test_task_planner_decomposition_and_assignment():
    """Task planner should build graph and assign agents."""
    planner = TaskPlanner()
    manager = AgentManager()
    nodes = planner.decompose("audit repo")
    assignments = planner.assign(nodes, manager)
    assert len(nodes) == 3
    assert assignments[0]["role"] == "observer"


def test_session_creation_resume_and_isolation():
    """Session manager should create isolated sessions."""
    sessions = SessionManager()
    one = sessions.create_session({"workspace": "one"})
    two = sessions.create_session({"workspace": "two"})
    sessions.add_memory(one.session_id, {"note": "first"})
    assert sessions.resume_session(one.session_id).memory[0]["note"] == "first"
    assert sessions.resume_session(two.session_id).memory == []


def test_orchestrator_dependency_cancellation_timeout():
    """Orchestrator should support dependencies, cancellation, and timeout."""
    orchestrator = Orchestrator({"echo": lambda payload: payload["value"], "slow": lambda payload: time.sleep(0.03)})
    first = orchestrator.add_task("echo", {"value": "first"}, priority=1)
    second = orchestrator.add_task("echo", {"value": "second"}, priority=2)
    orchestrator.add_dependency(second.task_id, first.task_id)
    assert orchestrator.run_next()["result"] == "first"
    assert orchestrator.run_next()["result"] == "second"
    cancelled = orchestrator.add_task("echo", {"value": "x"})
    assert orchestrator.cancel_task(cancelled.task_id) is True
    orchestrator.add_task("slow", timeout_seconds=0.001)
    assert orchestrator.run_next()["success"] is False


def test_advanced_scenario_tags():
    """Scenario simulator should include safe rich scenarios."""
    simulator = ScenarioSimulator()
    result = simulator.run_scenario("complex_failure_chain", {"task": "recover"}).to_dict()
    assert result["name"] == "complex_failure_chain"
    assert "multi_step_recovery" in result["notes"][0]
