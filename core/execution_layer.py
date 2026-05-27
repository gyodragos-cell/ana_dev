"""ANA MAX v22 execution layer scaffolding.

The execution layer is the boundary between routed tool decisions and actual
tool calls. This scaffold keeps the interface stable, normalizes raw tool
results, applies small output limits, and leaves policy, streaming, fallback,
and observability integrations for later v22 phases.
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib import request as url_request

from core.mcp_client import MCPClient, ToolEndpoint


DEFAULT_OUTPUT_LIMITS = {
    "max_text_bytes": 4096,
    "summary_bytes": 512,
}

DEFAULT_REDACTION_RULES = (
    "api_key",
    "token",
    "secret",
    "password",
)


def _utc_now() -> str:
    """Return an ISO-8601 UTC timestamp for audit-friendly records."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class ExecutionResult:
    """Normalized result returned by the execution layer."""

    tool: str
    success: bool
    data: Any = None
    summary: str = ""
    error: str | None = None
    output_bytes: int = 0
    latency_ms: float = 0.0
    truncated: bool = False
    started_at: str = ""
    ended_at: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe execution result."""
        return {
            "tool": self.tool,
            "success": self.success,
            "data": self.data,
            "summary": self.summary,
            "error": self.error,
            "output_bytes": self.output_bytes,
            "latency_ms": self.latency_ms,
            "truncated": self.truncated,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "metadata": dict(self.metadata),
        }


class ExecutionLayer:
    """Execute routed tools and normalize their outputs for v22."""

    def __init__(
        self,
        tool_registry: Any = None,
        output_limits: Mapping[str, int] | None = None,
        fallback_tools: tuple[str, ...] | None = None,
        tool_catalog: Mapping[str, ToolEndpoint | Mapping[str, Any]] | None = None,
        mcp_client: MCPClient | None = None,
        remote_client: Any = None,
        auto_repair: Any = None,
        observability: Any = None,
        safety_envelope: Mapping[str, Any] | None = None,
        network_transport: Any = None,
    ) -> None:
        """Initialize execution dependencies and output policies."""
        self.tool_registry = tool_registry
        self.fallback_tools = tuple(fallback_tools or ())
        self.tool_catalog = dict(tool_catalog or {})
        self.mcp_client = mcp_client
        self.remote_client = remote_client
        self.auto_repair = auto_repair
        self.observability = observability
        self.safety_envelope = dict(safety_envelope or {"safe_mode": True, "allow_mutation": False})
        self.network_transport = network_transport
        self.output_limits = dict(DEFAULT_OUTPUT_LIMITS)
        if output_limits:
            self.output_limits.update(output_limits)
        self.redaction_rules = tuple(DEFAULT_REDACTION_RULES)
        self.audit_events: list[dict[str, Any]] = []

    def execute(self, tool_name: str, arguments: Mapping[str, Any] | None = None) -> ExecutionResult:
        """Execute a tool through the injected registry and normalize output."""
        started_at = _utc_now()
        started = time.perf_counter()
        arguments = dict(arguments or {})
        self._record_audit_event("start", tool_name, arguments)

        try:
            raw_result = self._call_tool(tool_name, arguments)
            normalized = self._normalize_result(raw_result)
            if not normalized.get("success") and self.fallback_tools:
                normalized = self._execute_fallback(arguments, normalized)
            if not normalized.get("success") and self.auto_repair is not None:
                repair = self.auto_repair.plan_repair(
                    {
                        "tool": tool_name,
                        "error": normalized.get("error"),
                        "summary": normalized.get("summary"),
                        "backup_tool": self.fallback_tools[0] if self.fallback_tools else None,
                    }
                )
                normalized["repair_plan"] = repair.to_dict()
            limited = self._apply_output_limits(normalized)
            latency_ms = round((time.perf_counter() - started) * 1000, 3)
            result = ExecutionResult(
                tool=tool_name,
                success=limited["success"],
                data=limited.get("data"),
                summary=limited.get("summary", ""),
                error=limited.get("error"),
                output_bytes=limited.get("output_bytes", 0),
                latency_ms=latency_ms,
                truncated=limited.get("truncated", False),
                started_at=started_at,
                ended_at=_utc_now(),
                metadata={"executor": "v22_runtime", "fallback_used": bool(limited.get("fallback_used", False))},
            )
            self._record_audit_event("end", tool_name, {"success": result.success})
            if self.observability is not None:
                self.observability.record_event(
                    "execution_result",
                    {"tool_name": tool_name, "success": result.success, "latency_ms": result.latency_ms},
                )
            # TODO(v22): emit latency, output size, and success to observability.
            return result
        except Exception as error:  # pragma: no cover - defensive boundary
            handled = self._handle_error(error)
            result = ExecutionResult(
                tool=tool_name,
                success=False,
                summary=handled["summary"],
                error=handled["error"],
                latency_ms=round((time.perf_counter() - started) * 1000, 3),
                started_at=started_at,
                ended_at=_utc_now(),
                metadata={"executor": "v22_runtime", "handled_error": True},
            )
            self._record_audit_event("error", tool_name, {"error": result.error})
            return result

    def _normalize_result(self, raw_result: Any) -> dict[str, Any]:
        """Convert registry-specific output into a stable compact mapping."""
        if isinstance(raw_result, ExecutionResult):
            return raw_result.to_dict()
        if isinstance(raw_result, Mapping):
            data = raw_result.get("data")
            error = raw_result.get("error")
            success = bool(raw_result.get("success", error is None))
            summary = str(raw_result.get("summary") or raw_result.get("message") or "")
            return {
                "success": success,
                "data": data,
                "summary": self._redact(summary),
                "error": self._redact(str(error)) if error else None,
                "truncated": False,
            }
        status = getattr(raw_result, "status", None)
        error = getattr(raw_result, "error", None)
        data = getattr(raw_result, "data", raw_result)
        success = str(status).lower().endswith("success") if status is not None else error is None
        return {
            "success": success,
            "data": data,
            "summary": self._redact(str(getattr(raw_result, "message", ""))),
            "error": self._redact(str(error)) if error else None,
            "truncated": False,
        }

    def _apply_output_limits(self, result: Mapping[str, Any]) -> dict[str, Any]:
        """Apply byte limits and summarization placeholders to a result."""
        limited = dict(result)
        text = self._stringify_output(limited.get("data"))
        output_bytes = len(text.encode("utf-8", errors="replace"))
        limited["output_bytes"] = output_bytes
        limited.setdefault("truncated", False)

        max_bytes = int(self.output_limits.get("max_text_bytes", 4096))
        if output_bytes > max_bytes:
            limited = self._summarize_large_output(limited)
        return limited

    def _summarize_large_output(self, result: Mapping[str, Any]) -> dict[str, Any]:
        """Replace large output with a compact placeholder summary."""
        summarized = dict(result)
        text = self._stringify_output(summarized.get("data"))
        budget = int(self.output_limits.get("summary_bytes", 512))
        clipped = text[: max(0, budget - 18)].rstrip()
        summarized["data"] = None
        summarized["summary"] = self._redact(f"{clipped}... [summarized]")
        summarized["truncated"] = True
        # TODO(v22): use AIEngine.summarize for structured large-output summaries.
        # TODO(v22): support streaming output handling for long-running tools.
        return summarized

    def _handle_error(self, error: Exception) -> dict[str, str]:
        """Convert unexpected execution errors into compact safe errors."""
        message = self._redact(str(error) or error.__class__.__name__)
        return {
            "summary": "execution failed before a normalized tool result was returned",
            "error": message,
        }

    def _call_tool(self, tool_name: str, arguments: Mapping[str, Any]) -> Any:
        """Call a registry, mapping, or callable tool implementation."""
        endpoint = self._get_tool_endpoint(tool_name)
        if self.auto_repair is not None and hasattr(self.auto_repair, "is_disabled") and self.auto_repair.is_disabled(tool_name):
            return {"success": False, "error": f"tool temporarily disabled: {tool_name}", "data": None}
        capability_error = self._check_capability(endpoint, arguments)
        if capability_error:
            return {"success": False, "error": capability_error, "data": None}

        builtin = self._call_builtin_tool(endpoint.name, arguments)
        if builtin is not None:
            return builtin

        if endpoint.tool_type == "mcp":
            if self.mcp_client is None:
                return {"success": False, "error": "MCP client not configured", "data": None}
            if not endpoint.server_id:
                return {"success": False, "error": f"MCP server id missing for {tool_name}", "data": None}
            return self.mcp_client.call_tool(endpoint.server_id, tool_name, arguments)
        if endpoint.tool_type == "remote":
            if self.remote_client is None:
                return {"success": False, "error": "remote client not configured", "data": None}
            if hasattr(self.remote_client, "call_tool"):
                return self.remote_client.call_tool(endpoint.endpoint or tool_name, arguments)
            if callable(self.remote_client):
                return self.remote_client(endpoint.endpoint or tool_name, dict(arguments))
            return {"success": False, "error": "unsupported remote client", "data": None}

        if self.tool_registry is None:
            return {"success": False, "error": "no tool registry configured", "data": None}
        if hasattr(self.tool_registry, "execute"):
            return self.tool_registry.execute(tool_name, **dict(arguments))
        if hasattr(self.tool_registry, "call"):
            return self.tool_registry.call(tool_name, dict(arguments))
        if isinstance(self.tool_registry, Mapping):
            tool = self.tool_registry.get(tool_name)
            if callable(tool):
                return tool(**dict(arguments))
            return {"success": False, "error": f"tool not found: {tool_name}", "data": None}
        if callable(self.tool_registry):
            return self.tool_registry(tool_name, dict(arguments))
        return {"success": False, "error": "unsupported tool registry", "data": None}

    def _get_tool_endpoint(self, tool_name: str) -> ToolEndpoint:
        """Return a normalized tool endpoint descriptor."""
        raw = self.tool_catalog.get(tool_name)
        if isinstance(raw, ToolEndpoint):
            return raw
        if isinstance(raw, Mapping):
            return ToolEndpoint(
                name=str(raw.get("name") or tool_name),
                tool_type=str(raw.get("type") or raw.get("tool_type") or "local"),
                server_id=raw.get("server_id"),
                endpoint=raw.get("endpoint"),
                auth_ref=raw.get("auth_ref"),
                config=dict(raw.get("config") or {}),
            )
        return ToolEndpoint(name=tool_name, tool_type="local")

    def _check_capability(self, endpoint: ToolEndpoint, arguments: Mapping[str, Any]) -> str | None:
        """Enforce safe-mode, write-mode, subprocess, and network rules."""
        config = dict(endpoint.config or {})
        safe_mode = bool(self.safety_envelope.get("safe_mode", True))
        dev_mode = bool(self.safety_envelope.get("dev_mode", False))
        allow_mutation = bool(self.safety_envelope.get("allow_mutation", False))

        if safe_mode and config.get("safe_write"):
            return f"safe-mode blocked write tool: {endpoint.name}"
        if safe_mode and config.get("subprocess_allowed"):
            return f"safe-mode blocked subprocess tool: {endpoint.name}"
        if safe_mode and config.get("network_allowed"):
            return f"safe-mode blocked network tool: {endpoint.name}"
        if config.get("safe_write") and not (allow_mutation or dev_mode):
            return f"write-mode required for tool: {endpoint.name}"
        return None

    def _call_builtin_tool(self, tool_name: str, arguments: Mapping[str, Any]) -> dict[str, Any] | None:
        """Run built-in local live tools when explicitly routed."""
        if tool_name == "file_read":
            path = Path(str(arguments.get("path", ""))).expanduser()
            if not path.exists() or not path.is_file():
                return {"success": False, "error": f"file not found: {path}", "data": None}
            return {"success": True, "data": path.read_text(encoding="utf-8-sig", errors="replace"), "summary": "file read"}

        if tool_name == "file_write":
            path = Path(str(arguments.get("path", ""))).expanduser()
            content = str(arguments.get("content", ""))
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return {"success": True, "data": {"path": str(path), "bytes": len(content.encode("utf-8"))}, "summary": "file written"}

        if tool_name == "subprocess_exec":
            command = arguments.get("command")
            if isinstance(command, str):
                command_args = command.split()
            elif isinstance(command, list):
                command_args = [str(item) for item in command]
            else:
                return {"success": False, "error": "command must be a string or list", "data": None}
            completed = subprocess.run(command_args, capture_output=True, text=True, timeout=10, check=False)
            return {
                "success": completed.returncode == 0,
                "data": {"stdout": completed.stdout, "stderr": completed.stderr, "returncode": completed.returncode},
                "summary": "subprocess completed",
                "error": completed.stderr if completed.returncode else None,
            }

        if tool_name == "network_get":
            url = str(arguments.get("url", ""))
            if self.network_transport is not None:
                return self.network_transport(url)
            with url_request.urlopen(url, timeout=5) as response:
                body = response.read().decode("utf-8", errors="replace")
            return {"success": True, "data": body, "summary": "network get completed"}

        return None

    def _execute_fallback(self, arguments: Mapping[str, Any], previous: Mapping[str, Any]) -> dict[str, Any]:
        """Try configured fallback tools until one succeeds."""
        attempts = [dict(previous)]
        for fallback in self.fallback_tools:
            raw = self._call_tool(fallback, arguments)
            normalized = self._normalize_result(raw)
            attempts.append(normalized)
            if normalized.get("success"):
                result = dict(normalized)
                result["fallback_used"] = True
                result["fallback_tool"] = fallback
                result["fallback_attempts"] = len(attempts)
                return result
        result = dict(previous)
        result["fallback_used"] = bool(self.fallback_tools)
        result["fallback_attempts"] = len(attempts)
        return result

    def _record_audit_event(self, event: str, tool_name: str, payload: Mapping[str, Any]) -> None:
        """Record a compact in-memory audit event placeholder."""
        self.audit_events.append(
            {
                "event": event,
                "tool": tool_name,
                "payload_keys": sorted(str(key) for key in payload.keys()),
                "created_at": _utc_now(),
            }
        )

    def _redact(self, text: str) -> str:
        """Apply simple placeholder redaction rules to text."""
        redacted = text
        for marker in self.redaction_rules:
            redacted = redacted.replace(marker, "[redacted]")
        return redacted

    @staticmethod
    def _stringify_output(value: Any) -> str:
        """Convert output values into text for byte counting and summaries."""
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        return str(value)
