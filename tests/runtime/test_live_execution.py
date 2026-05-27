"""Live execution tests remain sandboxed and local."""

import sys

from core.execution_layer import ExecutionLayer


def test_safe_mode_blocks_write_subprocess_and_network(tmp_path):
    """Safe-mode should block mutating and external live tools."""
    catalog = {
        "file_write": {"type": "local", "config": {"safe_write": True}},
        "subprocess_exec": {"type": "local", "config": {"subprocess_allowed": True}},
        "network_get": {"type": "local", "config": {"network_allowed": True}},
    }
    layer = ExecutionLayer(tool_catalog=catalog, safety_envelope={"safe_mode": True})

    assert layer.execute("file_write", {"path": str(tmp_path / "x.txt"), "content": "x"}).success is False
    assert layer.execute("subprocess_exec", {"command": [sys.executable, "--version"]}).success is False
    assert layer.execute("network_get", {"url": "https://example.test"}).success is False


def test_file_read_write_in_write_mode(tmp_path):
    """Controlled write-mode should allow local file write and read."""
    catalog = {
        "file_write": {"type": "local", "config": {"safe_write": True}},
        "file_read": {"type": "local", "config": {"safe_read": True}},
    }
    layer = ExecutionLayer(tool_catalog=catalog, safety_envelope={"safe_mode": False, "allow_mutation": True})
    path = tmp_path / "note.txt"

    write = layer.execute("file_write", {"path": str(path), "content": "hello"}).to_dict()
    read = layer.execute("file_read", {"path": str(path)}).to_dict()

    assert write["success"] is True
    assert read["data"] == "hello"


def test_subprocess_execution_in_dev_mode():
    """Dev-mode should allow controlled subprocess execution."""
    layer = ExecutionLayer(
        tool_catalog={"subprocess_exec": {"type": "local", "config": {"subprocess_allowed": True}}},
        safety_envelope={"safe_mode": False, "dev_mode": True},
    )

    result = layer.execute("subprocess_exec", {"command": [sys.executable, "--version"]}).to_dict()

    assert result["success"] is True
    assert "Python" in result["data"]["stdout"] or "Python" in result["data"]["stderr"]


def test_network_call_mock_in_dev_mode():
    """Network live tool should use injected transport in tests."""
    layer = ExecutionLayer(
        tool_catalog={"network_get": {"type": "local", "config": {"network_allowed": True}}},
        safety_envelope={"safe_mode": False, "dev_mode": True},
        network_transport=lambda url: {"success": True, "data": f"mock:{url}", "summary": "mock network"},
    )

    result = layer.execute("network_get", {"url": "https://example.test"}).to_dict()

    assert result["success"] is True
    assert result["data"] == "mock:https://example.test"
