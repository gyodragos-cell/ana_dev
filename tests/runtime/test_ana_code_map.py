from __future__ import annotations

import importlib.util
import struct
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "ana_code_map.py"


def load_module():
    spec = importlib.util.spec_from_file_location("ana_code_map", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_code_map_refresh_filters_noise_and_queries_symbols(tmp_path: Path):
    module = load_module()
    project = tmp_path / "project"
    out_dir = tmp_path / "memory" / "code_map"
    project.mkdir()
    (project / "src").mkdir()
    (project / "src" / "calculator.py").write_text(
        '"""Calculator scoring logic."""\n'
        "import math\n\n"
        "class Scorer:\n"
        "    def calculate_score(self, level, bonus):\n"
        "        return level * 100 + bonus\n\n"
        "def helper():\n"
        "    return math.pi\n",
        encoding="utf-8",
    )
    (project / "logs").mkdir()
    (project / "logs" / "noise.py").write_text("def noisy(): pass\n", encoding="utf-8")

    stats = module.refresh(project, out_dir, force=True)
    result = module.query(out_dir, "calculate score scorer", limit=5)

    assert stats["summaries"] == 1
    assert stats["ignored_non_logic"] == 0
    assert result["results_count"] == 1
    assert result["results"][0]["file"] == "src/calculator.py"
    assert "Scorer" in result["results"][0]["symbols"]


def test_code_map_refresh_skips_unchanged_files_incrementally(tmp_path: Path):
    module = load_module()
    project = tmp_path / "project"
    out_dir = tmp_path / "memory" / "code_map"
    project.mkdir()
    (project / "src").mkdir()
    source = project / "src" / "router.py"
    source.write_text(
        "def choose_tool(task):\n"
        "    return 'code_context_pack'\n",
        encoding="utf-8",
    )

    first = module.refresh(project, out_dir, force=True)
    second = module.refresh(project, out_dir, force=False)

    assert first["updated"] == 1
    assert first["skipped"] == 0
    assert second["updated"] == 0
    assert second["skipped"] == 1
    assert second["summaries"] == 1


def test_code_map_includes_small_static_binaries(tmp_path: Path):
    module = load_module()
    project = tmp_path / "project"
    out_dir = tmp_path / "memory" / "code_map"
    project.mkdir()
    binary = project / "bin" / "tool.exe"
    binary.parent.mkdir()
    binary.write_bytes(_minimal_pe())

    stats = module.refresh(project, out_dir, force=True)
    result = module.query(out_dir, "tool exe kernel32 binary", limit=5)

    assert stats["summaries"] == 1
    assert result["results_count"] == 1
    assert result["results"][0]["file"] == "bin/tool.exe"
    assert "KERNEL32.dll" in result["results"][0]["dependencies"]


def test_code_map_query_demotes_generated_memory_for_general_lab_queries(tmp_path: Path):
    module = load_module()
    project = tmp_path / "project"
    out_dir = tmp_path / "memory" / "code_map"
    project.mkdir()
    script = project / "ANA_MAX" / "dev_artifacts" / "scripts" / "ana_autonomy_runner.py"
    script.parent.mkdir(parents=True)
    script.write_text(
        '"""Run lab-safe autonomy readiness pass for the next scoped action."""\n'
        "def choose_next_scoped_lab_action():\n"
        "    return 'continue with verified baseline'\n",
        encoding="utf-8",
    )
    checkpoint = project / "ANA_MAX" / "docs" / "SESSION_CHECKPOINT_2026-06-01T000000Z0000.md"
    checkpoint.parent.mkdir(parents=True)
    checkpoint.write_text(
        "# Session Checkpoint\n\n"
        "## Next scoped lab action after green baseline\n\n"
        "This generated checkpoint repeats next scoped lab action after green baseline "
        "so it should not outrank active scripts for ordinary project-state queries.\n",
        encoding="utf-8",
    )

    module.refresh(project, out_dir, force=True)
    result = module.query(out_dir, "next scoped lab action after green baseline", limit=2)

    assert result["results"][0]["file"] == "ANA_MAX/dev_artifacts/scripts/ana_autonomy_runner.py"
    assert result["results"][1]["file"].startswith("ANA_MAX/docs/SESSION_CHECKPOINT_")
    assert result["results"][1]["rank_penalty"] > 0


def test_code_map_query_keeps_generated_memory_when_requested(tmp_path: Path):
    module = load_module()
    project = tmp_path / "project"
    out_dir = tmp_path / "memory" / "code_map"
    project.mkdir()
    checkpoint = project / "ANA_MAX" / "docs" / "SESSION_CHECKPOINT_2026-06-01T000000Z0000.md"
    checkpoint.parent.mkdir(parents=True)
    checkpoint.write_text(
        "# Session Checkpoint\n\n"
        "## Baseline checkpoint handoff\n\n"
        "This generated checkpoint is intentionally queried by session checkpoint terms.\n",
        encoding="utf-8",
    )

    module.refresh(project, out_dir, force=True)
    result = module.query(out_dir, "session checkpoint baseline", limit=1)

    assert result["results"][0]["file"] == "ANA_MAX/docs/SESSION_CHECKPOINT_2026-06-01T000000Z0000.md"
    assert result["results"][0]["rank_penalty"] == 0


def _minimal_pe() -> bytes:
    data = bytearray(0x800)
    data[0:2] = b"MZ"
    struct.pack_into("<I", data, 0x3C, 0x80)
    pe = 0x80
    data[pe:pe + 4] = b"PE\x00\x00"
    struct.pack_into("<H", data, pe + 4, 0x8664)
    struct.pack_into("<H", data, pe + 6, 1)
    struct.pack_into("<H", data, pe + 20, 0xF0)
    opt = pe + 24
    struct.pack_into("<H", data, opt, 0x20B)
    struct.pack_into("<I", data, opt + 16, 0x1000)
    struct.pack_into("<Q", data, opt + 24, 0x140000000)
    struct.pack_into("<I", data, opt + 112 + 8, 0x1100)
    sec = opt + 0xF0
    data[sec:sec + 8] = b".text\x00\x00\x00"
    struct.pack_into("<I", data, sec + 8, 0x1000)
    struct.pack_into("<I", data, sec + 12, 0x1000)
    struct.pack_into("<I", data, sec + 16, 0x400)
    struct.pack_into("<I", data, sec + 20, 0x200)
    struct.pack_into("<I", data, 0x300 + 12, 0x1128)
    data[0x328:0x328 + len(b"KERNEL32.dll\x00")] = b"KERNEL32.dll\x00"
    return bytes(data)
