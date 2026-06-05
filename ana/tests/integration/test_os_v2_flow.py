from ana.config.loader import ConfigLoader
from ana.core.orchestrator.orchestrator import ANAMaxOS
from ana.services.http.service import FakeHTTPService, HTTPResponse
from ana.services.llm.service import DeterministicLLMService
from ana.services.shell.service import DeterministicShellService
from ana.tools.registry.registry import FallbackToolSpec, ToolRegistry, ToolSpec


def test_os_v2_executes_registered_services_with_traceable_events(tmp_path):
    config = ConfigLoader().from_mapping(
        {
            "mode": "dev",
            "services": ["http", "shell", "llm"],
            "event_bus": {"replay_limit": 20},
            "fallback": {"max_attempts": 1},
            "sandbox": {"max_input_keys": 8, "allow_external_effects": False},
            "logging": {"level": "info"},
        }
    )
    http = FakeHTTPService()
    http.register("GET", "https://ana.local/health", HTTPResponse(200, {"ok": True}))
    shell = DeterministicShellService()
    shell.register(("ana", "health"), lambda command: {"code": 0, "stdout": "ok"})
    llm = DeterministicLLMService()
    llm.register("hello", "hello from deterministic-fake")

    registry = ToolRegistry()
    registry.register(ToolSpec("http_fake", "http.request", http.request))
    registry.register(ToolSpec("shell_fake", "shell.run", shell.run))
    registry.register(ToolSpec("llm_fake", "llm.complete", llm.complete))
    registry.register_fallback(
        FallbackToolSpec(
            "llm_default",
            "llm.complete",
            lambda payload: {"text": "fallback response", "model": "fallback"},
        )
    )
    os_v2 = ANAMaxOS(config=config, registry=registry)

    http_response = os_v2.execute(
        "http.request",
        {"url": "https://ana.local/health"},
        trace_id="trace-http",
    )
    shell_response = os_v2.execute(
        "shell.run",
        {"command": ["ana", "health"]},
        trace_id="trace-shell",
    )
    llm_response = os_v2.execute(
        "llm.complete",
        {"prompt": "unknown"},
        trace_id="trace-llm",
    )

    assert http_response.ok is True
    assert http_response.output["result"]["status"] == 200
    assert shell_response.output["result"]["stdout"] == "ok"
    assert llm_response.ok is True
    assert llm_response.output["result"]["text"] == "fallback response"
    assert [event.topic for event in os_v2.event_bus.replay("orchestrator.completed")] == [
        "orchestrator.completed",
        "orchestrator.completed",
        "orchestrator.completed",
    ]


def test_os_v2_fails_unknown_service_without_guessing():
    config = ConfigLoader().from_mapping(
        {
            "mode": "dev",
            "services": ["fs"],
            "event_bus": {"replay_limit": 20},
            "fallback": {"max_attempts": 1},
            "sandbox": {"max_input_keys": 8, "allow_external_effects": False},
            "logging": {"level": "info"},
        }
    )
    response = ANAMaxOS(config=config, registry=ToolRegistry()).execute(
        "llm.complete",
        {"prompt": "hello"},
        trace_id="trace-fail",
    )

    assert response.ok is False
    assert response.error is not None
    assert response.error.code == "ROUTING_FAILURE"


def test_os_v2_registers_declarative_skill_from_skill_engine(monkeypatch, tmp_path):
    skill_root = tmp_path / "skills" / "skills"
    skill_dir = skill_root / "self-repair"
    skill_dir.mkdir(parents=True)
    skill_dir.joinpath("SKILL.md").write_text(
        """# ANA Self-Repair Skill
## Version
1.0.0
## Context
Self-repair declarative skill.
## Scop
Enable skill routing.
## Structura directoare
root
## Componente OS v2
component
## Discipline OS v2
discipline
## Taskuri pentru implementare
### A. task A
### B. task B
### C. task C
### D. task D
### E. task E
### F. task F
### G. task G
### H. task H
### I. task I
### J. task J
### K. task K
## Reguli pentru Codex
rule
## Output asteptat
result
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(ANAMaxOS, "_skill_root", lambda self: skill_root)

    config = ConfigLoader().from_mapping(
        {
            "mode": "dev",
            "services": ["ana"],
            "event_bus": {"replay_limit": 20},
            "fallback": {"max_attempts": 1},
            "sandbox": {"max_input_keys": 8, "allow_external_effects": False},
            "logging": {"level": "info"},
            "skills": {
                "self-repair": {
                    "capability": "ana.self_repair",
                }
            },
        }
    )
    registry = ToolRegistry()
    os_v2 = ANAMaxOS(config=config, registry=registry)

    tools = registry.tools_for("ana.self_repair")
    assert len(tools) == 1
    assert tools[0].name == "skill.self-repair"

    response = os_v2.execute("ana.self_repair", {"prompt": "test"}, trace_id="trace-skill")
    assert response.ok is True
    assert response.output["result"]["skill"] == "self-repair"
    assert response.output["result"]["capability"] == "ana.self_repair"
