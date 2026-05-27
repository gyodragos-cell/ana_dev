"""
ANA MAX - Session Checkpoint Tool

Stores a compact handoff summary so a future agent can continue without
reconstructing the whole chat.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from tools.base import Tool, ToolDefinition, ToolParameter, ToolResult, ToolStatus


class SessionCheckpointTool(Tool):
    def __init__(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.docs_dir = self.root / "docs"
        self.docs_dir.mkdir(parents=True, exist_ok=True)

    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="session_checkpoint",
            description=(
                "Save a compact session handoff into docs, conversation_learning, "
                "and ana_memory so the next agent can continue safely."
            ),
            parameters=[
                ToolParameter(name="title", description="Short checkpoint title", type="string", required=True),
                ToolParameter(name="summary", description="What happened in this session", type="string", required=True),
                ToolParameter(name="current_goal", description="Current project goal", type="string", required=False),
                ToolParameter(name="next_steps", description="Next steps, one per line or semicolon-separated", type="string", required=False),
                ToolParameter(name="files_changed", description="Changed files, one per line or semicolon-separated", type="string", required=False),
                ToolParameter(name="validation", description="Verification commands/results", type="string", required=False),
                ToolParameter(name="risks", description="Open risks or warnings", type="string", required=False),
                ToolParameter(name="sync_status", description="Lab/release sync status", type="string", required=False),
                ToolParameter(name="include_git", description="Include git status summary", type="boolean", required=False, default=True),
            ],
            category="memory",
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        title = str(kwargs.get("title") or "").strip()
        summary = str(kwargs.get("summary") or "").strip()
        if not title or not summary:
            return ToolResult(
                status=ToolStatus.ERROR,
                error="Parameters 'title' and 'summary' are required.",
            )

        checkpoint = self._build_checkpoint(kwargs)
        try:
            md_path = self._write_markdown(checkpoint)
            self._save_to_conversation_learning(checkpoint)
            self._save_to_ana_memory(checkpoint, md_path)
            self._write_latest_pointer(md_path, checkpoint)
        except Exception as exc:
            return ToolResult(status=ToolStatus.ERROR, error=str(exc))

        return ToolResult(
            status=ToolStatus.SUCCESS,
            data={
                "saved": True,
                "path": str(md_path),
                "topic": checkpoint["memory_topic"],
                "timestamp": checkpoint["timestamp"],
            },
            message=f"Session checkpoint saved: {md_path.name}",
        )

    def _build_checkpoint(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        safe_stamp = timestamp.replace(":", "").replace("+", "Z")
        title = str(kwargs.get("title") or "").strip()
        include_git = self._to_bool(kwargs.get("include_git", True))
        checkpoint = {
            "timestamp": timestamp,
            "safe_stamp": safe_stamp,
            "title": title,
            "summary": str(kwargs.get("summary") or "").strip(),
            "current_goal": str(kwargs.get("current_goal") or "").strip(),
            "next_steps": self._split_list(kwargs.get("next_steps")),
            "files_changed": self._split_list(kwargs.get("files_changed")),
            "validation": str(kwargs.get("validation") or "").strip(),
            "risks": self._split_list(kwargs.get("risks")),
            "sync_status": str(kwargs.get("sync_status") or "").strip(),
            "git": self._git_status() if include_git else {"included": False},
        }
        checkpoint["memory_topic"] = "session_checkpoint_" + safe_stamp.replace("-", "_")
        return checkpoint

    def _write_markdown(self, checkpoint: Dict[str, Any]) -> Path:
        filename = f"SESSION_CHECKPOINT_{checkpoint['safe_stamp']}.md"
        path = self.docs_dir / filename
        lines = [
            f"# Session Checkpoint - {checkpoint['timestamp']}",
            "",
            f"## {checkpoint['title']}",
            "",
            "## Summary",
            "",
            checkpoint["summary"],
            "",
        ]
        if checkpoint["current_goal"]:
            lines += ["## Current Goal", "", checkpoint["current_goal"], ""]
        lines += self._section_list("Next Steps", checkpoint["next_steps"])
        lines += self._section_list("Files Changed", checkpoint["files_changed"])
        if checkpoint["validation"]:
            lines += ["## Validation", "", "```text", checkpoint["validation"], "```", ""]
        lines += self._section_list("Risks", checkpoint["risks"])
        if checkpoint["sync_status"]:
            lines += ["## Lab/Release Sync Status", "", checkpoint["sync_status"], ""]
        git = checkpoint.get("git", {})
        if git.get("included"):
            lines += [
                "## Git Snapshot",
                "",
                f"- branch: {git.get('branch', 'unknown')}",
                f"- clean: {git.get('clean', False)}",
                "",
                "```text",
                git.get("status", "") or "clean",
                "```",
                "",
            ]
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    def _save_to_conversation_learning(self, checkpoint: Dict[str, Any]) -> None:
        from tools.conversation_learning_tool import ConversationLearningTool

        lesson = self._compact_text(checkpoint)
        result = ConversationLearningTool().execute(
            action="add",
            title=checkpoint["title"],
            category="session_checkpoint",
            problem="Session context can be lost when chat credit or agent session ends.",
            lesson=lesson,
            fix="Use session_checkpoint before handoff or when important decisions are made.",
            validation=checkpoint.get("validation", ""),
            source="session_checkpoint_tool",
            confidence="high",
            tags="handoff,checkpoint,memory,agent-continuity",
        )
        if not result.is_success:
            raise RuntimeError(result.error or "conversation_learning save failed")

    def _save_to_ana_memory(self, checkpoint: Dict[str, Any], md_path: Path) -> None:
        from tools.memory_tool import MemoryTool

        content = self._compact_text(checkpoint) + f"\n\nFull handoff: {md_path}"
        result = MemoryTool().execute(
            action="save_knowledge",
            topic=checkpoint["memory_topic"],
            content=content,
            category="session_checkpoint",
        )
        if not result.is_success:
            raise RuntimeError(result.error or "ana_memory save failed")

    def _write_latest_pointer(self, md_path: Path, checkpoint: Dict[str, Any]) -> None:
        latest = self.docs_dir / "CURRENT_SESSION_HANDOFF.md"
        latest.write_text(
            "\n".join(
                [
                    "# Current Session Handoff",
                    "",
                    f"Latest checkpoint: `{md_path.name}`",
                    f"Timestamp: {checkpoint['timestamp']}",
                    f"Memory topic: `{checkpoint['memory_topic']}`",
                    "",
                    "Open the checkpoint file for the full handoff.",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    def _git_status(self) -> Dict[str, Any]:
        root = self.root.parent
        data = {"included": True, "branch": "unknown", "status": "", "clean": False}
        try:
            branch = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=str(root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=5,
            )
            if branch.returncode == 0:
                data["branch"] = branch.stdout.strip()
            status = subprocess.run(
                ["git", "status", "--short"],
                cwd=str(root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=5,
            )
            if status.returncode == 0:
                data["status"] = status.stdout.strip()
                data["clean"] = not data["status"]
        except Exception as exc:
            data["error"] = str(exc)
        return data

    def _compact_text(self, checkpoint: Dict[str, Any]) -> str:
        parts = [
            f"Timestamp: {checkpoint['timestamp']}",
            f"Summary: {checkpoint['summary']}",
        ]
        if checkpoint["current_goal"]:
            parts.append(f"Current goal: {checkpoint['current_goal']}")
        if checkpoint["next_steps"]:
            parts.append("Next steps: " + "; ".join(checkpoint["next_steps"]))
        if checkpoint["sync_status"]:
            parts.append(f"Sync status: {checkpoint['sync_status']}")
        if checkpoint["risks"]:
            parts.append("Risks: " + "; ".join(checkpoint["risks"]))
        return "\n".join(parts)

    def _section_list(self, title: str, items: List[str]) -> List[str]:
        if not items:
            return []
        lines = [f"## {title}", ""]
        lines.extend(f"- {item}" for item in items)
        lines.append("")
        return lines

    def _split_list(self, value: Any) -> List[str]:
        if not value:
            return []
        if isinstance(value, list):
            raw_items = value
        else:
            text = str(value).replace("\r\n", "\n")
            sep = "\n" if "\n" in text else ";"
            raw_items = text.split(sep)
        return [str(item).strip(" -\t") for item in raw_items if str(item).strip(" -\t")]

    def _to_bool(self, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() not in {"0", "false", "no", "off"}
