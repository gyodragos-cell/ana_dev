from ana.config.loader import ConfigLoader
from ana.core.orchestrator.orchestrator import ANAMaxOS
from ana.tools.registry.registry import FallbackToolSpec, ToolRegistry


def _config(services):
    return ConfigLoader().from_mapping(
        {
            "mode": "dev",
            "services": services,
            "event_bus": {"replay_limit": 20},
            "fallback": {"max_attempts": 1},
            "sandbox": {"max_input_keys": 8, "allow_external_effects": False},
            "logging": {"level": "info"},
        }
    )


def test_cooperation_self_repairs_missing_primary_with_registered_fallback():
    registry = ToolRegistry()
    registry.register_fallback(
        FallbackToolSpec(
            "cooperative_default",
            "llm.complete",
            lambda payload: {
                "text": f"fallback handled: {payload['prompt']}",
                "model": "cooperative-fallback",
            },
        )
    )
    os_v2 = ANAMaxOS(config=_config(["llm"]), registry=registry)

    response = os_v2.execute(
        "llm.complete",
        {"prompt": "missing primary"},
        trace_id="trace-cooperate",
    )

    assert response.ok is True
    assert response.output["result"]["text"] == "fallback handled: missing primary"
    assert response.output["cooperation"]["self_repair"]["repaired"] is True
    assert response.output["cooperation"]["self_repair"]["fallback"] == "cooperative_default"
    routed_events = os_v2.event_bus.replay("orchestrator.routed")
    assert routed_events[0].payload["self_repair"] is True


def test_cooperation_explains_unrepairable_missing_route_without_guessing():
    os_v2 = ANAMaxOS(config=_config(["llm"]), registry=ToolRegistry())

    response = os_v2.execute(
        "llm.complete",
        {"prompt": "no route"},
        trace_id="trace-no-guess",
    )

    assert response.ok is False
    assert response.error is not None
    assert response.error.code == "ROUTING_FAILURE"
    assert response.error.details["self_repair_attempted"] is True
    assert response.error.details["fallback_attempted"] is False
    assert response.output["cooperation"]["zero_guessing"] is True
    assert "Register ToolSpec or FallbackToolSpec" in response.output["cooperation"]["next_action"]
