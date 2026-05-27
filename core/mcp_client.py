"""Safe MCP client abstraction for ANA MAX v23 development.

The client is disabled by default. Tests can inject fake transports, while real
HTTP/MCP calls require explicit configuration. Secrets are never hardcoded.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping
from urllib import error as url_error
from urllib import request as url_request


Transport = Callable[[str, Mapping[str, Any], float], Mapping[str, Any]]


@dataclass(frozen=True)
class MCPServerConfig:
    """Connection config for one MCP server."""

    server_id: str
    endpoint: str = ""
    enabled: bool = False
    timeout_seconds: float = 5.0
    retries: int = 0
    auth_ref: str | None = None
    capabilities: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolEndpoint:
    """Describe where a tool should execute."""

    name: str
    tool_type: str = "local"
    server_id: str | None = None
    endpoint: str | None = None
    auth_ref: str | None = None
    config: Mapping[str, Any] = field(default_factory=dict)


class MCPClient:
    """Call MCP tools through configured servers with normalized errors."""

    def __init__(
        self,
        servers: Mapping[str, MCPServerConfig] | None = None,
        transport: Transport | None = None,
    ) -> None:
        """Initialize server map and optional fake transport."""
        self.servers = dict(servers or {})
        self.transport = transport or self._http_transport

    def call_tool(self, server_id: str, tool_name: str, arguments: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """Call a configured MCP server tool and normalize the response."""
        config = self.servers.get(server_id)
        if config is None:
            return self._error(tool_name, f"unknown MCP server: {server_id}")
        if not config.enabled:
            return self._error(tool_name, f"MCP server disabled: {server_id}")

        payload = {
            "jsonrpc": "2.0",
            "id": f"ana-{int(time.time() * 1000)}",
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": dict(arguments or {})},
        }
        attempts = max(0, int(config.retries)) + 1
        last_error = ""
        for _ in range(attempts):
            try:
                raw = self.transport(config.endpoint, payload, float(config.timeout_seconds))
                return self._normalize_response(tool_name, raw)
            except TimeoutError as error:
                last_error = f"timeout: {error}"
            except Exception as error:  # pragma: no cover - defensive transport edge
                last_error = str(error)
        return self._error(tool_name, last_error or "MCP call failed")

    def get_capability_map(self) -> dict[str, dict[str, str]]:
        """Return per-server capability mapping for routing."""
        return {server_id: dict(config.capabilities) for server_id, config in self.servers.items()}

    def _normalize_response(self, tool_name: str, raw: Mapping[str, Any]) -> dict[str, Any]:
        """Normalize JSON-RPC or compact fake responses."""
        if "error" in raw and raw["error"]:
            return self._error(tool_name, str(raw["error"]))
        result = raw.get("result", raw)
        if not isinstance(result, Mapping):
            return self._error(tool_name, "invalid MCP response shape")
        if "content" in result:
            return {"success": True, "data": result["content"], "summary": f"MCP tool {tool_name} completed"}
        success = bool(result.get("success", True))
        return {
            "success": success,
            "data": result.get("data", result),
            "summary": str(result.get("summary") or result.get("message") or f"MCP tool {tool_name} completed"),
            "error": result.get("error"),
        }

    @staticmethod
    def _http_transport(endpoint: str, payload: Mapping[str, Any], timeout_seconds: float) -> Mapping[str, Any]:
        """Perform a minimal JSON HTTP POST transport."""
        if not endpoint:
            raise ValueError("MCP endpoint is not configured")
        req = url_request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with url_request.urlopen(req, timeout=timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8", errors="replace"))
        except url_error.URLError as error:
            if "timed out" in str(error).lower():
                raise TimeoutError(str(error)) from error
            raise

    @staticmethod
    def _error(tool_name: str, message: str) -> dict[str, Any]:
        """Build a normalized MCP error result."""
        return {"success": False, "tool": tool_name, "data": None, "summary": "MCP call failed", "error": message}


__all__ = ["MCPClient", "MCPServerConfig", "ToolEndpoint"]
