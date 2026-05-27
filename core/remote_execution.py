"""Remote execution layer for ANA MAX AI OS dev mode."""

from __future__ import annotations

import concurrent.futures
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Protocol


RemoteTransport = Callable[[str, str, Mapping[str, Any]], Mapping[str, Any]]


class RemoteExecutor(Protocol):
    """Protocol for pluggable remote execution backends."""

    def call(self, node_id: str, tool_name: str, arguments: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """Execute one tool call on a target node."""


@dataclass(frozen=True)
class RemoteCallResult:
    """Normalized remote call result."""

    success: bool
    tool: str
    node: str
    data: Mapping[str, Any]
    attempts: int = 1
    fallback_used: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe remote call result."""
        return {
            "success": self.success,
            "tool": self.tool,
            "node": self.node,
            "data": dict(self.data),
            "attempts": self.attempts,
            "fallback_used": self.fallback_used,
        }


class InProcessRemoteBackend:
    """In-process backend that simulates a remote node without network calls."""

    def __init__(self, handlers: Mapping[str, Callable[[Mapping[str, Any]], Mapping[str, Any]]] | None = None) -> None:
        """Initialize local fake node handlers."""
        self.handlers = dict(handlers or {})

    def execute(self, node_id: str, tool_name: str, arguments: Mapping[str, Any]) -> dict[str, Any]:
        """Execute a handler as if it lived on a remote node."""
        handler = self.handlers.get(tool_name)
        if handler is None:
            return {"success": True, "node": node_id, "tool": tool_name, "data": dict(arguments)}
        return dict(handler(arguments))


class RemoteExecution:
    """Execute remote tools with timeout, retry, and local fallback."""

    def __init__(
        self,
        transport: RemoteTransport | None = None,
        local_fallback: Any = None,
        retries: int = 0,
        timeout_seconds: float = 2.0,
    ) -> None:
        """Initialize remote execution."""
        backend = InProcessRemoteBackend()
        self.transport = transport or backend.execute
        self.local_fallback = local_fallback
        self.retries = retries
        self.timeout_seconds = timeout_seconds

    def call(self, node_id: str, tool_name: str, arguments: Mapping[str, Any] | None = None, capabilities: Mapping[str, bool] | None = None) -> dict[str, Any]:
        """Call a remote tool and fallback locally if configured."""
        args = dict(arguments or {})
        caps = dict(capabilities or {})
        attempts = self.retries + 1
        last_error = ""
        for attempt in range(1, attempts + 1):
            try:
                result = self._call_with_timeout(node_id, tool_name, args)
                if result.get("success", False):
                    result["capabilities"] = caps
                    result["attempts"] = attempt
                    result.setdefault("fallback_used", False)
                    return result
                last_error = str(result.get("error", "remote call failed"))
            except Exception as error:
                last_error = str(error)
        if self.local_fallback is not None:
            fallback = dict(self.local_fallback(tool_name, args))
            fallback.setdefault("success", True)
            fallback["fallback_used"] = True
            fallback["attempts"] = attempts
            return fallback
        return {"success": False, "error": last_error, "tool": tool_name, "node": node_id}

    def _call_with_timeout(self, node_id: str, tool_name: str, args: Mapping[str, Any]) -> dict[str, Any]:
        """Run one transport call with a local timeout guard."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self.transport, node_id, tool_name, args)
            try:
                return dict(future.result(timeout=self.timeout_seconds))
            except concurrent.futures.TimeoutError:
                return {"success": False, "error": "remote call timed out", "tool": tool_name, "node": node_id}

__all__ = ["InProcessRemoteBackend", "RemoteCallResult", "RemoteExecution", "RemoteExecutor"]
