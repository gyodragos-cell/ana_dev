"""ANA MAX v22 context builder scaffolding.

The context builder prepares compact, factual context for the v22 orchestrator.
It deliberately avoids heavy scans in this first scaffold and leaves concrete
collection strategies to future integrations with ANA tools such as workspace
situational awareness, error radar, project navigation, and focused file reads.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


DEFAULT_CONFIDENCE = 0.35


def _utc_now() -> str:
    """Return an ISO-8601 UTC timestamp for cache and context records."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class ContextSnapshot:
    """Compact context passed from the builder to planning and routing."""

    summary: str
    facts: tuple[str, ...] = field(default_factory=tuple)
    workspace_state: Mapping[str, Any] = field(default_factory=dict)
    recent_errors: tuple[Mapping[str, Any], ...] = field(default_factory=tuple)
    docs: tuple[Mapping[str, Any], ...] = field(default_factory=tuple)
    blind_spots: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = DEFAULT_CONFIDENCE
    created_at: str = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe context representation for engines and tests."""
        return {
            "summary": self.summary,
            "facts": list(self.facts),
            "workspace_state": dict(self.workspace_state),
            "recent_errors": [dict(item) for item in self.recent_errors],
            "docs": [dict(item) for item in self.docs],
            "blind_spots": list(self.blind_spots),
            "confidence": self.confidence,
            "created_at": self.created_at,
        }


class ContextBuilder:
    """Build and cache compact context for ANA MAX v22 tasks."""

    def __init__(self, cache_ttl_seconds: int = 30, max_docs: int = 5) -> None:
        """Initialize placeholder caches and freshness settings."""
        self.cache_ttl_seconds = cache_ttl_seconds
        self.max_docs = max_docs
        self._cache: dict[str, Any] = {
            "created_at": None,
            "workspace_state": None,
            "recent_errors": None,
            "docs": None,
        }

    def build_context(self, task_envelope: Any) -> ContextSnapshot:
        """Collect and merge the minimum useful context for a task envelope."""
        workspace_state = self._collect_workspace_state(task_envelope)
        recent_errors = self._collect_recent_errors(task_envelope)
        docs = self._collect_docs(task_envelope)
        return self._merge_and_summarize(
            task_envelope=task_envelope,
            workspace_state=workspace_state,
            recent_errors=recent_errors,
            docs=docs,
        )

    def _collect_workspace_state(self, task_envelope: Any) -> dict[str, Any]:
        """Collect compact real workspace state without broad file reads."""
        workspace = self._get_envelope_value(task_envelope, "workspace", "")
        root = Path(str(workspace or os.getcwd())).expanduser()
        exists = root.exists()
        is_dir = root.is_dir()
        git = self._collect_git_state(root) if exists and is_dir else {"known": False, "error": "workspace unavailable"}
        state = {
            "workspace": str(root),
            "exists": exists,
            "is_dir": is_dir,
            "source": "filesystem",
            "collected_at": _utc_now(),
            "git": git,
            "active_window": {"known": False},
        }
        self._cache["workspace_state"] = state
        self._cache["created_at"] = state["collected_at"]
        return state

    def _collect_recent_errors(self, task_envelope: Any) -> tuple[dict[str, Any], ...]:
        """Collect recent error signals from common local report files."""
        workspace = Path(str(self._get_envelope_value(task_envelope, "workspace", "") or os.getcwd()))
        errors: list[dict[str, Any]] = []
        for name in ("pytest.log", "test-output.log", "error.log"):
            path = workspace / name
            if path.exists() and path.is_file():
                errors.append({"path": str(path), "kind": "log_file", "loaded": False})
        self._cache["recent_errors"] = errors
        return tuple(errors)

    def _collect_docs(self, task_envelope: Any) -> tuple[dict[str, Any], ...]:
        """Collect relevant documentation pointers and small excerpts."""
        workspace = Path(str(self._get_envelope_value(task_envelope, "workspace", "") or os.getcwd()))
        candidates = [
            workspace / "ANA_MAX_V22_ARCHITECTURE.md",
            workspace / "README.md",
            workspace / "AGENT_START_HERE.md",
        ]
        docs: list[dict[str, Any]] = []
        for path in candidates:
            if len(docs) >= self.max_docs:
                break
            if path.exists() and path.is_file():
                docs.append(
                    {
                        "path": str(path),
                        "reason": "runtime owner documentation",
                        "loaded": True,
                        "excerpt": self._read_excerpt(path),
                    }
                )
        self._cache["docs"] = docs
        return tuple(docs)

    def _merge_and_summarize(
        self,
        task_envelope: Any,
        workspace_state: Mapping[str, Any],
        recent_errors: tuple[Mapping[str, Any], ...],
        docs: tuple[Mapping[str, Any], ...],
    ) -> ContextSnapshot:
        """Merge collected context into a compact summary object."""
        task = self._get_envelope_value(task_envelope, "task", "")
        facts = ["ContextBuilder active"]
        if workspace_state.get("workspace"):
            facts.append(f"Workspace set: {workspace_state['workspace']}")
        if workspace_state.get("git", {}).get("known"):
            facts.append(f"Git branch: {workspace_state['git'].get('branch', 'unknown')}")
        if docs:
            facts.append(f"Documentation pointers: {len(docs)}")
        if recent_errors:
            facts.append(f"Recent errors: {len(recent_errors)}")

        blind_spots = ["active UI not inspected"]
        if not workspace_state.get("git", {}).get("known"):
            blind_spots.append("git state unavailable")
        if not docs:
            blind_spots.append("no owner docs found")

        summary_task = task or "unspecified task"
        summary = f"Compact scaffold context for: {summary_task}"

        confidence = DEFAULT_CONFIDENCE
        if workspace_state.get("exists"):
            confidence += 0.1
        if workspace_state.get("git", {}).get("known"):
            confidence += 0.15
        if docs:
            confidence += 0.15
        confidence = round(min(confidence, 0.95), 4)

        return ContextSnapshot(
            summary=summary,
            facts=tuple(facts),
            workspace_state=dict(workspace_state),
            recent_errors=tuple(dict(item) for item in recent_errors),
            docs=tuple(dict(item) for item in docs),
            blind_spots=tuple(blind_spots),
            confidence=confidence,
        )

    @staticmethod
    def _get_envelope_value(task_envelope: Any, name: str, default: Any = None) -> Any:
        """Read a value from a TaskEnvelope-like object or mapping."""
        if isinstance(task_envelope, Mapping):
            return task_envelope.get(name, default)
        return getattr(task_envelope, name, default)

    @staticmethod
    def _read_excerpt(path: Path, max_chars: int = 500) -> str:
        """Read a small UTF-8 tolerant excerpt from an owner document."""
        try:
            return path.read_text(encoding="utf-8-sig", errors="replace")[:max_chars]
        except OSError:
            return ""

    @staticmethod
    def _collect_git_state(root: Path) -> dict[str, Any]:
        """Collect a compact git status snapshot when git is available."""
        try:
            branch = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=str(root),
                text=True,
                capture_output=True,
                timeout=2,
                check=False,
            )
            status = subprocess.run(
                ["git", "status", "--short"],
                cwd=str(root),
                text=True,
                capture_output=True,
                timeout=2,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            return {"known": False, "error": str(error)}

        if branch.returncode != 0 or status.returncode != 0:
            return {"known": False, "error": (branch.stderr or status.stderr).strip()}

        changed = [line for line in status.stdout.splitlines() if line.strip()]
        return {
            "known": True,
            "branch": branch.stdout.strip() or "detached",
            "dirty": bool(changed),
            "changed_count": len(changed),
        }
