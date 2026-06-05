"""Tests for the Code Map + Graph Map refresh helper."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "ana_refresh_context_maps.py"


def load_script():
    script_dir = str(SCRIPT.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location("ana_refresh_context_maps", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_refresh_context_maps_refreshes_code_then_graph_then_verifies(monkeypatch, tmp_path):
    script = load_script()
    calls: list[str] = []
    project = tmp_path / "project"
    code_out = tmp_path / "code_map"
    graph_out = tmp_path / "graph_map"
    project.mkdir()

    def fake_code_refresh(project_path, out_dir, force=True):
        calls.append(f"code:{force}")
        assert project_path == project.resolve()
        assert out_dir == code_out.resolve()
        return {
            "success": True,
            "summaries": 12,
            "updated": 12,
            "skipped": 0,
            "ignored_non_logic": 2,
            "out_dir": str(out_dir),
        }

    def fake_build_graph(code_map_out, graph_map_out):
        calls.append("graph")
        assert code_map_out == code_out.resolve()
        assert graph_map_out == graph_out.resolve()
        return {
            "schema": "ana.graph_map.v1",
            "updated_at": "2026-06-01T00:00:01Z",
            "code_map_updated_at": "2026-06-01T00:00:00Z",
            "stats": {"nodes": 20, "edges": 30},
        }

    def fake_context_status(code_map_path, graph_path):
        calls.append("status")
        assert code_map_path == code_out.resolve()
        assert graph_path == graph_out.resolve()
        return {
            "status": "PASS",
            "code_map": {"status": "PASS", "summaries": 12},
            "graph_map": {"status": "PASS", "nodes": 20, "edges": 30},
        }

    monkeypatch.setattr(script.ana_code_map, "refresh", fake_code_refresh)
    monkeypatch.setattr(script.ana_graph_map, "build_graph", fake_build_graph)
    monkeypatch.setattr(script, "context_maps_status_for_paths", fake_context_status)

    report = script.refresh_context_maps(project, code_out, graph_out, force=True)

    assert calls == ["code:True", "graph", "status"]
    assert report["success"] is True
    assert report["mode"] == "force"
    assert report["code_map"]["summaries"] == 12
    assert report["graph_map"]["nodes"] == 20
    assert report["message"] == "code:PASS(12) graph:PASS(20n/30e)"


def test_refresh_context_maps_warns_when_final_status_is_stale(monkeypatch, tmp_path):
    script = load_script()
    project = tmp_path / "project"
    project.mkdir()

    monkeypatch.setattr(script.ana_code_map, "refresh", lambda project_path, out_dir, force=True: {
        "success": True,
        "summaries": 12,
        "updated": 1,
        "skipped": 11,
        "ignored_non_logic": 2,
        "out_dir": str(out_dir),
    })
    monkeypatch.setattr(script.ana_graph_map, "build_graph", lambda code_map_out, graph_out: {
        "schema": "ana.graph_map.v1",
        "stats": {"nodes": 20, "edges": 30},
    })
    monkeypatch.setattr(script, "context_maps_status_for_paths", lambda code_map_out, graph_out: {
        "status": "WARN",
        "code_map": {"status": "STALE", "summaries": 12, "stale_source": "ANA_MAX/tools/example.py"},
        "graph_map": {"status": "PASS", "nodes": 20, "edges": 30},
    })

    report = script.refresh_context_maps(project, tmp_path / "code", tmp_path / "graph", force=False)

    assert report["success"] is False
    assert report["mode"] == "incremental"
    assert report["next_action"].startswith("Review context_maps stale source")


def test_print_human_includes_compact_counts(capsys):
    script = load_script()

    script.print_human({
        "success": True,
        "mode": "force",
        "code_map": {"summaries": 12},
        "graph_map": {"nodes": 20, "edges": 30},
        "message": "code:PASS(12) graph:PASS(20n/30e)",
        "elapsed_sec": 1.23,
        "next_action": "Done.",
    })

    output = capsys.readouterr().out
    assert "ANA Context Maps Refresh: PASS" in output
    assert "code=12" in output
    assert "graph=20n/30e" in output
    assert "next_action=Done." in output
