"""Memory manager tests."""

from core.memory_manager import MemoryManager


def test_memory_save_load(tmp_path):
    """Memory manager should persist semantic and episodic memory."""
    path = tmp_path / "memory.json"
    memory = MemoryManager(path)
    memory.save_semantic("grep_file", "best for file search")
    memory.save_episode("search files", "grep_file worked")
    memory.save()

    loaded = MemoryManager(path)
    loaded.load()

    assert "grep_file" in loaded.semantic
    assert loaded.episodic[0].metadata["task"] == "search files"


def test_memory_influence_on_routing_context():
    """Memory injection should surface relevant semantic memories."""
    memory = MemoryManager()
    memory.save_semantic("grep_file", "best for file search")

    context = memory.inject_context("grep_file should search")

    assert context["semantic_hits"][0]["key"] == "grep_file"
