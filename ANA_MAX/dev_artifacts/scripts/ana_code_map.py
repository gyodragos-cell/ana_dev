"""ANA MAX code map builder.

Builds a compact Antigravity-like project map:
- filters generated/noisy folders
- extracts deterministic structure from source files
- writes markdown summaries to ANA_MAX/memory/code_map
- answers quick routing queries from those summaries

This first pass is intentionally local and deterministic. LLM/tree-sitter
summaries can be added later without changing the output contract.
"""

from __future__ import annotations

import argparse
import ast
import fnmatch
import hashlib
import json
import os
import re
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


REPO_ROOT = Path(__file__).resolve().parents[3]
ANA_ROOT = REPO_ROOT / "ANA_MAX"
DEFAULT_PROJECT = REPO_ROOT
DEFAULT_OUT = ANA_ROOT / "memory" / "code_map"
INDEX_FILE = "index.json"

IGNORE_PATTERNS = [
    ".git/**",
    ".venv/**",
    "venv/**",
    ".pytest_cache/**",
    ".kiro/**",
    ".qoder/**",
    ".claude_brain/**",
    ".uploads/**",
    "__pycache__/**",
    "node_modules/**",
    "logs/**",
    "screenshots/**",
    "video/**",
    "voice_temp/**",
    "memory/**",
    "sandbox/**",
    "**/__pycache__/**",
    "**/node_modules/**",
    "**/venv/**",
    "**/.kiro/**",
    "**/logs/**",
    "**/screenshots/**",
    "**/video/**",
    "**/voice_temp/**",
    "**/memory/**",
    "**/sandbox/**",
    "**/dev_artifacts/vsix_build_*",
    "**/dev_artifacts/vsix_verify_*",
    "**/*.min.js",
    "**/*.vsix",
    "**/*.png",
    "**/*.jpg",
    "**/*.jpeg",
    "**/*.gif",
    "**/*.ico",
    "**/*.db",
    "**/*.sqlite",
    "**/*.pyc",
]

PRUNE_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    ".pytest_cache",
    ".kiro",
    ".qoder",
    ".claude_brain",
    ".uploads",
    "__pycache__",
    "node_modules",
    "logs",
    "screenshots",
    "video",
    "voice_temp",
    "memory",
    "sandbox",
}

SOURCE_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".java",
    ".cs",
    ".go",
    ".rs",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
    ".md",
}

BINARY_EXTENSIONS = {
    ".exe",
    ".dll",
    ".so",
    ".dylib",
}

BINARY_MAP_MAX_BYTES = 25 * 1024 * 1024


@dataclass
class FileSummary:
    path: str
    language: str
    size: int
    mtime: float
    sha1: str
    purpose: str
    symbols: list[str]
    imports: list[str]
    dependencies: list[str]
    keywords: list[str]
    summary_file: str


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def relpath(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def normalize_for_match(path: Path, root: Path) -> str:
    return relpath(path, root)


def is_ignored(path: Path, root: Path) -> bool:
    rel = normalize_for_match(path, root)
    return any(fnmatch.fnmatch(rel, pattern) for pattern in IGNORE_PATTERNS)


def is_source_file(path: Path) -> bool:
    return path.suffix.lower() in SOURCE_EXTENSIONS or path.suffix.lower() in BINARY_EXTENSIONS


def read_text(path: Path, max_bytes: int = 400_000) -> str:
    data = path.read_bytes()[:max_bytes]
    return data.decode("utf-8", errors="replace")


def sha1_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="replace")).hexdigest()


def sha1_file(path: Path) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def language_for(path: Path) -> str:
    return {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".java": "java",
        ".cs": "csharp",
        ".go": "go",
        ".rs": "rust",
        ".cpp": "cpp",
        ".c": "c",
        ".h": "c",
        ".hpp": "cpp",
        ".md": "markdown",
        ".exe": "binary",
        ".dll": "binary",
        ".so": "binary",
        ".dylib": "binary",
    }.get(path.suffix.lower(), "unknown")


