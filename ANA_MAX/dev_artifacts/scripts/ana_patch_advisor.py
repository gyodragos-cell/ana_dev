"""Read-only patch advisor for ANA lab signals.

This is deliberately not an auto-patcher. It turns current diagnostics into a
small, reviewable repair plan that Codex or the operator can approve.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import ana_dirty_tree_report


DEFAULT_MCP_URL = "http://127.0.0.1:8766/mcp"
REPO_ROOT = Path(__file__).resolve().parents[3]
ANA_ROOT = REPO_ROOT / "ANA_MAX"
REPORT_DIR = ANA_ROOT / "dev_artifacts" / "reports"
GRAPH_SCRIPT = ANA_ROOT / "dev_artifacts" / "scripts" / "ana_graph_map.py"
GRAPH_OUT = ANA_ROOT / "memory" / "graph_map"


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def json_request(url: str, payload: dict[str, Any], timeout: int = 30) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def call_tool(mcp_url: str, tool: str, arguments: dict[str, Any], timeout: int = 30) -> dict[str, Any]:
    response = json_request(
        mcp_url,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool, "arguments": arguments},
        },
        timeout=timeout,
    )
    content = response.get("result", {}).get("content", [])
    if not content:
        return {"success": False, "error": response.get("error") or "missing MCP content"}
    text = str(content[0].get("text") or "")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {"success": False, "error": "non-JSON tool response", "text": text[:500]}
    return payload if isinstance(payload, dict) else {"success": False, "data": payload}


def git_changed_paths(limit: int = 80) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=10,
        )
    except Exception:
        return []
    if result.returncode != 0:
        return []
    paths = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        paths.append(line[3:].strip().replace("\\", "/"))
        if len(paths) >= limit:
            break
    return paths


def classify_path(path: str) -> str:
    if "SESSION_CHECKPOINT_" in path or "/rem_sleep/" in path:
        return "memory"
    if path.startswith("docs/") or "/docs/" in path:
        return "docs"
    if path.startswith("tests/") or "/tests/" in path:
        return "tests"
    if path.startswith("ANA_MAX/tools/") or path.startswith("ANA_MAX/dev_artifacts/scripts/"):
        return "runtime"
    if path.startswith("vscode_extension/"):
        return "extension"
    return "other"


def graph_changed_candidates(changed_paths: list[str], limit: int = 5) -> list[str]:
    candidates = []
    for path in changed_paths:
        category = classify_path(path)
        if category not in {"runtime", "extension", "tests"}:
            continue
        normalized = path.replace("\\", "/")
        if any(part in normalized for part in ("/archives/", "/sandbox/", "/memory/", "/logs/", "/screenshots/")):
            continue
        candidates.append(normalized)
        if len(candidates) >= limit:
            break
    return candidates


def load_graph_map():
    spec = importlib.util.spec_from_file_location("ana_graph_map_for_patch_advisor", GRAPH_SCRIPT)
    if not spec or not spec.loader:
        raise RuntimeError(f"Graph map script not found: {GRAPH_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def build_blast_radius(changed_paths: list[str], limit: int = 12) -> dict[str, Any]:
    candidates = graph_changed_candidates(changed_paths)
    if not candidates:
        return {
            "available": False,
            "reason": "no_runtime_extension_or_test_paths",
            "candidates": [],
        }
    try:
        graph_map = load_graph_map()
        data = graph_map.blast_radius(GRAPH_OUT, candidates, limit=limit)
        return {
            "available": bool(data.get("success")),
            "candidates": candidates,
            "schema": data.get("schema"),
            "matched_changed": data.get("matched_changed", []),
            "affected_count": data.get("affected_count", 0),
            "affected": data.get("affected", [])[:limit],
            "next_step": data.get("next_step"),
        }
    except Exception as exc:
        return {
            "available": False,
            "reason": str(exc),
            "candidates": candidates,
        }


def active_blast_items(blast_radius: dict[str, Any]) -> list[dict[str, Any]]:
    items = blast_radius.get("affected") if isinstance(blast_radius, dict) else []
    if not isinstance(items, list):
        return []
    active = []
    for item in items:
        if item.get("low_signal"):
            continue
        name = str(item.get("name") or "")
        if not name:
            continue
        if name.startswith(("ANA_MAX/", "tests/", "vscode_extension/")):
            active.append(item)
    return active


def build_recommendations(
    findings: list[dict[str, Any]],
    changed_paths: list[str],
    blast_radius: dict[str, Any] | None = None,
    dirty_tree: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []
    kinds = {str(item.get("kind") or "") for item in findings}
    severities = {str(item.get("severity") or "") for item in findings}
    categories = {}
    for path in changed_paths:
        category = classify_path(path)
        categories[category] = categories.get(category, 0) + 1

    if "large_dirty_tree" in kinds:
        evidence = dirty_tree_evidence(findings, categories, dirty_tree)
        batches = dirty_tree_review_batches(dirty_tree)
        recommendations.append({
            "title": "Do not patch blindly while the lab tree is large",
            "confidence": 0.92,
            "evidence": evidence,
            "suggested_files": ["ANA_MAX/dev_artifacts/scripts/ana_memory_hygiene.py"],
            "next_step": "Keep current work scoped; archive checkpoint/REM noise only after explicit operator approval.",
            "apply_automatically": False,
        })
        if batches:
            first = batches[0]
            recommendations.append({
                "title": "Review active work batches before choosing a patch",
                "confidence": 0.88,
                "evidence": "; ".join(
                    f"{batch.get('category')}={batch.get('count')}"
                    for batch in batches[:6]
                ),
                "suggested_files": [str(path) for path in (first.get("sample") or [])[:5]],
                "next_step": str(first.get("next_step") or "Review the first active work batch, then run focused tests."),
                "apply_automatically": False,
            })

    if "traceback" in kinds or "syntax" in kinds or "python_import" in kinds:
        recommendations.append({
            "title": "Investigate highest-severity runtime finding before broad edits",
            "confidence": 0.85,
            "evidence": f"Error Radar severities: {', '.join(sorted(severities)) or 'unknown'}",
            "suggested_files": [],
            "next_step": "Open the owning file from the finding, reproduce once, then add a focused regression test.",
            "apply_automatically": False,
        })

    active_blast = active_blast_items(blast_radius or {})
    if active_blast:
        top = active_blast[:5]
        recommendations.append({
            "title": "Review graph blast-radius before editing",
            "confidence": 0.82,
            "evidence": "; ".join(
                f"{item.get('name')} score={item.get('score')} confidence={item.get('confidence')}"
                for item in top
            ),
            "suggested_files": [str(item.get("name")) for item in top if item.get("name")],
            "next_step": "Read high-score affected files/tests first, then run the smallest targeted pytest or extension test.",
            "apply_automatically": False,
        })

    if not recommendations:
        recommendations.append({
            "title": "No patch candidate from current diagnostics",
            "confidence": 0.7,
            "evidence": "Error Radar did not report actionable code blockers.",
            "suggested_files": [],
            "next_step": "Continue with one scoped lab action and verify with Nucleus Smoke or Autonomy Pass.",
            "apply_automatically": False,
        })
    return recommendations


def local_dirty_tree_evidence(dirty_tree: dict[str, Any]) -> str:
    categories = dirty_tree.get("categories") if isinstance(dirty_tree, dict) else {}
    categories = categories if isinstance(categories, dict) else {}
    return (
        f"{dirty_tree.get('total')} changed paths "
        f"({dirty_tree.get('tracked')} tracked, {dirty_tree.get('untracked')} untracked); "
        f"{categories.get('checkpoint', 0)} checkpoints, "
        f"{categories.get('rem_sleep', 0)} rem_sleep reports, "
        f"{categories.get('doc', 0)} docs, "
        f"{categories.get('test', 0)} tests, "
        f"{categories.get('runtime', 0)} runtime, "
        f"{categories.get('script', 0)} scripts from local Dirty Tree."
    )


def dirty_tree_review_batches(dirty_tree: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(dirty_tree, dict):
        return []
    active = dirty_tree.get("active_work")
    if not isinstance(active, dict):
        return []
    batches = active.get("review_batches")
    if not isinstance(batches, list):
        return []
    return [batch for batch in batches if isinstance(batch, dict)]


def compact_review_batches(dirty_tree: dict[str, Any]) -> list[dict[str, Any]]:
    compact = []
    for batch in dirty_tree_review_batches(dirty_tree):
        compact.append({
            "category": batch.get("category"),
            "count": batch.get("count"),
            "tracked": batch.get("tracked"),
            "untracked": batch.get("untracked"),
            "sample": (batch.get("sample") or [])[:5],
            "next_step": batch.get("next_step"),
            "suggested_commands": (batch.get("suggested_commands") or [])[:3],
        })
    return compact


def dirty_tree_evidence(
    findings: list[dict[str, Any]],
    sampled_categories: dict[str, int],
    dirty_tree: dict[str, Any] | None = None,
) -> str:
    if isinstance(dirty_tree, dict) and dirty_tree.get("schema") == "ana.dirty_tree_report.v1":
        return local_dirty_tree_evidence(dirty_tree)
    for finding in findings:
        if finding.get("kind") != "large_dirty_tree":
            continue
        details = finding.get("details")
        if not isinstance(details, dict):
            continue
        total = details.get("total")
        tracked = details.get("tracked")
        untracked = details.get("untracked")
        checkpoints = details.get("checkpoints")
        docs = details.get("docs")
        tests = details.get("tests")
        runtime = details.get("runtime")
        if any(value is not None for value in (total, checkpoints, docs, tests, runtime)):
            return (
                f"{total} changed paths ({tracked} tracked, {untracked} untracked); "
                f"{checkpoints} checkpoints, {docs} docs, {tests} tests, {runtime} runtime paths from Error Radar."
            )
    return (
        f"{sampled_categories.get('memory', 0)} memory files, "
        f"{sampled_categories.get('docs', 0)} docs, "
        f"{sampled_categories.get('tests', 0)} tests, "
        f"{sampled_categories.get('runtime', 0)} runtime/script paths in sampled git state."
    )


def is_known_noise_finding(finding: dict[str, Any]) -> bool:
    summary = str(finding.get("summary") or "")
    kind = str(finding.get("kind") or "")
    if kind == "traceback" and "name=debugger" in summary and "traceback_text" in summary:
        return True
    return False


def normalize_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [finding for finding in findings if not is_known_noise_finding(finding)]


def build_report(mcp_url: str, timeout: int = 30) -> dict[str, Any]:
    radar = call_tool(mcp_url, "error_radar", {"limit": 20}, timeout=timeout)
    findings = []
    if radar.get("success") and isinstance(radar.get("data"), dict):
        findings = radar["data"].get("findings") or []
    normalized_findings = normalize_findings(findings)
    changed_paths = git_changed_paths()
    blast_radius = build_blast_radius(changed_paths)
    try:
        dirty_tree = ana_dirty_tree_report.build_report(limit=12)
    except Exception as exc:
        dirty_tree = {"available": False, "error": str(exc)}
    return {
        "schema": "ana.patch_advisor.v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "mode": "suggest_only",
        "inputs": {
            "error_radar_success": bool(radar.get("success")),
            "finding_count": len(normalized_findings),
            "raw_finding_count": len(findings),
            "noise_filtered": len(findings) - len(normalized_findings),
            "changed_path_sample": len(changed_paths),
            "dirty_tree_available": dirty_tree.get("schema") == "ana.dirty_tree_report.v1",
            "dirty_tree_total": dirty_tree.get("total"),
            "blast_radius_available": bool(blast_radius.get("available")),
            "blast_radius_candidates": len(blast_radius.get("candidates") or []),
            "blast_radius_affected": int(blast_radius.get("affected_count") or 0),
        },
        "findings": normalized_findings[:5],
        "dirty_tree": {
            "available": dirty_tree.get("schema") == "ana.dirty_tree_report.v1",
            "total": dirty_tree.get("total"),
            "tracked": dirty_tree.get("tracked"),
            "untracked": dirty_tree.get("untracked"),
            "categories": dirty_tree.get("categories", {}),
            "active_work": dirty_tree.get("active_work", {}),
            "review_batches": compact_review_batches(dirty_tree),
            "recommendation": dirty_tree.get("recommendation"),
            "error": dirty_tree.get("error"),
        },
        "blast_radius": blast_radius,
        "recommendations": build_recommendations(normalized_findings, changed_paths, blast_radius, dirty_tree),
        "policy": {
            "read_only": True,
            "writes_files": False,
            "requires_operator_for_apply": True,
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build read-only ANA patch advice from current diagnostics.")
    parser.add_argument("--mcp-url", default=DEFAULT_MCP_URL)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--write-report", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_report(args.mcp_url, timeout=args.timeout)
    if args.write_report:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        path = REPORT_DIR / f"patch_advisor_{stamp}.json"
        path.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
        report["report"] = str(path)
    first = report["recommendations"][0]
    print(f"ANA Patch Advisor: {first['title']} confidence={int(first['confidence'] * 100)}%")
    print(f"next_action={first['next_step']}")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
