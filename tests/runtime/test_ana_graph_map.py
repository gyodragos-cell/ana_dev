from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "ana_graph_map.py"
CODE_SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "ana_code_map.py"


def load_script(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_graph_map_builds_queryable_graph_from_code_map(tmp_path: Path) -> None:
    project = tmp_path / "project"
    code_out = tmp_path / "code_map"
    graph_out = tmp_path / "graph_map"
    project.mkdir()
    (project / "alpha.py").write_text(
        '"""Alpha orchestration."""\n'
        "import json\n"
        "from beta import BetaTool\n"
        "class AlphaTool:\n"
        "    def execute(self):\n"
        "        return BetaTool()\n",
        encoding="utf-8",
    )
    (project / "beta.py").write_text(
        '"""Beta helper."""\n'
        "class BetaTool:\n"
        "    pass\n",
        encoding="utf-8",
    )

    code_map = load_script(CODE_SCRIPT, "ana_code_map_for_graph_test")
    graph_map = load_script(SCRIPT, "ana_graph_map_test")
    code_map.refresh(project, code_out, force=True)
    graph = graph_map.build_graph(code_out, graph_out)

    assert graph["schema"] == "ana.graph_map.v1"
    assert graph["stats"]["node_kinds"]["file"] == 2
    assert graph["stats"]["relations"]["defines"] >= 2
    assert (graph_out / "graph.json").exists()
    assert (graph_out / "GRAPH_REPORT.md").exists()
    assert (graph_out / "graph.html").exists()

    query = graph_map.query_graph(graph_out, "AlphaTool beta", limit=3)
    assert query["results_count"] >= 1
    assert any("alpha.py" in item["id"] or item["name"] == "AlphaTool" for item in query["results"])

    path = graph_map.path_query(graph_out, "alpha.py", "BetaTool", max_depth=4)
    assert path["found"] is True

    blast = graph_map.blast_radius(graph_out, ["alpha.py"], limit=10)
    assert blast["schema"] == "ana.graph_blast_radius.v1"
    assert blast["affected_count"] >= 1
    assert blast["affected"][0]["name"] == "alpha.py"
    assert blast["affected"][0]["confidence"] == "EXACT"


def test_graph_map_stats_reads_refreshed_graph(tmp_path: Path) -> None:
    project = tmp_path / "project"
    code_out = tmp_path / "code_map"
    graph_out = tmp_path / "graph_map"
    project.mkdir()
    (project / "tool_router.py").write_text(
        "import json\n"
        "def recommend(task):\n"
        "    return {'tool': 'code_context_pack'}\n",
        encoding="utf-8",
    )

    code_map = load_script(CODE_SCRIPT, "ana_code_map_for_graph_stats_test")
    graph_map = load_script(SCRIPT, "ana_graph_map_stats_test")
    code_map.refresh(project, code_out, force=True)
    graph_map.build_graph(code_out, graph_out)
    stats = graph_map.stats(graph_out)

    assert stats["success"] is True
    assert stats["schema"] == "ana.graph_map.v1"
    assert stats["stats"]["nodes"] >= 3
    assert stats["stats"]["edges"] >= 2
    assert stats["stats"]["node_kinds"]["file"] == 1


def test_graph_map_blast_radius_finds_probable_tests(tmp_path: Path) -> None:
    project = tmp_path / "project"
    code_out = tmp_path / "code_map"
    graph_out = tmp_path / "graph_map"
    project.mkdir()
    (project / "payment.py").write_text(
        "def calculate_payment():\n"
        "    return 1\n",
        encoding="utf-8",
    )
    (project / "test_payment.py").write_text(
        "from payment import calculate_payment\n"
        "def test_calculate_payment():\n"
        "    assert calculate_payment() == 1\n",
        encoding="utf-8",
    )

    code_map = load_script(CODE_SCRIPT, "ana_code_map_for_graph_blast_test")
    graph_map = load_script(SCRIPT, "ana_graph_map_blast_test")
    code_map.refresh(project, code_out, force=True)
    graph_map.build_graph(code_out, graph_out)

    blast = graph_map.blast_radius(graph_out, "payment.py", limit=10)
    names = {item["name"] for item in blast["affected"]}

    assert "payment.py" in names
    assert "test_payment.py" in names
    test_item = next(item for item in blast["affected"] if item["name"] == "test_payment.py")
    assert test_item["score"] >= 80
    assert any("probable test" in reason for reason in test_item["reasons"])


def test_graph_map_blast_radius_downranks_archive_noise(tmp_path: Path) -> None:
    project = tmp_path / "project"
    code_out = tmp_path / "code_map"
    graph_out = tmp_path / "graph_map"
    archive = project / "ANA_MAX" / "archives" / "tests" / "standalone"
    real_tests = project / "tests" / "runtime"
    archive.mkdir(parents=True)
    real_tests.mkdir(parents=True)
    (project / "router.py").write_text(
        "import time\n"
        "def route():\n"
        "    return 'ok'\n",
        encoding="utf-8",
    )
    (archive / "old_router_demo.py").write_text("import time\nprint(time.time())\n", encoding="utf-8")
    (real_tests / "test_router.py").write_text(
        "from router import route\n"
        "def test_route():\n"
        "    assert route() == 'ok'\n",
        encoding="utf-8",
    )

    code_map = load_script(CODE_SCRIPT, "ana_code_map_for_graph_noise_test")
    graph_map = load_script(SCRIPT, "ana_graph_map_noise_test")
    code_map.refresh(project, code_out, force=True)
    graph_map.build_graph(code_out, graph_out)

    blast = graph_map.blast_radius(graph_out, "router.py", limit=10)
    by_name = {item["name"]: item for item in blast["affected"]}

    assert "tests/runtime/test_router.py" in by_name
    assert by_name["tests/runtime/test_router.py"]["score"] > by_name.get(
        "ANA_MAX/archives/tests/standalone/old_router_demo.py",
        {"score": 0},
    )["score"]


def test_graph_map_blast_radius_does_not_match_generic_basename(tmp_path: Path) -> None:
    project = tmp_path / "project"
    code_out = tmp_path / "code_map"
    graph_out = tmp_path / "graph_map"
    plugins = project / "ANA_MAX" / "plugins"
    tools = project / "ANA_MAX" / "tools"
    plugins.mkdir(parents=True)
    tools.mkdir(parents=True)
    (plugins / "__init__.py").write_text("class PluginBase:\n    pass\n", encoding="utf-8")
    # Deliberately do not create tools/__init__.py in the code map.

    code_map = load_script(CODE_SCRIPT, "ana_code_map_for_graph_generic_test")
    graph_map = load_script(SCRIPT, "ana_graph_map_generic_test")
    code_map.refresh(project, code_out, force=True)
    graph_map.build_graph(code_out, graph_out)

    blast = graph_map.blast_radius(graph_out, "ANA_MAX/tools/__init__.py", limit=10)

    assert blast["matched_changed"] == []
    assert not any(item["name"] == "ANA_MAX/plugins/__init__.py" for item in blast["affected"])


def test_graph_query_demotes_generated_memory_and_filters_low_signal_neighbors(tmp_path: Path) -> None:
    project = tmp_path / "project"
    code_out = tmp_path / "code_map"
    graph_out = tmp_path / "graph_map"
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
        "so graph queries should not treat it as active work.\n",
        encoding="utf-8",
    )
    archive = project / "ANA_MAX" / "archives" / "security_research" / "README.md"
    archive.parent.mkdir(parents=True)
    archive.write_text(
        "# Research Archive\n\n"
        "## Next scoped lab action after green baseline\n\n"
        "Archive note for old security research material, not the active workflow.\n",
        encoding="utf-8",
    )

    code_map = load_script(CODE_SCRIPT, "ana_code_map_for_graph_query_noise_test")
    graph_map = load_script(SCRIPT, "ana_graph_map_query_noise_test")
    code_map.refresh(project, code_out, force=True)
    graph_map.build_graph(code_out, graph_out)

    query = graph_map.query_graph(graph_out, "next scoped lab action after green baseline", limit=20)
    names = [item["name"] for item in query["results"]]
    active_index = names.index("ANA_MAX/dev_artifacts/scripts/ana_autonomy_runner.py")
    generated_indices = [
        index
        for index, name in enumerate(names)
        if "SESSION_CHECKPOINT_" in name or "/archives/" in name.replace("\\", "/")
    ]

    assert generated_indices
    assert all(active_index < index for index in generated_indices)
    assert all(
        item["rank_penalty"] > 0
        for item in query["results"]
        if "SESSION_CHECKPOINT_" in item["name"] or "/archives/" in item["name"].replace("\\", "/")
    )
    keyword_next = next(item for item in query["results"] if item["id"] == "keyword:next")
    assert keyword_next["hidden_low_signal_neighbors"] > 0
    assert not any("SESSION_CHECKPOINT_" in neighbor["name"] for neighbor in keyword_next["neighbors"])
    assert not any("/archives/" in neighbor["name"].replace("\\", "/") for neighbor in keyword_next["neighbors"])