def extract_python(text: str) -> tuple[list[str], list[str], list[str]]:
    symbols: list[str] = []
    imports: list[str] = []
    dependencies: list[str] = []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return symbols, imports, dependencies

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.append(node.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name.split(".")[0]
                imports.append(name)
                dependencies.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module:
                imports.append(module.split(".")[0])
                dependencies.append(module)
    return unique(symbols), unique(imports), unique(dependencies)


JS_SYMBOL_RE = re.compile(
    r"(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)|"
    r"(?:export\s+)?class\s+([A-Za-z_$][\w$]*)|"
    r"(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>"
)
IMPORT_RE = re.compile(r"(?:from\s+['\"]([^'\"]+)['\"]|import\s+[^'\"]*['\"]([^'\"]+)['\"]|require\(['\"]([^'\"]+)['\"]\))")


def extract_regex(text: str) -> tuple[list[str], list[str], list[str]]:
    symbols: list[str] = []
    dependencies: list[str] = []
    for match in JS_SYMBOL_RE.finditer(text):
        symbols.extend([group for group in match.groups() if group])
    for match in IMPORT_RE.finditer(text):
        dep = next((group for group in match.groups() if group), "")
        if dep:
            dependencies.append(dep)
    imports = [dep.split("/")[0].split(".")[0] for dep in dependencies if dep]
    return unique(symbols), unique(imports), unique(dependencies)


def extract_markdown(text: str) -> tuple[list[str], list[str], list[str]]:
    headings = []
    for line in text.splitlines():
        if line.startswith("#"):
            headings.append(line.lstrip("#").strip())
    return unique(headings[:30]), [], []


def unique(values: list[str], limit: int = 80) -> list[str]:
    seen = set()
    result = []
    for value in values:
        value = str(value).strip()
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
        if len(result) >= limit:
            break
    return result


def is_logic_file(path: Path, text: str, symbols: list[str], dependencies: list[str]) -> bool:
    if path.suffix.lower() == ".md":
        return bool(symbols) and len(text) > 120
    return bool(symbols or dependencies)


def purpose_for(path: Path, text: str, symbols: list[str]) -> str:
    doc = ""
    if path.suffix.lower() == ".py":
        try:
            module = ast.parse(text)
            doc = ast.get_docstring(module) or ""
        except SyntaxError:
            doc = ""
    if not doc:
        for line in text.splitlines()[:30]:
            stripped = line.strip(" #/*")
            if len(stripped) > 25 and not stripped.startswith(("import ", "from ")):
                doc = stripped
                break
    if doc:
        return " ".join(doc.split())[:220]
    if symbols:
        return f"Defines {', '.join(symbols[:5])}."
    return f"Source module {path.name}."


def keywords_for(path: str, purpose: str, symbols: list[str], imports: list[str]) -> list[str]:
    raw = " ".join([path, purpose, " ".join(symbols), " ".join(imports)]).lower()
    words = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]{2,}", raw)
    stop = {"the", "and", "for", "with", "from", "this", "that", "tool", "ana", "max"}
    return unique([word for word in words if word not in stop], limit=40)


def summary_filename(rel: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "__", rel)
    return f"{safe}.summary.md"


