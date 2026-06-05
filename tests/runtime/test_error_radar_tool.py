from pathlib import Path

import sys


ROOT = Path(__file__).resolve().parents[2]
ANA_MAX = ROOT / "ANA_MAX"
if str(ANA_MAX) not in sys.path:
    sys.path.insert(0, str(ANA_MAX))

from tools.error_radar_tool import ERROR_PATTERNS, ErrorRadarTool


def _matches(kind: str, text: str) -> bool:
    pattern = dict(ERROR_PATTERNS)[kind]
    return bool(pattern.search(text))


def test_auth_pattern_ignores_log_timestamp_milliseconds():
    line = "2026-05-28 19:50:24,403 - __main__ - INFO - HTTP /mcp tools/call end success=True"

    assert not _matches("auth", line)


def test_auth_pattern_matches_real_auth_failures():
    assert _matches("auth", "HTTP 403 forbidden")
    assert _matches("auth", "status_code=401")
    assert _matches("auth", "unauthorized request")


def test_monitor_noise_ignores_successful_mcp_info_lines():
    radar = ErrorRadarTool()
    line = "2026-05-28 19:50:24,403 - __main__ - INFO - HTTP /mcp tools/call end name=agent_coach success=True"

    assert radar._is_monitor_noise(line)


def test_monitor_noise_ignores_debugger_traceback_argument_lines():
    radar = ErrorRadarTool()
    http_line = "2026-05-31 13:02:42,704 - __main__ - INFO - HTTP /mcp tools/call start name=debugger id=762691 args=['action', 'traceback_text']"
    tool_line = "2026-05-31 13:02:42,704 - tools.base - INFO - TOOL START name=debugger args={'action': \"'analyze'\", 'traceback_text': \"'ValueError: ana smoke test'\"}"

    assert radar._is_monitor_noise(http_line)
    assert radar._is_monitor_noise(tool_line)


def test_dirty_tree_breakdown_groups_lab_changes():
    radar = ErrorRadarTool()
    details = radar._dirty_tree_breakdown(
        [
            " M ANA_MAX/tools/error_radar_tool.py",
            "?? docs/examples/ERROR_RADAR_FINDING_EXAMPLE.md",
            "?? tests/runtime/test_error_radar_tool.py",
            "?? ANA_MAX/docs/SESSION_CHECKPOINT_2026-05-31T001333Z0000.md",
        ]
    )

    assert details["total"] == 4
    assert details["tracked"] == 1
    assert details["untracked"] == 3
    assert details["docs"] == 2
    assert details["examples"] == 1
    assert details["tests"] == 1
    assert details["runtime"] == 1
    assert details["checkpoints"] == 1
    assert details["sample_paths"][0] == "ANA_MAX/tools/error_radar_tool.py"


def test_dirty_tree_breakdown_counts_runtime_from_ana_root_paths():
    radar = ErrorRadarTool()
    details = radar._dirty_tree_breakdown(
        [
            " M tools/error_radar_tool.py",
            " M core/agent.py",
            "?? dev_artifacts/scripts/ana_patch_advisor.py",
            " M main.py",
        ]
    )

    assert details["runtime"] == 4


def test_error_radar_sorts_before_limit_and_summarizes(monkeypatch):
    radar = ErrorRadarTool()

    monkeypatch.setattr(radar, "_scan_logs", lambda limit: [
        {"source": "ana_max.log", "kind": "auth", "severity": "medium", "summary": "HTTP 403 forbidden"},
        {"source": "ana_max.log", "kind": "auth", "severity": "medium", "summary": "HTTP 403 forbidden"},
    ])
    monkeypatch.setattr(radar, "_scan_git", lambda: [
        {"source": "git", "kind": "large_dirty_tree", "severity": "medium", "summary": "lots changed"},
    ])
    monkeypatch.setattr(radar, "_scan_windows", lambda: [
        {"source": "visible_window", "kind": "visible_error", "severity": "high", "summary": "Crash dialog"},
    ])

    result = radar.execute(scope="all", limit=2)
    findings = result.data["findings"]

    assert [item["kind"] for item in findings] == ["visible_error", "auth"]
    assert result.data["summary"]["top_kind"] == "visible_error"
    assert result.data["summary"]["top_severity"] == "high"
    assert result.data["summary"]["by_kind"] == {"visible_error": 1, "auth": 1}
