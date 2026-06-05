from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path


ANA_MAX_DIR = Path(__file__).resolve().parents[2] / "ANA_MAX"
if str(ANA_MAX_DIR) not in sys.path:
    sys.path.insert(0, str(ANA_MAX_DIR))

from tools.graph_context_pack_tool import GraphContextPackTool  # noqa: E402
import tools.graph_context_pack_tool as graph_tool  # noqa: E402


SCRIPT = ANA_MAX_DIR / "dev_artifacts" / "scripts" / "ana_code_map.py"


def load_code_map():
    spec = importlib.util.spec_from_file_location("ana_code_map_for_graph_tool_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_graph_context_pack_refresh_and_query(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "project"
    code_out = tmp_path / "code_map"
    graph_out = tmp_path / "graph_map"
    project.mkdir()
    (project / "router.py").write_text(
        '"""Router logic."""\n'
        "import json\n"
        "class ToolRouter:\n"
        "    def recommend(self):\n"
        "        return json.dumps({'tool': 'code_context_pack'})\n",
        encoding="utf-8",
    )
    load_code_map().refresh(project, code_out, force=True)

    monkeypatch.setattr(graph_tool, "REPO_ROOT", project)
    monkeypatch.setattr(graph_tool, "CODE_MAP_OUT", code_out)
    monkeypatch.setattr(graph_tool, "GRAPH_OUT", graph_out)

    refresh = GraphContextPackTool().execute(action="refresh")
    assert refresh.is_success
    assert refresh.data["stats"]["node_kinds"]["file"] == 1

    query = GraphContextPackTool().execute(action="query", query="ToolRouter", limit=5)
    assert query.is_success
    assert query.data["results_count"] >= 1
    assert any(item["name"] == "ToolRouter" or "router.py" in item["id"] for item in query.data["results"])


def test_graph_context_pack_refreshes_stale_graph_after_code_map_changes(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "project"
    code_out = tmp_path / "code_map"
    graph_out = tmp_path / "graph_map"
    project.mkdir()
    source = project / "router.py"
    source.write_text(
        "class ToolRouter:\n"
        "    pass\n",
        encoding="utf-8",
    )
    code_map = load_code_map()
    code_map.refresh(project, code_out, force=True)

    monkeypatch.setattr(graph_tool, "REPO_ROOT", project)
    monkeypatch.setattr(graph_tool, "CODE_MAP_OUT", code_out)
    monkeypatch.setattr(graph_tool, "GRAPH_OUT", graph_out)

    refresh = GraphContextPackTool().execute(action="refresh")
    assert refresh.is_success

    source.write_text(
        "class ToolRouter:\n"
        "    pass\n\n"
        "class FreshGraphSignal:\n"
        "    pass\n",
        encoding="utf-8",
    )
    time.sleep(0.02)
    code_map.refresh(project, code_out, force=True)

    query = GraphContextPackTool().execute(action="query", query="FreshGraphSignal", limit=5)

    assert query.is_success
    assert any(item["name"] == "FreshGraphSignal" for item in query.data["results"])
