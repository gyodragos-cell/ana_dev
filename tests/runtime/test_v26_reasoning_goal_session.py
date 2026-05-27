"""Tests for v26 reasoning, critic, goals, feedback, and sessions."""

import time

from core.agent_manager import AgentManager
from core.audit_trail import AuditTrail
from core.auto_repair import AutoRepairEngine
from core.goal_manager import GoalManager
from core.human_feedback import HumanFeedback
from core.observability import Observability
from core.policy_engine import PolicyEngine
from core.reasoning_engine import ReasoningEngine
from core.self_evaluation import SelfEvaluation
from core.session_manager import SessionManager
from core.task_planner import TaskPlanner


def test_reasoning_influences_planning_without_public_content():
    """Reasoning engine should return hints and safe public traces."""
    engine = ReasoningEngine()
    step = engine.add_step("audit repo needs observe first", "planning")
    assert engine.influence_planning("audit repo")["hint_count"] == 1
    assert "summary" not in engine.public_trace()[0]
    assert engine.public_trace()[0]["step_id"] == step.step_id


def test_critic_catches_issues_and_feeds_repair():
    """Self evaluation should catch obvious issues and create repair event."""
    critic = SelfEvaluation()
    evaluation = critic.evaluate_plan({"steps": []})
    repair = AutoRepairEngine().plan_repair(critic.suggest_repair_event(evaluation))
    assert evaluation.passed is False
    assert repair.strategy in {"diagnose", "suggest_patch"}


def test_long_horizon_resume_and_session_integration():
    """Task planner should resume from checkpoint with session memory."""
    planner = TaskPlanner()
    nodes = planner.long_horizon("ship release", phases=3)
    remaining = planner.resume_from_checkpoint(nodes, {nodes[0].node_id})
    sessions = SessionManager()
    session = sessions.create_session({"plan": "ship"}, max_steps=2)
    sessions.record_step(session.session_id)
    sessions.add_memory(session.session_id, {"remaining": len(remaining)})
    assert len(remaining) == 2
    assert sessions.resume_session(session.session_id).memory[0]["remaining"] == 2


def test_goal_decomposition_progress_completion():
    """Goal manager should decompose and track completion."""
    manager = GoalManager()
    goal = manager.define_goal("audit", ["observe", "verify"])
    manager.mark_complete(goal.goal_id, "observe")
    assert goal.progress() == 0.5
    manager.mark_complete(goal.goal_id, "verify")
    assert goal.to_dict()["done"] is True


def test_agent_negotiation_and_audit_logging():
    """Agents should negotiate and audit should log high-level decision."""
    agents = AgentManager()
    planner = agents.spawn_agent("planner", "plan")
    critic = agents.spawn_agent("critic", "critic")
    winner = agents.resolve_conflict([planner.agent_id, critic.agent_id])
    audit = AuditTrail()
    audit.record("negotiation", {"winner": winner})
    assert winner == critic.agent_id
    assert audit.events[0].event_type == "negotiation"


def test_session_ttl_policy_and_archive(tmp_path):
    """Session manager should enforce TTL, policy, and archive."""
    sessions = SessionManager()
    session = sessions.create_session(ttl_seconds=0.001, max_steps=1)
    time.sleep(0.002)
    assert sessions.is_expired(session.session_id) is True
    sessions.record_step(session.session_id)
    try:
        sessions.record_step(session.session_id)
        assert False
    except PermissionError:
        pass
    assert sessions.archive_session(session.session_id, tmp_path).exists()


def test_human_feedback_influences_routing_and_respects_policy():
    """Human feedback should create score adjustments."""
    feedback = HumanFeedback(PolicyEngine(safe_mode=True))
    feedback.record("grep_file", 1.0, "good")
    assert feedback.routing_feedback("grep_file")["score_boost"] > 0


def test_advanced_observability_events_safe_filtering():
    """Observability should emit advanced events and filter payloads."""
    obs = Observability()
    obs.record_reasoning_event({"safe_trace": [{"step": "x"}], "private": "hidden"})
    obs.record_goal_event({"goal": "audit", "progress": 1})
    assert len(obs.filtered_events(safe_mode=True)) == 2
    assert "safe_trace" in obs.filtered_events(safe_mode=False)[0]["payload"]
