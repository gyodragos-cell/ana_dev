"""Session lifecycle orchestration tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ANA_ROOT = ROOT / "ANA_MAX"
sys.path.insert(0, str(ANA_ROOT))

from core.session_lifecycle import SessionLifecycle  # noqa: E402
from tools.base import ToolResult, ToolStatus  # noqa: E402
from tools.session_lifecycle_tool import SessionLifecycleTool  # noqa: E402


class FakeTool:
    def __init__(self, name: str, data=None) -> None:
        self.name = name
        self.calls = []
        self.data = data if data is not None else {"tool": name}

    def execute(self, **kwargs):
        self.calls.append(kwargs)
        return ToolResult(
            status=ToolStatus.SUCCESS,
            data=self.data,
            message=f"{self.name} ok",
        )


def test_wake_first_run_writes_manifest_and_observes_workspace(tmp_path: Path) -> None:
    awareness = FakeTool("workspace_situational_awareness", {"recommended_next_step": "observe"})
    lifecycle = SessionLifecycle(
        root=tmp_path,
        tools={"workspace_situational_awareness": awareness},
    )

    result = lifecycle.wake()

    assert result["status"] == "first_run"
    assert result["source"] == "fresh_start"
    assert awareness.calls == [
        {"include_git": True, "include_uia": False, "include_errors": True}
    ]

    manifest = json.loads((tmp_path / "memory" / "session_manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "first_run"
    assert manifest["source"] == "fresh_start"
    assert manifest["workspace_situational_awareness"]["success"] is True


def test_wake_resumes_from_latest_rem_report(tmp_path: Path) -> None:
    reports = tmp_path / "docs" / "rem_sleep"
    reports.mkdir(parents=True)
    old = reports / "REM_SLEEP_REPORT_2026-01-01T000000+0000.md"
    new = reports / "REM_SLEEP_REPORT_2026-01-02T000000+0000.md"
    old.write_text("# old", encoding="utf-8")
    new.write_text("# latest\nContinue router work.", encoding="utf-8")

    lifecycle = SessionLifecycle(root=tmp_path)
    result = lifecycle.wake()

    assert result["status"] == "resumed"
    assert result["source"] == "last_rem"
    assert result["last_rem_report"].endswith(new.name)

    manifest = json.loads((tmp_path / "memory" / "session_manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "resumed"
    assert manifest["last_rem_report"].endswith(new.name)
    assert "Continue router work" in manifest["last_rem_excerpt"]


def test_rest_defaults_to_preview_analyze_without_consolidating(tmp_path: Path) -> None:
    rem = FakeTool("session_rem_sleep", {"headline": "analysis only"})
    lifecycle = SessionLifecycle(root=tmp_path, tools={"session_rem_sleep": rem})

    result = lifecycle.rest()

    assert result["action"] == "analyze"
    assert result["write_status"] == "preview_only"
    assert "Save it" in result["operator_prompt"]
    assert rem.calls[0]["action"] == "analyze"


def test_rest_can_consolidate_explicitly(tmp_path: Path) -> None:
    rem = FakeTool("session_rem_sleep", {"headline": "saved"})
    lifecycle = SessionLifecycle(root=tmp_path, tools={"session_rem_sleep": rem})

    result = lifecycle.rest(consolidate=True)

    assert result["action"] == "consolidate"
    assert result["write_status"] == "consolidated"
    assert rem.calls[0]["action"] == "consolidate"


def test_recommend_uses_agent_coach_recommend(tmp_path: Path) -> None:
    coach = FakeTool("agent_coach", {"primary_tool": "error_radar"})
    lifecycle = SessionLifecycle(root=tmp_path, tools={"agent_coach": coach})

    result = lifecycle.recommend("fix python error", error="ValueError", max_tools=3)

    assert result["phase"] == "recommend"
    assert result["success"] is True
    assert coach.calls[0]["action"] == "recommend"
    assert coach.calls[0]["task"] == "fix python error"
    assert coach.calls[0]["error"] == "ValueError"
    assert coach.calls[0]["max_tools"] == 3


def test_session_lifecycle_tool_exposes_rest_preview() -> None:
    tool = SessionLifecycleTool()
    definition = tool.get_definition()

    assert definition.name == "session_lifecycle"
    assert any(param.name == "consolidate" for param in definition.parameters)
