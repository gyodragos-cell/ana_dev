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
