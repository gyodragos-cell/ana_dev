"""Agent manager tests."""

from core.agent_manager import AgentManager


def test_agent_spawn():
    """Agent manager should spawn supported agent roles."""
    manager = AgentManager()

    agent = manager.spawn_agent("tool", "run grep")

    assert agent.agent_id in manager.agents
    assert agent.role == "tool"


def test_agent_routing():
    """Agent manager should route task types to roles."""
    manager = AgentManager()

    agent = manager.route_agent("scenario", "run fake scenario")

    assert agent.role == "scenario"


def test_agent_cleanup():
    """Agent manager should clean up spawned agents."""
    manager = AgentManager()
    agent = manager.spawn_agent("analysis", "inspect")

    assert manager.cleanup_agent(agent.agent_id) is True
    assert manager.snapshot()["agents"] == {}
