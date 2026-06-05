from __future__ import annotations

import sys
from pathlib import Path


ANA_MAX_DIR = Path(__file__).resolve().parents[2] / "ANA_MAX"
if str(ANA_MAX_DIR) not in sys.path:
    sys.path.insert(0, str(ANA_MAX_DIR))

from tools.base import ToolResult, ToolStatus  # noqa: E402
from tools.input_api_probe_tool import InputApiProbeTool  # noqa: E402
import tools.input_api_probe_tool as input_probe  # noqa: E402


def test_input_api_probe_lists_empty_authorized_targets_by_default(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(input_probe, "AUTHORIZED_TARGETS_FILE", tmp_path / "missing.json")

    result = InputApiProbeTool().execute(operation="list_authorized")

    assert result.is_success
    assert result.data["authorized_targets"] == []
    assert result.data["lab_only"] is True


def test_input_api_probe_spec_is_safe_without_authorization(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(input_probe, "AUTHORIZED_TARGETS_FILE", tmp_path / "missing.json")

    result = InputApiProbeTool().execute(
        operation="spec",
        target_process="game_input_sandbox.exe",
        api_name="RegisterRawInputDevices",
    )

    assert result.is_success
    assert result.data["authorized"] is False
    assert result.data["spec"]["policy"]["no_raw_key_storage"] is True
    assert result.data["spec"]["policy"]["no_character_decoding"] is True


def test_input_api_probe_execute_blocks_unauthorized(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(input_probe, "AUTHORIZED_TARGETS_FILE", tmp_path / "missing.json")

    result = InputApiProbeTool().execute(
        operation="execute",
        target_process="game_input_sandbox.exe",
        api_name="RegisterRawInputDevices",
        confirm=True,
    )

    assert result.status == ToolStatus.BLOCKED
    assert "not authorized" in result.error


def test_input_api_probe_execute_requires_confirm_for_authorized(tmp_path: Path, monkeypatch) -> None:
    config = tmp_path / "targets.json"
    config.write_text('{"authorized_targets": ["game_input_sandbox.exe"]}', encoding="utf-8")
    monkeypatch.setattr(input_probe, "AUTHORIZED_TARGETS_FILE", config)

    result = InputApiProbeTool().execute(
        operation="execute",
        target_process="game_input_sandbox.exe",
        api_name="RegisterRawInputDevices",
        confirm=False,
    )

    assert result.status == ToolStatus.REQUIRES_CONFIRMATION


def test_input_api_probe_execute_returns_aggregate_only_for_authorized(tmp_path: Path, monkeypatch) -> None:
    config = tmp_path / "targets.json"
    config.write_text('{"authorized_targets": ["game_input_sandbox.exe"]}', encoding="utf-8")
    monkeypatch.setattr(input_probe, "AUTHORIZED_TARGETS_FILE", config)

    def fake_run(self, target, spec, duration):
        return ToolResult(
            status=ToolStatus.SUCCESS,
            data={
                "schema": "ana.input_api_probe.result.v1",
                "target_process": target,
                "api": spec["api"],
                "summary": {
                    "calls_total": 3,
                    "unique_codes_count": 2,
                    "top_codes": [{"vk_code": 1, "count": 2}],
                },
                "policy": spec["policy"],
            },
        )

    monkeypatch.setattr(InputApiProbeTool, "_run_frida_probe", fake_run)

    result = InputApiProbeTool().execute(
        operation="execute",
        target_process="game_input_sandbox.exe",
        api_name="GetAsyncKeyState",
        confirm=True,
    )

    assert result.is_success
    summary = result.data["summary"]
    assert summary == {
        "calls_total": 3,
        "unique_codes_count": 2,
        "top_codes": [{"vk_code": 1, "count": 2}],
    }
    assert set(summary) == {"calls_total", "unique_codes_count", "top_codes"}