def test_graph_query_keeps_generated_memory_when_requested(tmp_path: Path) -> None:
    project = tmp_path / "project"
    code_out = tmp_path / "code_map"
    graph_out = tmp_path / "graph_map"
    project.mkdir()
    checkpoint = project / "ANA_MAX" / "docs" / "SESSION_CHECKPOINT_2026-06-01T000000Z0000.md"
    checkpoint.parent.mkdir(parents=True)
    checkpoint.write_text(
        "# Session Checkpoint\n\n"
        "## Baseline checkpoint handoff\n\n"
        "This generated checkpoint is intentionally queried by session checkpoint terms.\n",
        encoding="utf-8",
    )

    code_map = load_script(CODE_SCRIPT, "ana_code_map_for_graph_checkpoint_query_test")
    graph_map = load_script(SCRIPT, "ana_graph_map_checkpoint_query_test")
    code_map.refresh(project, code_out, force=True)
    graph_map.build_graph(code_out, graph_out)

    query = graph_map.query_graph(graph_out, "session checkpoint baseline", limit=5)
    checkpoint_result = next(
        item
        for item in query["results"]
        if item["name"] == "ANA_MAX/docs/SESSION_CHECKPOINT_2026-06-01T000000Z0000.md"
    )

    assert checkpoint_result["rank_penalty"] == 0
