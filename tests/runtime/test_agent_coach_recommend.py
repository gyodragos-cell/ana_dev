from __future__ import annotations

import json
import sys
from pathlib import Path


ANA_MAX_DIR = Path(__file__).resolve().parents[2] / "ANA_MAX"
if str(ANA_MAX_DIR) not in sys.path:
    sys.path.insert(0, str(ANA_MAX_DIR))

from tools.agent_coach_tool import AgentCoachTool  # noqa: E402


def test_agent_coach_recommend_uses_tool_router_for_error_task(tmp_path: Path) -> None:
    coach = AgentCoachTool()
    coach.log_file = tmp_path / "observability.jsonl"
    coach.memory_file = tmp_path / "agent_coach_lessons.jsonl"

    result = coach.execute(
        action="recommend",
        task="PowerShell command failed twice with encoding error",
        error="UnicodeEncodeError",
        max_tools=4,
        include_prompt=False,
    )

    assert result.is_success
    assert result.data["schema"] == "ana.agent_coach.recommend.v1"
    assert result.data["router"]["mode"] == "failure"
    assert "active_profiles" in result.data["router"]
    assert "tool_profiles" in result.data["router"]
    assert result.data["primary_tool"] == "error_radar"
    assert result.data["tool_stack"] == [
        "error_radar",
        "agent_coach",
        "ana_memory",
        "debugger",
    ]


def test_agent_coach_recommend_uses_telemetry_for_repeated_failures(tmp_path: Path) -> None:
    log_file = tmp_path / "observability.jsonl"
    entries = [
        {
            "timestamp": "2026-05-27T00:00:00Z",
            "tool": "tool_contract_validator",
            "args": {"action": "validate_tool", "tool_name": "missing"},
            "latency_sec": 0.0,
            "status": "error",
            "error": "Missing tool",
        }
        for _ in range(3)
    ]
    log_file.write_text("\n".join(json.dumps(entry) for entry in entries), encoding="utf-8")

    coach = AgentCoachTool()
    coach.log_file = log_file
    coach.memory_file = tmp_path / "agent_coach_lessons.jsonl"

    result = coach.execute(
        action="recommend",
        task="",
        max_tools=5,
        repeat_threshold=5,
        include_prompt=True,
    )

    assert result.is_success
    assert result.data["severity"] == "critical"
    assert result.data["router"]["mode"] == "failure"
    assert result.data["primary_tool"] == "error_radar"
    assert "tool_healthcheck" in result.data["tool_stack"]
    assert "prompt_for_qoder" in result.data


def test_agent_coach_ignores_lab_monitor_noise(tmp_path: Path) -> None:
    log_file = tmp_path / "observability.jsonl"
    entries = []
    entries.extend(
        {
            "timestamp": "2026-05-27T00:00:00Z",
            "tool": "event_stream",
            "args": {"action": "stats", "hours": "1"},
            "latency_sec": 0.0,
            "status": "success",
            "error": None,
        }
        for _ in range(10)
    )
    entries.extend(
        {
            "timestamp": "2026-05-27T00:00:00Z",
            "tool": "tool_contract_validator",
            "args": {"action": "validate_tool", "tool_name": "definitely_missing_tool_for_guidance"},
            "latency_sec": 0.0,
            "status": "error",
            "error": "success=false",
        }
        for _ in range(5)
    )
    entries.extend(
        {
            "timestamp": "2026-05-27T00:00:01Z",
            "tool": "graph_context_pack",
            "args": {"action": "stats"},
            "latency_sec": 0.2,
            "status": "success",
            "error": None,
        }
        for _ in range(12)
    )
    entries.extend(
        {
            "timestamp": "2026-05-27T00:00:01Z",
            "tool": "code_context_pack",
            "args": {
                "query": "operator status reload behavior",
                "limit": "1",
                "include_graph": "True",
                "include_text": "False",
            },
            "latency_sec": 1.0,
            "status": "success",
            "error": None,
        }
        for _ in range(12)
    )
    entries.extend(
        {
            "timestamp": "2026-05-27T00:00:01Z",
            "tool": "code_context_pack",
            "args": {"task": "ANA nucleus smoke graph context", "limit": "3", "include_graph": "True"},
            "latency_sec": 1.0,
            "status": "success",
            "error": None,
        }
        for _ in range(12)
    )
    entries.extend(
        {
            "timestamp": "2026-05-27T00:00:01Z",
            "tool": "code_context_pack",
            "args": {"task": "ANA lab autonomous readiness pass", "limit": "5", "include_graph": "True"},
            "latency_sec": 1.0,
            "status": "success",
            "error": None,
        }
        for _ in range(12)
    )
    entries.extend(
        {
            "timestamp": "2026-05-27T00:00:01Z",
            "tool": "code_context_pack",
            "args": {
                "query": "next scoped lab action after green baseline",
                "limit": "5",
                "include_graph": "True",
                "include_text": "False",
            },
            "latency_sec": 1.0,
            "status": "success",
            "error": None,
        }
        for _ in range(12)
    )
    entries.extend(
        {
            "timestamp": "2026-05-27T00:00:01Z",
            "tool": "tool_router",
            "args": {"task": "ANA nucleus smoke code context verify", "max_tools": "6"},
            "latency_sec": 0.1,
            "status": "success",
            "error": None,
        }
        for _ in range(12)
    )
    entries.extend(
        {
            "timestamp": "2026-05-27T00:00:01Z",
            "tool": "session_audit",
            "args": {"action": "trust", "hours": "1", "limit": "40"},
            "latency_sec": 0.02,
            "status": "success",
            "error": None,
        }
        for _ in range(12)
    )
    entries.extend(
        {
            "timestamp": "2026-05-27T00:00:01Z",
            "tool": "error_radar",
            "args": {"scope": "git", "limit": "20"},
            "latency_sec": 0.06,
            "status": "success",
            "error": None,
        }
        for _ in range(12)
    )
    entries.extend(
        {
            "timestamp": "2026-05-27T00:00:02Z",
            "tool": "router_failure_demo",
            "args": {},
            "latency_sec": 0.0,
            "status": "error",
            "error": "demo failure",
        }
        for _ in range(4)
    )
    entries.extend(
        {
            "timestamp": "2026-05-27T00:00:03Z",
            "tool": "tool_router",
            "args": {"task": "Tool router_failure_demo failed", "error": "demo failure"},
            "latency_sec": 0.0,
            "status": "success",
            "error": None,
        }
        for _ in range(4)
    )
    log_file.write_text("\n".join(json.dumps(entry) for entry in entries), encoding="utf-8")

    coach = AgentCoachTool()
    coach.log_file = log_file
    coach.memory_file = tmp_path / "agent_coach_lessons.jsonl"

    result = coach.execute(action="recommend", task="ANA lab hub periodic check", include_prompt=False)

    assert result.is_success
    assert result.data["severity"] == "ok"
    assert result.data["coach"]["signals"] == []