def load_binary_map_module():
    import importlib.util

    script = ANA_ROOT / "dev_artifacts" / "scripts" / "ana_binary_map.py"
    spec = importlib.util.spec_from_file_location("ana_binary_map_for_code_map", script)
    if not spec or not spec.loader:
        raise RuntimeError(f"Binary map script not found: {script}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def extract_binary_file(path: Path, root: Path, out_dir: Path) -> FileSummary | None:
    if path.stat().st_size > BINARY_MAP_MAX_BYTES:
        return None
    binary_map = load_binary_map_module().parse_binary(path, max_bytes=BINARY_MAP_MAX_BYTES, strings_limit=30)
    rel = relpath(path, root)
    stat = path.stat()
    symbols = [binary_map.format, binary_map.architecture]
    symbols.extend(binary_map.exports[:30])
    imports = binary_map.imports[:40]
    dependencies = binary_map.imports[:40]
    section_names = [section.get("name", "") for section in binary_map.sections[:12]]
    purpose = (
        f"Static binary {binary_map.format} {binary_map.architecture}; "
        f"entry={binary_map.entry_point or 'unknown'}; "
        f"sections={', '.join(section_names) if section_names else 'none'}; "
        f"imports={', '.join(imports[:8]) if imports else 'none'}."
    )
    return FileSummary(
        path=rel,
        language="binary",
        size=stat.st_size,
        mtime=stat.st_mtime,
        sha1=sha1_file(path),
        purpose=purpose[:240],
        symbols=unique(symbols),
        imports=imports,
        dependencies=dependencies,
        keywords=keywords_for(rel, purpose, symbols, imports),
        summary_file=summary_filename(rel),
    )


def extract_file(path: Path, root: Path, out_dir: Path) -> FileSummary | None:
    if path.suffix.lower() in BINARY_EXTENSIONS:
        return extract_binary_file(path, root, out_dir)

    text = read_text(path)
    lang = language_for(path)
    if lang == "python":
        symbols, imports, dependencies = extract_python(text)
    elif lang in {"javascript", "typescript"}:
        symbols, imports, dependencies = extract_regex(text)
    elif lang == "markdown":
        symbols, imports, dependencies = extract_markdown(text)
    else:
        symbols, imports, dependencies = extract_regex(text)

    if not is_logic_file(path, text, symbols, dependencies):
        return None

    rel = relpath(path, root)
    stat = path.stat()
    digest = sha1_text(text)
    purpose = purpose_for(path, text, symbols)
    summary_file = summary_filename(rel)
    return FileSummary(
        path=rel,
        language=lang,
        size=stat.st_size,
        mtime=stat.st_mtime,
        sha1=digest,
        purpose=purpose,
        symbols=symbols[:40],
        imports=imports[:40],
        dependencies=dependencies[:40],
        keywords=keywords_for(rel, purpose, symbols, imports),
        summary_file=summary_file,
    )


def write_summary(summary: FileSummary, out_dir: Path) -> None:
    target = out_dir / summary.summary_file
    lines = [
        f"# {summary.path}",
        "",
        f"- language: `{summary.language}`",
        f"- purpose: {summary.purpose}",
        f"- symbols: {', '.join(summary.symbols[:25]) if summary.symbols else 'none'}",
        f"- imports: {', '.join(summary.imports[:25]) if summary.imports else 'none'}",
        f"- dependencies: {', '.join(summary.dependencies[:25]) if summary.dependencies else 'none'}",
        f"- keywords: {', '.join(summary.keywords[:30]) if summary.keywords else 'none'}",
        "",
    ]
    target.write_text("\n".join(lines), encoding="utf-8")


def load_index(out_dir: Path) -> dict[str, Any]:
    path = out_dir / INDEX_FILE
    if not path.exists():
        return {"schema": "ana.code_map.v1", "files": {}, "updated_at": None}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"schema": "ana.code_map.v1", "files": {}, "updated_at": None}


def save_index(out_dir: Path, index: dict[str, Any]) -> None:
    index["updated_at"] = now_iso()
    (out_dir / INDEX_FILE).write_text(json.dumps(index, indent=2, sort_keys=True), encoding="utf-8")


