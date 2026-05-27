"""Optimization snapshot persistence tests."""

import pytest

from core.optimization_snapshot import OptimizationSnapshotManager, OptimizationSnapshotRecord


def test_snapshot_save_load(tmp_path):
    """Snapshot manager should save and load dev-local JSON."""
    manager = OptimizationSnapshotManager(tmp_path)
    record = OptimizationSnapshotRecord(
        reliability={"grep_file": 0.9},
        noise={"grep_file": 0.1},
        latency={"grep_file": 12.0},
        failure_streak={"grep_file": 0},
        scenario_effectiveness={"file_search": {"calls": 1, "successes": 1}},
    )

    path = manager.save_snapshot("latest", record)
    loaded = manager.load_snapshot("latest")

    assert path.exists()
    assert loaded["reliability"]["grep_file"] == 0.9


def test_snapshot_blocks_public_release_in_safe_mode():
    """Safe-mode should reject public release snapshot roots."""
    manager = OptimizationSnapshotManager("C:/Users/billy/Desktop/ANA_MAX_GitHub_Release")

    with pytest.raises(PermissionError):
        manager.save_snapshot("bad", OptimizationSnapshotRecord())
