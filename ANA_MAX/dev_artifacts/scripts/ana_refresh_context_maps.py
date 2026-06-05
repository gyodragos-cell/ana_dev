"""Refresh ANA Code Map and Graph Map in the safe order."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[3]
ANA_ROOT = REPO_ROOT / "ANA_MAX"
DEFAULT_PROJECT = REPO_ROOT
DEFAULT_CODE_MAP_OUT = ANA_ROOT / "memory" / "code_map"
DEFAULT_GRAPH_OUT = ANA_ROOT / "memory" / "graph_map"

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import ana_code_map
import ana_graph_map
import ana_operator_status


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def context_maps_status_for_paths(code_map_out: Path, graph_out: Path) -> dict[str, Any]:
    active_source = ana_operator_status.latest_active_context_source()
    code = ana_operator_status.context_map_entry("code", code_map_out / "index.json", active_source)
    graph_required_mtime = float(code.get("mtime") or 0) if code.get("status") == "PASS" else 0.0
    graph = ana_operator_status.context_map_entry(
        "graph",
        graph_out / "graph.json",
        active_source,
        graph_required_mtime,
        "code_map",
    )
    if graph.get("status") == "PASS" and code.get("status") not in ("PASS",):
        graph["status"] = "STALE"
        graph["stale_source"] = f"code_map_{str(code.get('status') or 'unknown').lower()}"
    statuses = [code.get("status"), graph.get("status")]
    return {
        "schema": "ana.context_maps_status.v1",
        "status": "PASS" if statuses == ["PASS", "PASS"] else "WARN",
        "active_source": active_source,
        "code_map": code,
        "graph_map": graph,
    }


def refresh_context_maps(
    project: Path = DEFAULT_PROJECT,
    code_map_out: Path = DEFAULT_CODE_MAP_OUT,
    graph_out: Path = DEFAULT_GRAPH_OUT,
    force: bool = True,
) -> dict[str, Any]:
    started = time.time()
    code_payload = ana_code_map.refresh(project.resolve(), code_map_out.resolve(), force=force)
    graph = ana_graph_map.build_graph(code_map_out.resolve(), graph_out.resolve())
    graph_payload = {
        "success": True,
        "schema": graph.get("schema", "ana.graph_map.v1"),
        "graph_out": str(graph_out.resolve()),
        "stats": graph.get("stats", ana_graph_map.graph_stats(graph)),
        "updated_at": graph.get("updated_at"),
        "code_map_updated_at": graph.get("code_map_updated_at"),
    }
    context_maps = context_maps_status_for_paths(code_map_out.resolve(), graph_out.resolve())
    success = bool(code_payload.get("success")) and context_maps.get("status") == "PASS"
    return {
        "success": success,
        "schema": "ana.refresh_context_maps.v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "elapsed_sec": round(time.time() - started, 3),
        "mode": "force" if force else "incremental",
        "project": str(project.resolve()),
        "code_map": {
            "success": code_payload.get("success"),
            "summaries": code_payload.get("summaries"),
            "updated": code_payload.get("updated"),
            "skipped": code_payload.get("skipped"),
            "ignored_non_logic": code_payload.get("ignored_non_logic"),
            "out_dir": code_payload.get("out_dir"),
        },
        "graph_map": {
            "success": graph_payload.get("success"),
            "nodes": (graph_payload.get("stats") or {}).get("nodes"),
            "edges": (graph_payload.get("stats") or {}).get("edges"),
            "graph_out": graph_payload.get("graph_out"),
            "updated_at": graph_payload.get("updated_at"),
            "code_map_updated_at": graph_payload.get("code_map_updated_at"),
        },
        "context_maps": context_maps,
        "message": ana_operator_status.format_context_maps(context_maps),
        "next_action": (
            "Rerun Operator Status or Nucleus Smoke; context maps are fresh."
            if success
            else "Review context_maps stale source, refresh again after active edits settle."
        ),
    }


def print_human(report: dict[str, Any]) -> None:
    code = report.get("code_map") if isinstance(report, dict) else {}
    graph = report.get("graph_map") if isinstance(report, dict) else {}
    code = code if isinstance(code, dict) else {}
    graph = graph if isinstance(graph, dict) else {}
    status = "PASS" if report.get("success") else "WARN"
    print(
        "ANA Context Maps Refresh: "
        f"{status} "
        f"mode={report.get('mode')} "
        f"code={code.get('summaries')} "
        f"graph={graph.get('nodes')}n/{graph.get('edges')}e "
        f"maps={report.get('message')} "
        f"elapsed={report.get('elapsed_sec')}s"
    )
    print(f"next_action={report.get('next_action')}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Refresh ANA Code Map and Graph Map in order.")
    parser.add_argument("--project", default=str(DEFAULT_PROJECT))
    parser.add_argument("--code-map-out", default=str(DEFAULT_CODE_MAP_OUT))
    parser.add_argument("--graph-out", default=str(DEFAULT_GRAPH_OUT))
    parser.add_argument("--incremental", action="store_true", help="Skip unchanged files in Code Map.")
    parser.add_argument("--json", action="store_true", help="Print JSON only.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = refresh_context_maps(
        project=Path(args.project),
        code_map_out=Path(args.code_map_out),
        graph_out=Path(args.graph_out),
        force=not args.incremental,
    )
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_human(report)
    return 0 if report.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
