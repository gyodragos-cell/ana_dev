"""Semantic filesystem abstraction for ANA MAX AI OS."""

from __future__ import annotations

from typing import Any


class SemanticFS:
    """Memory-backed virtual filesystem with simple semantic lookup."""

    def __init__(self) -> None:
        """Initialize virtual files and mounts."""
        self.files: dict[str, str] = {}
        self.metadata: dict[str, dict[str, Any]] = {}
        self.mounts: dict[str, list[str]] = {}

    def write(self, path: str, content: str, tags: list[str] | None = None, metadata: dict[str, Any] | None = None) -> None:
        """Write a virtual file."""
        self.files[path] = content
        self.metadata[path] = {"tags": list(tags or []), **dict(metadata or {})}

    def read(self, path: str) -> str:
        """Read a virtual file."""
        return self.files[path]

    def search(self, query: str) -> list[dict[str, Any]]:
        """Search virtual files by substring."""
        q = query.lower()
        return [
            {"path": path, "content": content, "metadata": dict(self.metadata.get(path, {}))}
            for path, content in self.files.items()
            if q in path.lower()
            or q in content.lower()
            or q in " ".join(self.metadata.get(path, {}).get("tags", [])).lower()
        ]

    def search_by_tag(self, tag: str) -> list[dict[str, Any]]:
        """Search virtual files by tag."""
        wanted = tag.lower()
        return [
            {"path": path, "content": self.files[path], "metadata": dict(meta)}
            for path, meta in self.metadata.items()
            if wanted in [str(item).lower() for item in meta.get("tags", [])]
        ]

    def mount_tool_dir(self, name: str, paths: list[str]) -> None:
        """Mount virtual paths for a tool."""
        self.mounts[name] = list(paths)


__all__ = ["SemanticFS"]
