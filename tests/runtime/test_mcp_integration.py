"""MCP integration tests use fake transports only."""

from core.execution_layer import ExecutionLayer
from core.mcp_client import MCPClient, MCPServerConfig, ToolEndpoint


def test_mcp_success_scenario():
    """MCP client should normalize a fake JSON-RPC success response."""
    client = MCPClient(
        {"fake": MCPServerConfig(server_id="fake", endpoint="mock://fake", enabled=True)},
        transport=lambda endpoint, payload, timeout: {"result": {"success": True, "data": {"ok": True}}},
    )
    layer = ExecutionLayer(
        tool_catalog={"mcp_tool": ToolEndpoint(name="mcp_tool", tool_type="mcp", server_id="fake")},
        mcp_client=client,
    )

    result = layer.execute("mcp_tool", {"value": 1}).to_dict()

    assert result["success"] is True
    assert result["data"]["ok"] is True


def test_mcp_timeout_scenario():
    """MCP client should normalize fake timeout errors."""
    def timeout_transport(endpoint, payload, timeout):
        raise TimeoutError("fake timeout")

    client = MCPClient(
        {"fake": MCPServerConfig(server_id="fake", endpoint="mock://fake", enabled=True)},
        transport=timeout_transport,
    )

    result = client.call_tool("fake", "slow_tool", {})

    assert result["success"] is False
    assert "timeout" in result["error"]


def test_mcp_invalid_response_scenario():
    """MCP client should reject invalid response shapes."""
    client = MCPClient(
        {"fake": MCPServerConfig(server_id="fake", endpoint="mock://fake", enabled=True)},
        transport=lambda endpoint, payload, timeout: {"result": "bad"},
    )

    result = client.call_tool("fake", "bad_tool", {})

    assert result["success"] is False
    assert "invalid" in result["error"]


def test_mcp_disabled_by_default():
    """MCP servers should be disabled unless explicitly enabled."""
    client = MCPClient({"fake": MCPServerConfig(server_id="fake", endpoint="mock://fake")})

    result = client.call_tool("fake", "tool", {})

    assert result["success"] is False
    assert "disabled" in result["error"]
