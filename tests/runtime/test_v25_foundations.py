"""Tests for ANA MAX v25 foundation modules."""

import pytest

from core.audit_trail import AuditTrail
from core.auto_tuning import AutoTuningEngine
from core.deployment_prep import DeploymentPrep
from core.memory_engine import MemoryEngine
from core.policy_engine import PolicyEngine
from core.profiling_engine import ProfilingEngine
from core.self_diagnostic import SelfDiagnosticEngine
from core.workspace_manager import WorkspaceManager


def test_memory_engine_save_load_and_prune(tmp_path):
    """Memory engine should persist, search, and prune records."""
    path = tmp_path / "memory.json"
    memory = MemoryEngine(path)
    memory.add_semantic("grep_file", "grep_file is best for file search")
    memory.add_episode("search", "grep_file worked")
    assert memory.search("file search")
    assert memory.router_score("grep_file", "file search") > 0
    memory.save()
    loaded = MemoryEngine(path)
    loaded.load()
    loaded.prune(min_score=0.99)
    assert "grep_file" not in loaded.semantic or loaded.semantic["grep_file"].score < 1.0


def test_workspace_switching_and_isolation(tmp_path):
    """Workspace manager should switch and enforce isolation."""
    manager = WorkspaceManager()
    one = tmp_path / "one"
    two = tmp_path / "two"
    one.mkdir()
    two.mkdir()
    manager.register_workspace("one", one)
    manager.register_workspace("two", two)
    manager.switch_workspace("two")
    assert manager.route_context()["workspace"]["workspace_id"] == "two"
    assert manager.enforce_isolation(two / "file.txt") is True
    assert manager.enforce_isolation(one / "file.txt") is False


def test_policy_enforcement_and_dev_override():
    """Policy engine should block safe-mode risks and allow dev override."""
    safe = PolicyEngine(safe_mode=True)
    assert safe.evaluate("write", {"safe_write": True}).allowed is False
    dev = PolicyEngine(safe_mode=True, dev_mode=True)
    assert dev.evaluate("write", {"safe_write": True}).allowed is True


def test_audit_write_read_and_redaction(tmp_path):
    """Audit trail should persist redacted events."""
    path = tmp_path / "audit.json"
    audit = AuditTrail(path)
    audit.record("tool_call", {"tool": "x", "token": "secret"})
    audit.save()
    loaded = audit.load()
    assert loaded[0]["payload"]["token"] == "[redacted]"


def test_audit_safe_mode_blocks_public_path():
    """Audit trail should reject public release writes in safe-mode."""
    audit = AuditTrail("C:/Users/billy/Desktop/ANA_MAX_GitHub_Release/audit.json")
    with pytest.raises(PermissionError):
        audit.save()


def test_profiling_snapshot_and_optimization_feedback():
    """Profiling should expose latency feedback."""
    profiler = ProfilingEngine()
    profiler.record_tool_latency("grep_file", 12)
    profiler.record_routing_overhead(2)
    profiler.record_scenario_cost("safe", 1)
    assert profiler.snapshot()["tool_latency"]["grep_file"]["count"] == 1
    assert profiler.optimization_feedback()["grep_file"]["avg_latency_ms"] == 12


def test_auto_tuning_respects_policy():
    """Auto tuning should adjust weights and keep risk conservative in safe-mode."""
    tuned = AutoTuningEngine(PolicyEngine(safe_mode=True)).tune(
        {"risk": -0.1, "reliability": 0.2, "noise": -0.1, "latency": -0.05, "scenario_fit": 0.1},
        {"failure_rate": 0.4, "noise": 0.5, "latency_ms": 2000},
    )
    assert tuned["reliability"] > 0.2
    assert tuned["risk"] <= -0.25


def test_self_diagnostic_triggers():
    """Self diagnostics should detect slow tools and failures."""
    report = SelfDiagnosticEngine().diagnose(
        {"tool_stats": {"x": {"avg_latency_ms": 2000, "failure_streak": 3}}, "policy_events": [{"allowed": False}]}
    )
    assert report["status"] == "degraded"
    assert len(report["issues"]) >= 2


def test_deployment_prep_safe_exports():
    """Deployment prep should redact config and block memory in safe-mode."""
    prep = DeploymentPrep(safe_mode=True)
    assert "token" not in prep.export_config({"token": "x", "mode": "dev"})
    with pytest.raises(PermissionError):
        prep.export_memory({"semantic": {}})