def query_rank_penalty(path: str, query_terms: set[str]) -> int:
    """Demote generated memory unless the query explicitly asks for it."""
    normalized = path.replace("\\", "/")
    lower = normalized.lower()
    if lower.startswith("ana_max/docs/session_checkpoint_"):
        return 0 if query_terms & {"checkpoint", "checkpoints", "session", "handoff"} else 5
    if lower.startswith("ana_max/docs/rem_sleep/"):
        return 0 if query_terms & {"rem", "sleep", "retrospective", "memory"} else 5
    if "/dev_artifacts/archives/" in lower or lower.startswith("ana_max/archives/"):
        archive_terms = {
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
        return 0 if query_terms & archive_terms else 3
    return 0


def iter_project_files(root: Path) -> list[Path]:
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        rel_dir = current.relative_to(root).as_posix() if current != root else ""
        dirnames[:] = [
            dirname
            for dirname in dirnames
            if dirname not in PRUNE_DIR_NAMES
            and not dirname.startswith("vsix_build_")
            and not dirname.startswith("vsix_verify_")
            and not is_ignored(current / dirname, root)
        ]
        if rel_dir and is_ignored(current, root):
            continue
        for filename in filenames:
            path = current / filename
            if is_ignored(path, root) or not is_source_file(path):
                continue
            files.append(path)
    return files


def refresh(root: Path, out_dir: Path, force: bool = False) -> dict[str, Any]:
    started = time.time()
    out_dir.mkdir(parents=True, exist_ok=True)
    index = load_index(out_dir)
    old_files: dict[str, Any] = index.get("files", {})
    new_files: dict[str, Any] = {}
    processed = updated = skipped = ignored_non_logic = 0

    for path in iter_project_files(root):
        processed += 1
        rel = relpath(path, root)
        stat = path.stat()
        old = old_files.get(rel, {})
        if not force and old.get("mtime") == stat.st_mtime and old.get("size") == stat.st_size:
            new_files[rel] = old
            skipped += 1
            continue

        summary = extract_file(path, root, out_dir)
        if summary is None:
            ignored_non_logic += 1
            continue
        write_summary(summary, out_dir)
        new_files[rel] = asdict(summary)
        updated += 1

    removed = sorted(set(old_files) - set(new_files))
    for rel in removed:
        old_summary = old_files.get(rel, {}).get("summary_file")
        if old_summary:
            try:
                (out_dir / old_summary).unlink(missing_ok=True)
            except OSError:
                pass
    live_summaries = {item.get("summary_file") for item in new_files.values()}
    orphaned = 0
    for summary_path in out_dir.glob("*.summary.md"):
        if summary_path.name in live_summaries:
            continue
        try:
            summary_path.unlink()
            orphaned += 1
        except OSError:
            pass

    index = {
        "schema": "ana.code_map.v1",
        "project_root": str(root),
        "out_dir": str(out_dir),
        "updated_at": now_iso(),
        "files": new_files,
    }
    save_index(out_dir, index)
    return {
        "success": True,
        "project_root": str(root),
        "out_dir": str(out_dir),
        "files_seen": processed,
        "summaries": len(new_files),
        "updated": updated,
        "skipped": skipped,
        "ignored_non_logic": ignored_non_logic,
        "removed": len(removed),
        "orphaned_summaries_removed": orphaned,
        "elapsed_sec": round(time.time() - started, 3),
    }


def query(out_dir: Path, text: str, limit: int = 8) -> dict[str, Any]:
    index = load_index(out_dir)
    files = index.get("files", {})
    raw_terms = re.findall(r"[a-zA-Z_][a-zA-Z0-9_.-]{2,}", text.lower())
    query_terms = set(raw_terms)
    for term in raw_terms:
        query_terms.update(part for part in re.split(r"[_./-]+", term) if len(part) >= 3)
    scored = []
    for item in files.values():
        hay = set(item.get("keywords") or [])
        hay.update(str(item.get("path", "")).lower().replace("/", " ").split())
        hay.update(symbol.lower() for symbol in item.get("symbols", []))
        overlap = sorted(query_terms & hay)
        if not overlap:
            continue
        base_score = len(overlap) + min(3, len(set(item.get("symbols", [])) & query_terms))
        penalty = query_rank_penalty(str(item.get("path", "")), query_terms)
        score = base_score - penalty
        scored.append((score, base_score, penalty, overlap, item))
    scored.sort(key=lambda row: (-row[0], -row[1], row[2], row[4].get("path", "")))
    results = [
        {
            "file": item.get("path"),
            "summary_file": item.get("summary_file"),
            "score": score,
            "base_score": base_score,
            "rank_penalty": penalty,
            "matched_terms": overlap,
            "purpose": item.get("purpose"),
            "symbols": item.get("symbols", [])[:12],
            "dependencies": item.get("dependencies", [])[:12],
        }
        for score, base_score, penalty, overlap, item in scored[:limit]
    ]
    return {
        "success": True,
        "query": text,
        "updated_at": index.get("updated_at"),
        "results_count": len(results),
        "results": results,
        "next_step": "Open the top file only, then inspect nearby symbols." if results else "Run refresh or use project_navigator grep as fallback.",
    }


def stats(out_dir: Path) -> dict[str, Any]:
    index = load_index(out_dir)
    files = index.get("files", {})
    languages: dict[str, int] = {}
    for item in files.values():
        lang = item.get("language", "unknown")
        languages[lang] = languages.get(lang, 0) + 1
    return {
        "success": True,
        "schema": index.get("schema", "ana.code_map.v1"),
        "project_root": index.get("project_root"),
        "out_dir": str(out_dir),
        "updated_at": index.get("updated_at"),
        "summaries": len(files),
        "languages": dict(sorted(languages.items())),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build/query ANA MAX compact code map.")
    parser.add_argument("action", choices=["refresh", "query", "stats"])
    parser.add_argument("--project", default=str(DEFAULT_PROJECT))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--query", default="")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--force", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.project).resolve()
    out_dir = Path(args.out).resolve()

    if args.action == "refresh":
        payload = refresh(root, out_dir, force=args.force)
    elif args.action == "query":
        if not args.query:
            raise SystemExit("--query is required for action=query")
        payload = query(out_dir, args.query, limit=args.limit)
    else:
        payload = stats(out_dir)

    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
