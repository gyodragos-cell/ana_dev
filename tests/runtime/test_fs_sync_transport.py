"""Tests for filesystem sync over transport."""

from pathlib import Path

from core.fs_sync import FSSync


class FakeTransport:
    """In-memory transport for FS sync tests."""

    def __init__(self):
        """Initialize sent envelope storage."""
        self.sent = []

    def send(self, envelope):
        """Record one envelope."""
        self.sent.append(envelope)


def test_write_file_broadcasts_fs_update_when_transport_set(tmp_path):
    """write_file should broadcast fs.update when transport is configured."""
    transport = FakeTransport()
    fs_sync = FSSync(root_path=str(tmp_path), transport=transport, node_id="n1")
    fs_sync.write_file("a.txt", "hello")
    assert len(transport.sent) >= 1
    envelope = transport.sent[-1]
    assert envelope["type"] == "fs.update"
    assert envelope["payload"]["path"].endswith("a.txt")


def test_delete_file_broadcasts_fs_delete_when_transport_set(tmp_path):
    """delete_file should broadcast fs.delete when transport is configured."""
    transport = FakeTransport()
    fs_sync = FSSync(root_path=str(tmp_path), transport=transport, node_id="n1")
    fs_sync.write_file("a.txt", "hello")
    fs_sync.delete_file("a.txt")
    assert transport.sent[-1]["type"] == "fs.delete"


def test_write_file_without_transport_still_writes_locally(tmp_path):
    """write_file should work locally without transport."""
    fs_sync = FSSync(root_path=str(tmp_path), transport=None)
    fs_sync.write_file("a.txt", "hello")
    assert (tmp_path / "a.txt").read_text(encoding="utf-8") == "hello"


def test_handle_remote_update_creates_file_if_missing(tmp_path):
    """Remote fs.update should create missing files."""
    fs_sync = FSSync(root_path=str(tmp_path), transport=None)
    envelope = {
        "version": 1,
        "type": "fs.update",
        "source_node": "n2",
        "target_node": "n0",
        "timestamp": "2025-01-01T00:00:00Z",
        "payload": {
            "path": "b.txt",
            "content": "world",
            "mtime": "2025-01-01T00:00:00Z",
            "node_id": "n2",
        },
    }
    fs_sync.handle_fs_message(envelope)
    assert (tmp_path / "b.txt").read_text(encoding="utf-8") == "world"


def test_handle_remote_delete_removes_file_if_newer(tmp_path):
    """Remote fs.delete should remove files when remote mtime wins."""
    fs_sync = FSSync(root_path=str(tmp_path), transport=None)
    Path(tmp_path / "c.txt").write_text("old", encoding="utf-8")
    envelope = {
        "version": 1,
        "type": "fs.delete",
        "source_node": "n2",
        "target_node": "n0",
        "timestamp": "2999-01-01T00:00:00Z",
        "payload": {"path": "c.txt", "mtime": "2999-01-01T00:00:00Z", "node_id": "n2"},
    }
    fs_sync.handle_fs_message(envelope)
    assert not (tmp_path / "c.txt").exists()


def test_request_full_fs_sync_sends_pull_request(tmp_path):
    """request_full_fs_sync should send fs.pull_request."""
    transport = FakeTransport()
    fs_sync = FSSync(root_path=str(tmp_path), transport=transport, node_id="n1")
    fs_sync.request_full_fs_sync("n0")
    assert len(transport.sent) == 1
    assert transport.sent[0]["type"] == "fs.pull_request"
    assert transport.sent[0]["target_node"] == "n0"
