"""ANA MAX graph map builder.

Builds a local knowledge graph from the deterministic code map:
- file nodes from ANA_MAX/memory/code_map/index.json
- symbol nodes for functions/classes/headings
- dependency nodes for imports/dependencies
- confidence-labelled edges inspired by Graphify's useful parts

This is lab-native and read-only with respect to source files. It does not
execute project code and does not require external graph dependencies.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
from collections import Counter, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


REPO_ROOT = Path(__file__).resolve().parents[3]
ANA_ROOT = REPO_ROOT / "ANA_MAX"
CODE_MAP_OUT = ANA_ROOT / "memory" / "code_map"
GRAPH_OUT = ANA_ROOT / "memory" / "graph_map"
GRAPH_JSON = "graph.json"
GRAPH_REPORT = "GRAPH_REPORT.md"
GRAPH_HTML = "graph.html"
COMMON_CONTEXT_NAMES = {
    "__future__",
    "argparse",
    "collections",
    "dataclasses",
    "datetime",
    "execute",
    "get_definition",
    "hashlib",
    "html",
    "importlib.util",
    "json",
    "logging",
    "os",
    "pathlib",
    "re",
    "sys",
    "time",
    "typing",
    "tools.base",
}
COMMON_TEST_TOKENS = {"ana", "max", "py", "test", "tests", "tool", "tools", "runtime"}
GENERIC_FILE_NAMES = {"__init__.py", "index.js", "index.ts", "main.py"}
CHECKPOINT_TERMS = {"checkpoint", "checkpoints", "session", "handoff"}
REM_TERMS = {"rem", "sleep", "retrospective", "memory"}
ARCHIVE_TERMS = {
    "archive",
    "archives",
    "security",
    "research",
    "charles",
    "frida",
    "apk",
    "mobile",
    "game",
    "mitm",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_code_index(code_map_out: Path) -> dict[str, Any]:
    path = code_map_out / "index.json"
    if not path.exists():
        return {"schema": "ana.code_map.v1", "files": {}, "updated_at": None}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"schema": "ana.code_map.v1", "files": {}, "updated_at": None}


def node_id(kind: str, name: str) -> str:
    safe = re.sub(r"\s+", " ", str(name or "").strip())
    return f"{kind}:{safe}"


def add_node(nodes: dict[str, dict[str, Any]], kind: str, name: str, **attrs: Any) -> str:
    ident = node_id(kind, name)
    current = nodes.setdefault(ident, {"id": ident, "kind": kind, "name": name})
    for key, value in attrs.items():
        if value in (None, "", []):
            continue
        current[key] = value
    return ident


def add_edge(edges: list[dict[str, Any]], source: str, target: str, relation: str, confidence: str, **attrs: Any) -> None:
    if source == target:
        return
    edge = {
        "source": source,
        "target": target,
        "relation": relation,
        "confidence": confidence,
    }
    edge.update({key: value for key, value in attrs.items() if value not in (None, "", [])})
    edges.append(edge)


def normalize_dep(dep: str) -> str:
    dep = str(dep or "").strip()
    if not dep:
        return ""
    return dep.replace("\\", "/")


def build_graph(code_map_out: Path, graph_out: Path) -> dict[str, Any]:
    started = time.time()
    index = load_code_index(code_map_out)
    files: dict[str, Any] = index.get("files", {})
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []

    for rel, item in sorted(files.items()):
        file_node = add_node(
            nodes,
            "file",
            rel,
            language=item.get("language"),
            purpose=item.get("purpose"),
            summary_file=item.get("summary_file"),
            size=item.get("size"),
        )
        for symbol in (item.get("symbols") or [])[:60]:
            symbol_node = add_node(nodes, "symbol", symbol)
            add_edge(edges, file_node, symbol_node, "defines", "EXTRACTED")

        for dep in (item.get("dependencies") or item.get("imports") or [])[:80]:
            dep_name = normalize_dep(dep)
            if not dep_name:
                continue
            dep_node = add_node(nodes, "dependency", dep_name)
            add_edge(edges, file_node, dep_node, "imports", "EXTRACTED")

        for keyword in (item.get("keywords") or [])[:24]:
            keyword_node = add_node(nodes, "keyword", keyword)
            add_edge(edges, file_node, keyword_node, "mentions", "INFERRED")

    graph = {
        "schema": "ana.graph_map.v1",
        "source": "ana_code_map",
        "updated_at": now_iso(),
        "code_map_updated_at": index.get("updated_at"),
        "code_map_out": str(code_map_out),
        "graph_out": str(graph_out),
        "nodes": list(nodes.values()),
        "edges": dedupe_edges(edges),
        "stats": {},
    }
    graph["stats"] = graph_stats(graph)
    graph["stats"]["elapsed_sec"] = round(time.time() - started, 3)
    graph_out.mkdir(parents=True, exist_ok=True)
    write_graph_outputs(graph, graph_out)
    return graph


def dedupe_edges(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    result = []
    for edge in edges:
        key = (edge["source"], edge["target"], edge["relation"], edge["confidence"])
        if key in seen:
            continue
        seen.add(key)
        result.append(edge)
    return result


def graph_stats(graph: dict[str, Any]) -> dict[str, Any]:
    node_kinds = Counter(node.get("kind") for node in graph.get("nodes", []))
    relations = Counter(edge.get("relation") for edge in graph.get("edges", []))
    degree: Counter[str] = Counter()
    for edge in graph.get("edges", []):
        degree[edge["source"]] += 1
        degree[edge["target"]] += 1
    node_lookup = {node["id"]: node for node in graph.get("nodes", [])}
    hubs = []
    for ident, count in degree.most_common(12):
        node = node_lookup.get(ident, {"id": ident, "name": ident, "kind": "unknown"})
        hubs.append({"id": ident, "name": node.get("name"), "kind": node.get("kind"), "degree": count})
    return {
        "nodes": len(graph.get("nodes", [])),
        "edges": len(graph.get("edges", [])),
        "node_kinds": dict(sorted(node_kinds.items())),
        "relations": dict(sorted(relations.items())),
        "top_hubs": hubs,
    }


def write_graph_outputs(graph: dict[str, Any], graph_out: Path) -> None:
    (graph_out / GRAPH_JSON).write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")
    (graph_out / GRAPH_REPORT).write_text(render_report(graph), encoding="utf-8")
    (graph_out / GRAPH_HTML).write_text(render_html(graph), encoding="utf-8")


def render_report(graph: dict[str, Any]) -> str:
    stats = graph.get("stats", {})
    lines = [
        "# ANA Graph Map Report",
        "",
        f"- schema: `{graph.get('schema')}`",
        f"- source: `{graph.get('source')}`",
        f"- updated_at: `{graph.get('updated_at')}`",
        f"- code_map_updated_at: `{graph.get('code_map_updated_at')}`",
        f"- nodes: `{stats.get('nodes', 0)}`",
        f"- edges: `{stats.get('edges', 0)}`",
        "",
        "## Node Kinds",
        "",
    ]
    for kind, count in (stats.get("node_kinds") or {}).items():
        lines.append(f"- `{kind}`: {count}")
    lines.extend(["", "## Relations", ""])
    for relation, count in (stats.get("relations") or {}).items():
        lines.append(f"- `{relation}`: {count}")
    lines.extend(["", "## Top Hubs", ""])
    for hub in stats.get("top_hubs") or []:
        lines.append(f"- `{hub.get('kind')}` `{hub.get('name')}` degree={hub.get('degree')}")
    return "\n".join(lines) + "\n"


def render_html(graph: dict[str, Any]) -> str:
    stats = graph.get("stats", {})
    hubs = stats.get("top_hubs") or []
    hub_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(str(hub.get('kind')))}</td>"
        f"<td>{html.escape(str(hub.get('name')))}</td>"
        f"<td>{html.escape(str(hub.get('degree')))}</td>"
        "</tr>"
        for hub in hubs
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ANA Graph Map</title>
  <style>
    body {{ margin: 0; font-family: Segoe UI, Arial, sans-serif; background: #101820; color: #e8eef2; }}
    main {{ max-width: 1100px; margin: 0 auto; padding: 28px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }}
    .card {{ background: #172430; border: 1px solid #294154; border-radius: 8px; padding: 14px; }}
    .metric {{ font-size: 30px; font-weight: 700; margin-top: 8px; }}
    table {{ width: 100%; border-collapse: collapse; background: #172430; border: 1px solid #294154; }}
    th, td {{ text-align: left; border-bottom: 1px solid #294154; padding: 8px; }}
    pre {{ white-space: pre-wrap; background: #0b1118; border-radius: 8px; padding: 12px; overflow: auto; }}
  </style>
</head>
<body>
  <main>
    <h1>ANA Graph Map</h1>
    <p>Local knowledge graph generated from ANA Code Map. Read-only, deterministic, no code execution.</p>
    <div class="grid">
      <section class="card"><div>Nodes</div><div class="metric">{stats.get('nodes', 0)}</div></section>
      <section class="card"><div>Edges</div><div class="metric">{stats.get('edges', 0)}</div></section>
      <section class="card"><div>Files</div><div class="metric">{(stats.get('node_kinds') or {}).get('file', 0)}</div></section>
      <section class="card"><div>Symbols</div><div class="metric">{(stats.get('node_kinds') or {}).get('symbol', 0)}</div></section>
    </div>
    <h2>Top Hubs</h2>
    <table><thead><tr><th>Kind</th><th>Name</th><th>Degree</th></tr></thead><tbody>{hub_rows}</tbody></table>
    <h2>Stats</h2>
    <pre>{html.escape(json.dumps(stats, indent=2, ensure_ascii=False))}</pre>
  </main>
</body>
</html>
"""


