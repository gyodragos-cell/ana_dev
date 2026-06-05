from __future__ import annotations

import json
import sys
from pathlib import Path


ANA_MAX_DIR = Path(__file__).resolve().parents[2] / "ANA_MAX"
if str(ANA_MAX_DIR) not in sys.path:
    sys.path.insert(0, str(ANA_MAX_DIR))

from tools.session_rem_sleep_tool import SessionRemSleepTool  # noqa: E402


def _tool_with_tmp_root(tmp_path: Path) -> SessionRemSleepTool:
    tool = SessionRemSleepTool()
    tool.root = tmp_path
    tool.docs_dir = tmp_path / "docs"
    tool.memory_dir = tmp_path / "memory"
    tool.log_file = tmp_path / "logs" / "observability.jsonl"
    tool.reports_dir = tool.docs_dir / "rem_sleep"
    tool.conversation_file = tool.memory_dir / "conversation_learning.jsonl"
    tool.docs_dir.mkdir(parents=True)
    tool.memory_dir.mkdir(parents=True)
    tool.log_file.parent.mkdir(parents=True)
    return tool


def test_session_rem_sleep_analyze_extracts_patterns(tmp_path: Path) -> None:
    tool = _tool_with_tmp_root(tmp_path)
    (tool.docs_dir / "SESSION_CHECKPOINT_2026-05-27T000000Z.md").write_text(
        "\n".join(
            [
                "Validation passed: no-reload quality gate is green.",
                "Risk: old MCP server needs restart before new tools are visible.",
            ]
        ),
        encoding="utf-8",
    )
    entries = [
        {"tool": "tool_contract_validator", "status": "error", "error": "missing tool"},
        {"tool": "tool_contract_validator", "status": "error", "error": "missing tool"},
    ]
    tool.log_file.write_text("\n".join(json.dumps(entry) for entry in entries), encoding="utf-8")

    result = tool.execute(action="analyze", telemetry_limit=10)

    assert result.is_success
    assert result.data["schema"] == "ana.session_rem_sleep.v1"
    assert result.data["inspected"]["checkpoints"] == 1
    assert result.data["worked"]
    assert any("tool_contract_validator" in item for item in result.data["mistakes_or_friction"])
    assert any("agent_coach" in item for item in result.data["recommendations"])


def test_session_rem_sleep_consolidate_writes_report_without_memory(tmp_path: Path) -> None:
    tool = _tool_with_tmp_root(tmp_path)
    (tool.docs_dir / "SESSION_CHECKPOINT_2026-05-27T000000Z.md").write_text(
        "OK: smart readiness passed.",
        encoding="utf-8",
    )

    result = tool.execute(action="consolidate", save_memory=False)

    assert result.is_success
    report_path = Path(result.data["saved_report"])
    assert report_path.exists()
    assert "REM Sleep Report" in report_path.read_text(encoding="utf-8")

    latest = tool.execute(action="latest")
    assert latest.is_success
    assert latest.data["found"] is True


def test_session_rem_sleep_latest_returns_newest_written_report(tmp_path: Path) -> None:
    tool = _tool_with_tmp_root(tmp_path)
    tool.reports_dir.mkdir(parents=True, exist_ok=True)
    old = tool.reports_dir / "REM_SLEEP_REPORT_2026-05-31T190000+0000.md"
    new = tool.reports_dir / "REM_SLEEP_REPORT_2026-05-31T221219+0000.md"
    old.write_text("# old\n", encoding="utf-8")
    new.write_text("# new\n", encoding="utf-8")

    latest = tool.execute(action="latest")

    assert latest.is_success
    assert latest.data["found"] is True
    assert latest.data["path"].endswith(new.name)
    assert "# new" in latest.data["content"]
