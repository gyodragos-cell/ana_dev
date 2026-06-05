"""Tests for local source checkpoint helper."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "ana_local_checkpoint.py"


def load_script():
    spec = importlib.util.spec_from_file_location("ana_local_checkpoint", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parser_requires_title_and_summary():
    script = load_script()
    parser = script.build_parser()

    args = parser.parse_args(["--title", "T", "--summary", "S", "--no-include-git"])

    assert args.title == "T"
    assert args.summary == "S"
    assert args.include_git is False
    assert args.refresh_memory_archive is True


def test_parser_can_disable_memory_archive_refresh():
    script = load_script()
    parser = script.build_parser()

    args = parser.parse_args(["--title", "T", "--summary", "S", "--no-refresh-memory-archive"])

    assert args.refresh_memory_archive is False


def test_result_to_dict_normalizes_tool_result_shape():
    script = load_script()

    class FakeResult:
        is_success = True
        data = {"path": "x"}
        message = "ok"
        error = None

    payload = script.result_to_dict(FakeResult())

    assert payload == {"success": True, "data": {"path": "x"}, "message": "ok", "error": None}