def load_graph(graph_out: Path) -> dict[str, Any]:
    path = graph_out / GRAPH_JSON
    if not path.exists():
        return {"schema": "ana.graph_map.v1", "nodes": [], "edges": [], "stats": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def token_set(text: str) -> set[str]:
    raw = re.findall(r"[A-Za-z0-9_.-]{3,}", str(text or "").lower())
    result = set(raw)
    for token in raw:
        result.update(part for part in re.split(r"[_./-]+", token) if len(part) >= 3)
    return result


def query_graph(graph_out: Path, text: str, limit: int = 8) -> dict[str, Any]:
    graph = load_graph(graph_out)
    terms = token_set(text)
    raw_terms = {term.lower() for term in re.findall(r"[A-Za-z0-9_.-]{3,}", str(text or ""))}
    incoming, outgoing = adjacency(graph)
    node_lookup = {node["id"]: node for node in graph.get("nodes", [])}
    scored = []
    for node in graph.get("nodes", []):
        node_name = str(node.get("name", "")).lower()
        hay = token_set(" ".join([
            str(node.get("id", "")),
            str(node.get("name", "")),
            str(node.get("kind", "")),
            str(node.get("language", "")),
            str(node.get("purpose", "")),
        ]))
        overlap = sorted(terms & hay)
        if not overlap:
            continue
        degree = len(incoming.get(node["id"], [])) + len(outgoing.get(node["id"], []))
        exact_name_bonus = 8 if node_name in raw_terms else 0
        kind_bonus = 4 if node.get("kind") in {"file", "symbol"} else 0
        base_score = len(overlap) * 10 + exact_name_bonus + kind_bonus + min(degree, 12)
        penalty = query_rank_penalty(node, terms, degree)
        score = base_score - penalty
        scored.append((score, base_score, penalty, overlap, degree, node))
    scored.sort(key=lambda row: (-row[0], -row[1], row[2], row[5].get("kind", ""), row[5].get("name", "")))
    results = []
    for score, base_score, penalty, overlap, degree, node in scored[:limit]:
        raw_neighbors = outgoing.get(node["id"], [])[:8] + incoming.get(node["id"], [])[:8]
        neighbors, hidden_low_signal = query_neighbors(raw_neighbors, node_lookup, terms)
        results.append({
            "id": node.get("id"),
            "kind": node.get("kind"),
            "name": node.get("name"),
            "score": score,
            "base_score": base_score,
            "rank_penalty": penalty,
            "degree": degree,
            "matched_terms": overlap,
            "purpose": node.get("purpose"),
            "neighbors": neighbors[:10],
            "hidden_low_signal_neighbors": hidden_low_signal,
        })
    return {
        "success": True,
        "schema": "ana.graph_query.v1",
        "query": text,
        "updated_at": graph.get("updated_at"),
        "results_count": len(results),
        "results": results,
        "next_step": "Use top node neighbors to choose the smallest context pack." if results else "Run graph refresh after code map refresh.",
    }


def allows_low_signal_context(name: str, terms: set[str]) -> bool:
    lower = name.replace("\\", "/").lower()
    if "/docs/session_checkpoint_" in lower:
        return bool(terms & CHECKPOINT_TERMS)
    if "/docs/rem_sleep/" in lower:
        return bool(terms & REM_TERMS)
    if "/dev_artifacts/archives/" in lower or "/archives/" in lower:
        return bool(terms & ARCHIVE_TERMS)
    return True


def query_rank_penalty(node: dict[str, Any], terms: set[str], degree: int) -> int:
    kind = node.get("kind")
    name = str(node.get("name") or "")
    penalty = 0
    if kind == "keyword":
        penalty += 8 + min(max(degree - 20, 0) // 20, 8)
    if kind == "file" and is_low_signal_file(node) and not allows_low_signal_context(name, terms):
        penalty += 48
    return penalty


def query_neighbors(
    neighbors: list[dict[str, Any]],
    node_lookup: dict[str, dict[str, Any]],
    terms: set[str],
) -> tuple[list[dict[str, Any]], int]:
    visible: list[dict[str, Any]] = []
    hidden_low_signal = 0
    for neighbor in neighbors:
        neighbor_node = node_lookup.get(str(neighbor.get("id") or ""), {})
        if neighbor_node.get("kind") == "file" and is_low_signal_file(neighbor_node):
            name = str(neighbor_node.get("name") or neighbor.get("name") or "")
            if not allows_low_signal_context(name, terms):
                hidden_low_signal += 1
                continue
        visible.append(neighbor)
    return visible, hidden_low_signal


def blast_radius(graph_out: Path, changed: list[str] | str, limit: int = 20) -> dict[str, Any]:
    graph = load_graph(graph_out)
    changed_items = normalize_changed(changed)
    node_lookup = {node["id"]: node for node in graph.get("nodes", [])}
    incoming, outgoing = adjacency(graph)
    file_nodes = [node for node in graph.get("nodes", []) if node.get("kind") == "file"]
    changed_nodes = []
    for item in changed_items:
        match = best_file_node(file_nodes, item)
        if match:
            changed_nodes.append(match)

    affected: dict[str, dict[str, Any]] = {}
    for changed_node in changed_nodes:
        changed_id = changed_node["id"]
        changed_name = str(changed_node.get("name") or changed_id)
        add_affected(
            affected,
            changed_node,
            score=100,
            confidence="EXACT",
            reasons=[f"changed file: {changed_name}"],
        )

        direct_neighbors = outgoing.get(changed_id, []) + incoming.get(changed_id, [])
        for neighbor in direct_neighbors:
            neighbor_node = node_lookup.get(neighbor["id"])
            if not neighbor_node:
                continue
            if neighbor_node.get("kind") == "file":
                add_affected(
                    affected,
                    neighbor_node,
                    score=72,
                    confidence=neighbor.get("confidence") or "INFERRED",
                    reasons=[f"{neighbor.get('direction')} {neighbor.get('relation')} with {changed_name}"],
                )

        shared_context = {
            item["id"]: item for item in direct_neighbors
            if (
                item.get("id")
                and node_lookup.get(item["id"], {}).get("kind") in {"symbol", "dependency", "keyword"}
                and not is_common_context(node_lookup.get(item["id"], {}))
            )
        }
        for context_id, context in shared_context.items():
            context_node = node_lookup.get(context_id, {})
            candidates = incoming.get(context_id, []) + outgoing.get(context_id, [])
            for candidate in candidates:
                candidate_node = node_lookup.get(candidate["id"])
                if not candidate_node or candidate_node.get("kind") != "file" or candidate["id"] == changed_id:
                    continue
                relation = context.get("relation") or candidate.get("relation")
                context_kind = context_node.get("kind")
                context_name = context_node.get("name")
                score = 64 if context_kind in {"dependency", "symbol"} else 48
                confidence = "EXTRACTED" if context_kind in {"dependency", "symbol"} else "INFERRED"
                add_affected(
                    affected,
                    candidate_node,
                    score=score,
                    confidence=confidence,
                    reasons=[f"shares {context_kind} `{context_name}` via {relation}"],
                )

        for test_node in probable_tests(file_nodes, changed_name):
            add_affected(
                affected,
                test_node,
                score=82,
                confidence="INFERRED",
                reasons=[f"probable test for {changed_name}"],
            )

    results = sorted(
        affected.values(),
        key=lambda item: (-item["score"], item["kind"], item["name"]),
    )[: max(1, min(int(limit or 20), 100))]
    return {
        "success": True,
        "schema": "ana.graph_blast_radius.v1",
        "changed": changed_items,
        "matched_changed": [
            {"id": node.get("id"), "name": node.get("name"), "kind": node.get("kind")}
            for node in changed_nodes
        ],
        "updated_at": graph.get("updated_at"),
        "affected_count": len(results),
        "affected": results,
        "next_step": (
            "Run targeted tests/review for high-score affected files first."
            if results else
            "Refresh Code Map and Graph Map, then retry blast-radius."
        ),
    }


def normalize_changed(changed: list[str] | str) -> list[str]:
    if isinstance(changed, str):
        parts = re.split(r"[,;\n]+", changed)
    else:
        parts = [str(item) for item in changed]
    return [part.replace("\\", "/").strip() for part in parts if part and part.strip()]


def best_file_node(file_nodes: list[dict[str, Any]], text: str) -> dict[str, Any] | None:
    normalized = text.replace("\\", "/").strip().lower()
    if not normalized:
        return None
    for node in file_nodes:
        name = str(node.get("name") or "").replace("\\", "/").lower()
        if name == normalized:
            return node
    for node in file_nodes:
        name = str(node.get("name") or "").replace("\\", "/").lower()
        if name.endswith("/" + normalized) or normalized.endswith("/" + name):
            return node
    if Path(normalized).name not in GENERIC_FILE_NAMES:
        for node in file_nodes:
            name = str(node.get("name") or "").replace("\\", "/").lower()
            if Path(name).name == Path(normalized).name:
                return node
    if "/" in normalized and Path(normalized).name in GENERIC_FILE_NAMES:
        return None
    query_match = query_graph_from_loaded({"nodes": file_nodes, "edges": []}, normalized, limit=1)
    return query_match[0] if query_match else None


def add_affected(
    affected: dict[str, dict[str, Any]],
    node: dict[str, Any],
    *,
    score: int,
    confidence: str,
    reasons: list[str],
) -> None:
    ident = node["id"]
    adjusted_score = min(score, 38) if is_low_signal_file(node) and score < 100 else score
    current = affected.setdefault(
        ident,
        {
            "id": ident,
            "kind": node.get("kind"),
            "name": node.get("name"),
            "score": 0,
            "confidence": confidence,
            "reasons": [],
            "purpose": node.get("purpose"),
            "low_signal": is_low_signal_file(node),
        },
    )
    current["score"] = max(int(current.get("score") or 0), int(adjusted_score))
    if confidence == "EXACT" or (confidence == "EXTRACTED" and current.get("confidence") != "EXACT"):
        current["confidence"] = confidence
    for reason in reasons:
        if reason not in current["reasons"]:
            current["reasons"].append(reason)
    current["reasons"] = current["reasons"][:8]


def probable_tests(file_nodes: list[dict[str, Any]], changed_name: str) -> list[dict[str, Any]]:
    path = changed_name.replace("\\", "/").lower()
    stem = Path(path).stem
    tokens = {token for token in token_set(stem) if token not in COMMON_TEST_TOKENS and len(token) >= 4}
    tests = []
    for node in file_nodes:
        name = str(node.get("name") or "").replace("\\", "/").lower()
        if not any(marker in name for marker in ("test", "tests/", "_test.", ".spec.", ".test.")):
            continue
        name_tokens = token_set(name)
        if stem and stem in name or (tokens and tokens & name_tokens):
            tests.append(node)
    return tests[:12]


def is_common_context(node: dict[str, Any]) -> bool:
    name = str(node.get("name") or "").lower().strip()
    if name in COMMON_CONTEXT_NAMES:
        return True
    if node.get("kind") == "keyword" and name in {"ana_max", "tools", "test", "time"}:
        return True
    return False


def is_low_signal_file(node: dict[str, Any]) -> bool:
    if node.get("kind") != "file":
        return False
    name = str(node.get("name") or "").replace("\\", "/").lower()
    return any(
        part in name
        for part in (
            "/archives/",
            "/sandbox/",
            "/memory/",
            "/logs/",
            "/screenshots/",
            "/docs/session_checkpoint_",
            "/docs/rem_sleep/",
            "/docs/test_reports/",
        )
    )


def adjacency(graph: dict[str, Any]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    node_names = {node["id"]: node.get("name") for node in graph.get("nodes", [])}
    incoming: dict[str, list[dict[str, Any]]] = {}
    outgoing: dict[str, list[dict[str, Any]]] = {}
    for edge in graph.get("edges", []):
        source = edge.get("source")
        target = edge.get("target")
        if not source or not target:
            continue
        out_item = {
            "id": target,
            "name": node_names.get(target, target),
            "relation": edge.get("relation"),
            "confidence": edge.get("confidence"),
            "direction": "out",
        }
        in_item = {
            "id": source,
            "name": node_names.get(source, source),
            "relation": edge.get("relation"),
            "confidence": edge.get("confidence"),
            "direction": "in",
        }
        outgoing.setdefault(source, []).append(out_item)
        incoming.setdefault(target, []).append(in_item)
    return incoming, outgoing


def path_query(graph_out: Path, source_text: str, target_text: str, max_depth: int = 4) -> dict[str, Any]:
    graph = load_graph(graph_out)
    source = best_node_id(graph, source_text)
    target = best_node_id(graph, target_text)
    if not source or not target:
        return {"success": True, "schema": "ana.graph_path.v1", "found": False, "reason": "source_or_target_not_found"}
    neighbors: dict[str, list[str]] = {}
    edge_lookup: dict[tuple[str, str], dict[str, Any]] = {}
    for edge in graph.get("edges", []):
        a, b = edge["source"], edge["target"]
        neighbors.setdefault(a, []).append(b)
        neighbors.setdefault(b, []).append(a)
        edge_lookup[(a, b)] = edge
        edge_lookup[(b, a)] = edge
    queue = deque([(source, [source])])
    seen = {source}
    while queue:
        current, path = queue.popleft()
        if current == target:
            return render_path(graph, path, edge_lookup)
        if len(path) > max_depth + 1:
            continue
        for nxt in neighbors.get(current, []):
            if nxt in seen:
                continue
            seen.add(nxt)
            queue.append((nxt, path + [nxt]))
    return {"success": True, "schema": "ana.graph_path.v1", "found": False, "source": source, "target": target}


def best_node_id(graph: dict[str, Any], text: str) -> str | None:
    result = query_graph_from_loaded(graph, text, limit=1)
    if not result:
        return None
    return result[0].get("id")


def query_graph_from_loaded(graph: dict[str, Any], text: str, limit: int = 1) -> list[dict[str, Any]]:
    terms = token_set(text)
    raw_terms = {term.lower() for term in re.findall(r"[A-Za-z0-9_.-]{3,}", str(text or ""))}
    kind_priority = {"file": 0, "symbol": 1, "dependency": 2, "keyword": 3}
    scored = []
    for node in graph.get("nodes", []):
        name = str(node.get("name", "")).lower()
        hay = token_set(f"{node.get('id', '')} {node.get('name', '')} {node.get('kind', '')} {node.get('purpose', '')}")
        overlap = terms & hay
        if overlap:
            exact = 1 if name in raw_terms else 0
            scored.append((len(overlap), exact, kind_priority.get(node.get("kind"), 9), node))
    scored.sort(key=lambda row: (-row[0], -row[1], row[2], row[3].get("name", "")))
    return [node for *_score, node in scored[:limit]]


def render_path(graph: dict[str, Any], path: list[str], edge_lookup: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    nodes = {node["id"]: node for node in graph.get("nodes", [])}
    steps = []
    for index, ident in enumerate(path):
        node = nodes.get(ident, {"id": ident, "name": ident, "kind": "unknown"})
        item = {"id": ident, "name": node.get("name"), "kind": node.get("kind")}
        if index > 0:
            edge = edge_lookup.get((path[index - 1], ident), {})
            item["via"] = edge.get("relation")
            item["confidence"] = edge.get("confidence")
        steps.append(item)
    return {
        "success": True,
        "schema": "ana.graph_path.v1",
        "found": True,
        "hops": max(0, len(path) - 1),
        "path": steps,
    }


def stats(graph_out: Path) -> dict[str, Any]:
    graph = load_graph(graph_out)
    return {
        "success": True,
        "schema": graph.get("schema", "ana.graph_map.v1"),
        "updated_at": graph.get("updated_at"),
        "graph_out": str(graph_out),
        "stats": graph.get("stats", graph_stats(graph)),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build/query ANA MAX graph map.")
    parser.add_argument("action", choices=["refresh", "query", "path", "stats", "blast"])
    parser.add_argument("--code-map-out", default=str(CODE_MAP_OUT))
    parser.add_argument("--out", default=str(GRAPH_OUT))
    parser.add_argument("--query", default="")
    parser.add_argument("--source", default="")
    parser.add_argument("--target", default="")
    parser.add_argument("--changed", action="append", default=[])
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--max-depth", type=int, default=4)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    code_map_out = Path(args.code_map_out).resolve()
    graph_out = Path(args.out).resolve()
    if args.action == "refresh":
        graph = build_graph(code_map_out, graph_out)
        payload = {"success": True, "schema": graph.get("schema"), "graph_out": str(graph_out), "stats": graph.get("stats")}
    elif args.action == "query":
        if not args.query:
            raise SystemExit("--query is required for action=query")
        payload = query_graph(graph_out, args.query, limit=args.limit)
    elif args.action == "path":
        if not args.source or not args.target:
            raise SystemExit("--source and --target are required for action=path")
        payload = path_query(graph_out, args.source, args.target, max_depth=args.max_depth)
    elif args.action == "blast":
        changed = args.changed or ([args.query] if args.query else [])
        if not changed:
            raise SystemExit("--changed or --query is required for action=blast")
        payload = blast_radius(graph_out, changed, limit=args.limit)
    else:
        payload = stats(graph_out)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
