from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ANA_MAX_DIR = Path(__file__).resolve().parents[2] / "ANA_MAX"
if str(ANA_MAX_DIR) not in sys.path:
    sys.path.insert(0, str(ANA_MAX_DIR))

from tools.base import ToolResult, ToolStatus  # noqa: E402
from tools.code_context_pack_tool import CodeContextPackTool  # noqa: E402
import tools.code_context_pack_tool as context_pack  # noqa: E402


SCRIPT = ANA_MAX_DIR / "dev_artifacts" / "scripts" / "ana_code_map.py"


def load_code_map():
    spec = importlib.util.spec_from_file_location("ana_code_map_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_code_context_pack_links_ui_snapshot_to_code_map(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "project"
    out_dir = tmp_path / "code_map"
    project.mkdir()
    (project / "tools").mkdir()
    (project / "tools" / "foreground_ui_snapshot.py").write_text(
        '"""Foreground UI snapshot logic."""\n'
        "class ForegroundUISnapshotTool:\n"
        "    def execute(self):\n"
        "        return {'active_app': 'Code'}\n",
        encoding="utf-8",
    )
    load_code_map().refresh(project, out_dir, force=True)

    def fake_snapshot_execute(self, **kwargs):
        return ToolResult(
            status=ToolStatus.SUCCESS,
            data={
                "active_app": "Code",
                "title": "foreground_ui_snapshot.py - ana_dev - Visual Studio Code",
                "visible_text": ["class ForegroundUISnapshotTool"],
                "detected_errors": [],
                "suggested_actions": [],
            },
        )

    monkeypatch.setattr(context_pack, "REPO_ROOT", project)
    monkeypatch.setattr(context_pack, "CODE_MAP_OUT", out_dir)
    monkeypatch.setattr(context_pack, "GRAPH_MAP_OUT", tmp_path / "graph_map")
    monkeypatch.setattr(context_pack.ForegroundUISnapshotTool, "execute", fake_snapshot_execute)

    result = CodeContextPackTool().execute(task="why is foreground snapshot failing", limit=3)

    assert result.is_success
    assert result.data["schema"] == "ana.code_context_pack.v1"
    assert result.data["snapshot"]["title"].startswith("foreground_ui_snapshot.py")
    assert result.data["code_map"]["results"][0]["file"] == "tools/foreground_ui_snapshot.py"
    assert result.data["graph_map"]["results"]
    assert "ana_graph_map" in result.data["compressed_state"]["evidence"]
    assert result.data["compressed_state"]["current_file_candidates"] == ["tools/foreground_ui_snapshot.py"]


def test_code_context_pack_accepts_query_alias(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "project"
    out_dir = tmp_path / "code_map"
    project.mkdir()
    (project / "ana_operator_status.py").write_text(
        '"""Print compact operator status."""\n'
        "def build_operator_status():\n"
        "    return 'reload behavior status'\n",
        encoding="utf-8",
    )
    load_code_map().refresh(project, out_dir, force=True)

    def fake_snapshot_execute(self, **kwargs):
        return ToolResult(
            status=ToolStatus.SUCCESS,
            data={
                "active_app": "Code",
                "title": "Untitled - Visual Studio Code",
                "visible_text": ["unrelated visible text"],
                "detected_errors": [],
                "suggested_actions": [],
            },
        )

    monkeypatch.setattr(context_pack, "REPO_ROOT", project)
    monkeypatch.setattr(context_pack, "CODE_MAP_OUT", out_dir)
    monkeypatch.setattr(context_pack, "GRAPH_MAP_OUT", tmp_path / "graph_map")
    monkeypatch.setattr(context_pack.ForegroundUISnapshotTool, "execute", fake_snapshot_execute)

    result = CodeContextPackTool().execute(query="operator status reload behavior", limit=3)

    assert result.is_success
    assert result.data["compressed_state"]["goal"] == "operator status reload behavior"
    assert result.data["code_map"]["results"][0]["file"] == "ana_operator_status.py"


def test_code_context_pack_include_text_false_keeps_query_precise() -> None:
    query = context_pack._candidate_terms(
        {
            "active_app": "Code",
            "title": "SESSION_CHECKPOINT_2026-05-31T202156Z0000.md",
            "visible_text": ["error_radar_summary Layout"],
        },
        "operator status reload behavior",
        include_snapshot_terms=False,
    )

    assert query == "operator status reload behavior"


def test_code_context_pack_prefers_graph_ranked_file() -> None:
    results = [
        {"file": "vscode_extension/CHANGELOG.md", "score": 4},
        {"file": "ANA_MAX/dev_artifacts/scripts/ana_operator_status.py", "score": 3},
    ]
    graph_query = {
        "results": [
            {
                "kind": "file",
                "name": "ANA_MAX/dev_artifacts/scripts/ana_operator_status.py",
            }
        ]
    }

    ranked = context_pack._prefer_graph_files(results, graph_query)

    assert ranked[0]["file"] == "ANA_MAX/dev_artifacts/scripts/ana_operator_status.py"


def test_code_context_pack_expands_code_map_query_when_graph_enabled(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "project"
    out_dir = tmp_path / "code_map"
    project.mkdir()

    def fake_snapshot_execute(self, **kwargs):
        return ToolResult(status=ToolStatus.SUCCESS, data={})

    class FakeCodeMap:
        def __init__(self) -> None:
            self.seen_limit = None

        def stats(self, out):
            return {"summaries": 3, "updated_at": "now"}

        def query(self, out, query_text, limit=5):
            self.seen_limit = limit
            return {
                "results": [
                    {"file": "vscode_extension/CHANGELOG.md"},
                    {"file": "ANA_MAX/dev_artifacts/scripts/ana_operator_status.py"},
                    {"file": "docs/NEXT_SESSION_BOOTSTRAP.md"},
                ][:limit]
            }

    fake_code_map = FakeCodeMap()
    monkeypatch.setattr(context_pack, "REPO_ROOT", project)
    monkeypatch.setattr(context_pack, "CODE_MAP_OUT", out_dir)
    monkeypatch.setattr(context_pack, "_load_code_map_module", lambda: fake_code_map)
    monkeypatch.setattr(context_pack.CodeContextPackTool, "_graph_query", lambda self, query_text, limit: {
        "results": [
            {"kind": "file", "name": "ANA_MAX/dev_artifacts/scripts/ana_operator_status.py"}
        ]
    })
    monkeypatch.setattr(context_pack.ForegroundUISnapshotTool, "execute", fake_snapshot_execute)

    result = CodeContextPackTool().execute(query="operator status reload behavior", limit=1, include_graph=True, include_text=False)

    assert result.is_success
    assert fake_code_map.seen_limit == 3
    assert result.data["code_map"]["results"][0]["file"] == "ANA_MAX/dev_artifacts/scripts/ana_operator_status.py"
    assert len(result.data["code_map"]["results"]) == 1
