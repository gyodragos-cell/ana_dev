"""Tests for live MCP behavior freshness checker."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "ana_live_behavior_check.py"
EXPECTED_CONTEXT_TOP = "ANA_MAX/dev_artifacts/scripts/ana_autonomy_runner.py"


def live_agent_coach_payload(signals=None):
    return {
        "success": True,
        "data": {
            "coach": {
                "signals": signals or [],
            },
        },
    }


def live_context_generated_noise_payload(code_results=None, graph_results=None):
    return {
        "success": True,
        "data": {
            "code_map": {
                "results": code_results or [{"file": EXPECTED_CONTEXT_TOP}],
            },
            "graph_map": {
                "results": graph_results or [
                    {"kind": "file", "name": EXPECTED_CONTEXT_TOP, "neighbors": []}
                ],
            },
        },
    }


def load_script():
    script_dir = str(SCRIPT.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location("ana_live_behavior_check", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module.call_live_agent_coach_monitor_filter = lambda mcp_url, timeout=30: live_agent_coach_payload()
    module.call_live_context_generated_noise_filter = (
        lambda mcp_url, timeout=30: live_context_generated_noise_payload()
    )
    return module


def live_radar_payload(runtime: int = 65, include_summary: bool = True):
    data = {"findings": [{"kind": "large_dirty_tree", "severity": "medium", "source": "git", "details": {"runtime": runtime}}]}
    if include_summary:
        data["summary"] = {
            "by_severity": {"medium": 1},
            "by_kind": {"large_dirty_tree": 1},
            "by_source": {"git": 1},
            "top_kind": "large_dirty_tree",
            "top_severity": "medium",
            "top_source": "git",
        }
    return {"success": True, "data": data}


def test_live_behavior_passes_when_identity_fields_are_present(monkeypatch):
    script = load_script()
    monkeypatch.setattr(script, "call_live_session_trust", lambda mcp_url, timeout=30: {
        "success": True,
        "message": "Gata cu 100% incredere.",
        "data": {
            "trust": {
                "score": 100,
                "signals": {"identity_surface_status": "PASS"},
            },
            "identity_surface": {"status": "PASS"},
        },
    })
    monkeypatch.setattr(script, "call_live_error_radar", lambda mcp_url, timeout=30: live_radar_payload())
    monkeypatch.setattr(script, "call_live_code_context_query_alias", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "code_map": {"query": "operator status reload behavior"},
            "compressed_state": {"goal": "operator status reload behavior"},
        },
    })
    monkeypatch.setattr(script, "call_live_code_context_graph_preference", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "code_map": {
                "results": [{"file": "ANA_MAX/dev_artifacts/scripts/ana_operator_status.py"}]
            }
        },
    })
    monkeypatch.setattr(script, "call_live_code_context_graph_limit_one", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "code_map": {
                "results": [{"file": "ANA_MAX/dev_artifacts/scripts/ana_operator_status.py"}]
            }
        },
    })
    monkeypatch.setattr(script, "disk_error_radar_runtime_count", lambda: 65)

    report = script.build_report()

    assert report["status"] == "PASS"
    assert report["checks"]["session_audit_identity_surface_field"] is True
    assert report["checks"]["session_audit_identity_signal"] is True
    assert report["checks"]["code_context_query_alias"] is True
    assert report["checks"]["code_context_graph_preference"] is True
    assert report["checks"]["code_context_graph_limit_one"] is True
    assert report["checks"]["error_radar_runtime_breakdown"] is True
    assert report["checks"]["error_radar_summary"] is True
    assert report["checks"]["agent_coach_monitor_noise_filter"] is True
    assert report["checks"]["context_generated_memory_noise_filter"] is True
    assert report["agent_coach"]["known_monitor_noise"] == []
    assert report["context_generated_memory_noise"]["top_file"] == EXPECTED_CONTEXT_TOP


def test_live_behavior_warns_when_agent_coach_monitor_noise_filter_is_stale(monkeypatch):
    script = load_script()
    monkeypatch.setattr(script, "call_live_session_trust", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "trust": {"score": 100, "signals": {"identity_surface_status": "PASS"}},
            "identity_surface": {"status": "PASS"},
        },
    })
    monkeypatch.setattr(script, "call_live_error_radar", lambda mcp_url, timeout=30: live_radar_payload())
    monkeypatch.setattr(script, "call_live_code_context_query_alias", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "code_map": {"query": "operator status reload behavior"},
            "compressed_state": {"goal": "operator status reload behavior"},
        },
    })
    monkeypatch.setattr(script, "call_live_code_context_graph_preference", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "code_map": {
                "results": [{"file": "ANA_MAX/dev_artifacts/scripts/ana_operator_status.py"}]
            }
        },
    })
    monkeypatch.setattr(script, "call_live_code_context_graph_limit_one", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "code_map": {
                "results": [{"file": "ANA_MAX/dev_artifacts/scripts/ana_operator_status.py"}]
            }
        },
    })
    monkeypatch.setattr(script, "call_live_agent_coach_monitor_filter", lambda mcp_url, timeout=30: live_agent_coach_payload([
        {
            "type": "repeated_error",
            "tool": "router_failure_demo",
            "count": 4,
            "error": "demo failure",
        }
    ]))
    monkeypatch.setattr(script, "disk_error_radar_runtime_count", lambda: 65)

    report = script.build_report()

    assert report["status"] == "WARN"
    assert report["checks"]["agent_coach_monitor_noise_filter"] is False
    assert report["agent_coach"]["known_monitor_noise"][0]["tool"] == "router_failure_demo"


def test_live_behavior_warns_when_context_generated_memory_noise_filter_is_stale(monkeypatch):
    script = load_script()
    monkeypatch.setattr(script, "call_live_session_trust", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "trust": {"score": 100, "signals": {"identity_surface_status": "PASS"}},
            "identity_surface": {"status": "PASS"},
        },
    })
    monkeypatch.setattr(script, "call_live_error_radar", lambda mcp_url, timeout=30: live_radar_payload())
    monkeypatch.setattr(script, "call_live_code_context_query_alias", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "code_map": {"query": "operator status reload behavior"},
            "compressed_state": {"goal": "operator status reload behavior"},
        },
    })
    monkeypatch.setattr(script, "call_live_code_context_graph_preference", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "code_map": {
                "results": [{"file": "ANA_MAX/dev_artifacts/scripts/ana_operator_status.py"}]
            }
        },
    })
    monkeypatch.setattr(script, "call_live_code_context_graph_limit_one", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "code_map": {
                "results": [{"file": "ANA_MAX/dev_artifacts/scripts/ana_operator_status.py"}]
            }
        },
    })
    monkeypatch.setattr(script, "call_live_context_generated_noise_filter", lambda mcp_url, timeout=30: live_context_generated_noise_payload(
        code_results=[
            {"file": "ANA_MAX/docs/SESSION_CHECKPOINT_2026-06-01T000000Z0000.md"},
            {"file": EXPECTED_CONTEXT_TOP},
        ],
        graph_results=[
            {
                "kind": "keyword",
                "name": "next",
                "neighbors": [
                    {"name": "ANA_MAX/archives/security_research/README.md"},
                ],
            }
        ],
    ))
    monkeypatch.setattr(script, "disk_error_radar_runtime_count", lambda: 65)

    report = script.build_report()

    assert report["status"] == "WARN"
    assert report["checks"]["context_generated_memory_noise_filter"] is False
    assert report["context_generated_memory_noise"]["top_file_ok"] is False
    assert report["context_generated_memory_noise"]["noisy_code_files"]
    assert report["context_generated_memory_noise"]["noisy_graph_neighbors"]


def test_live_behavior_warns_when_live_session_audit_is_stale(monkeypatch, capsys):
    script = load_script()
    monkeypatch.setattr(script, "call_live_session_trust", lambda mcp_url, timeout=30: {
        "success": True,
        "message": "Gata cu 72% incredere.",
        "data": {
            "trust": {
                "score": 72,
                "signals": {"has_code_context_pack": False},
            },
        },
    })
    monkeypatch.setattr(script, "call_live_error_radar", lambda mcp_url, timeout=30: live_radar_payload())
    monkeypatch.setattr(script, "call_live_code_context_query_alias", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "code_map": {"query": "operator status reload behavior"},
            "compressed_state": {"goal": "operator status reload behavior"},
        },
    })
    monkeypatch.setattr(script, "call_live_code_context_graph_preference", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "code_map": {
                "results": [{"file": "ANA_MAX/dev_artifacts/scripts/ana_operator_status.py"}]
            }
        },
    })
    monkeypatch.setattr(script, "call_live_code_context_graph_limit_one", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "code_map": {
                "results": [{"file": "ANA_MAX/dev_artifacts/scripts/ana_operator_status.py"}]
            }
        },
    })
    monkeypatch.setattr(script, "disk_error_radar_runtime_count", lambda: 65)

    code = script.main([])

    output = capsys.readouterr().out
    assert code == 1
    assert "ANA Live Behavior: WARN" in output
    assert "session_audit_identity_field=False" in output
    assert "Restart ANA MCP, then run Live Behavior" in output


def test_live_behavior_allow_warn_returns_success_for_operator_collection(monkeypatch):
    script = load_script()
    monkeypatch.setattr(script, "call_live_session_trust", lambda mcp_url, timeout=30: {
        "success": True,
        "message": "Gata cu 72% incredere.",
        "data": {
            "trust": {
                "score": 72,
                "signals": {"has_code_context_pack": False},
            },
        },
    })
    monkeypatch.setattr(script, "call_live_error_radar", lambda mcp_url, timeout=30: live_radar_payload())
    monkeypatch.setattr(script, "call_live_code_context_query_alias", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "code_map": {"query": "operator status reload behavior"},
            "compressed_state": {"goal": "operator status reload behavior"},
        },
    })
    monkeypatch.setattr(script, "call_live_code_context_graph_preference", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "code_map": {
                "results": [{"file": "ANA_MAX/dev_artifacts/scripts/ana_operator_status.py"}]
            }
        },
    })
    monkeypatch.setattr(script, "call_live_code_context_graph_limit_one", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "code_map": {
                "results": [{"file": "ANA_MAX/dev_artifacts/scripts/ana_operator_status.py"}]
            }
        },
    })
    monkeypatch.setattr(script, "disk_error_radar_runtime_count", lambda: 65)

    code = script.main(["--allow-warn"])

    assert code == 0


def test_live_behavior_warns_when_error_radar_runtime_is_stale(monkeypatch):
    script = load_script()
    monkeypatch.setattr(script, "call_live_session_trust", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "trust": {"score": 100, "signals": {"identity_surface_status": "PASS"}},
            "identity_surface": {"status": "PASS"},
        },
    })
    monkeypatch.setattr(script, "call_live_error_radar", lambda mcp_url, timeout=30: live_radar_payload(runtime=0))
    monkeypatch.setattr(script, "call_live_code_context_query_alias", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "code_map": {"query": "operator status reload behavior"},
            "compressed_state": {"goal": "operator status reload behavior"},
        },
    })
    monkeypatch.setattr(script, "call_live_code_context_graph_preference", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "code_map": {
                "results": [{"file": "ANA_MAX/dev_artifacts/scripts/ana_operator_status.py"}]
            }
        },
    })
    monkeypatch.setattr(script, "call_live_code_context_graph_limit_one", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "code_map": {
                "results": [{"file": "ANA_MAX/dev_artifacts/scripts/ana_operator_status.py"}]
            }
        },
    })
    monkeypatch.setattr(script, "disk_error_radar_runtime_count", lambda: 65)

    report = script.build_report()

    assert report["status"] == "WARN"
    assert report["checks"]["error_radar_runtime_breakdown"] is False
    assert report["error_radar"]["live_runtime"] == 0
    assert report["error_radar"]["disk_runtime"] == 65


def test_live_behavior_warns_when_code_context_query_alias_is_stale(monkeypatch):
    script = load_script()
    monkeypatch.setattr(script, "call_live_session_trust", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "trust": {"score": 100, "signals": {"identity_surface_status": "PASS"}},
            "identity_surface": {"status": "PASS"},
        },
    })
    monkeypatch.setattr(script, "call_live_error_radar", lambda mcp_url, timeout=30: live_radar_payload())
    monkeypatch.setattr(script, "call_live_code_context_query_alias", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "code_map": {"query": "Untitled Workspace Code"},
            "compressed_state": {"goal": "Observe current workspace and route next action."},
        },
    })
    monkeypatch.setattr(script, "call_live_code_context_graph_preference", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "code_map": {
                "results": [{"file": "ANA_MAX/dev_artifacts/scripts/ana_operator_status.py"}]
            }
        },
    })
    monkeypatch.setattr(script, "call_live_code_context_graph_limit_one", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "code_map": {
                "results": [{"file": "ANA_MAX/dev_artifacts/scripts/ana_operator_status.py"}]
            }
        },
    })
    monkeypatch.setattr(script, "disk_error_radar_runtime_count", lambda: 65)

    report = script.build_report()

    assert report["status"] == "WARN"
    assert report["checks"]["code_context_query_alias"] is False


def test_live_behavior_warns_when_code_context_graph_preference_is_stale(monkeypatch):
    script = load_script()
    monkeypatch.setattr(script, "call_live_session_trust", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "trust": {"score": 100, "signals": {"identity_surface_status": "PASS"}},
            "identity_surface": {"status": "PASS"},
        },
    })
    monkeypatch.setattr(script, "call_live_error_radar", lambda mcp_url, timeout=30: live_radar_payload())
    monkeypatch.setattr(script, "call_live_code_context_query_alias", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "code_map": {"query": "operator status reload behavior"},
            "compressed_state": {"goal": "operator status reload behavior"},
        },
    })
    monkeypatch.setattr(script, "call_live_code_context_graph_preference", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "code_map": {
                "results": [{"file": "vscode_extension/CHANGELOG.md"}]
            }
        },
    })
    monkeypatch.setattr(script, "call_live_code_context_graph_limit_one", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "code_map": {
                "results": [{"file": "ANA_MAX/dev_artifacts/scripts/ana_operator_status.py"}]
            }
        },
    })
    monkeypatch.setattr(script, "disk_error_radar_runtime_count", lambda: 65)

    report = script.build_report()

    assert report["status"] == "WARN"
    assert report["checks"]["code_context_graph_preference"] is False


def test_live_behavior_warns_when_code_context_graph_limit_one_is_stale(monkeypatch):
    script = load_script()
    monkeypatch.setattr(script, "call_live_session_trust", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "trust": {"score": 100, "signals": {"identity_surface_status": "PASS"}},
            "identity_surface": {"status": "PASS"},
        },
    })
    monkeypatch.setattr(script, "call_live_error_radar", lambda mcp_url, timeout=30: live_radar_payload())
    monkeypatch.setattr(script, "call_live_code_context_query_alias", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "code_map": {"query": "operator status reload behavior"},
            "compressed_state": {"goal": "operator status reload behavior"},
        },
    })
    monkeypatch.setattr(script, "call_live_code_context_graph_preference", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "code_map": {
                "results": [{"file": "ANA_MAX/dev_artifacts/scripts/ana_operator_status.py"}]
            }
        },
    })
    monkeypatch.setattr(script, "call_live_code_context_graph_limit_one", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "code_map": {
                "results": [{"file": "vscode_extension/CHANGELOG.md"}]
            }
        },
    })
    monkeypatch.setattr(script, "disk_error_radar_runtime_count", lambda: 65)

    report = script.build_report()

    assert report["status"] == "WARN"
    assert report["checks"]["code_context_graph_limit_one"] is False
    assert report["code_context_pack"]["graph_limit_one_top_file"] == "vscode_extension/CHANGELOG.md"


def test_live_behavior_warns_when_error_radar_summary_is_stale(monkeypatch):
    script = load_script()
    monkeypatch.setattr(script, "call_live_session_trust", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "trust": {"score": 100, "signals": {"identity_surface_status": "PASS"}},
            "identity_surface": {"status": "PASS"},
        },
    })
    monkeypatch.setattr(script, "call_live_error_radar", lambda mcp_url, timeout=30: live_radar_payload(include_summary=False))
    monkeypatch.setattr(script, "call_live_code_context_query_alias", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "code_map": {"query": "operator status reload behavior"},
            "compressed_state": {"goal": "operator status reload behavior"},
        },
    })
    monkeypatch.setattr(script, "call_live_code_context_graph_preference", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "code_map": {
                "results": [{"file": "ANA_MAX/dev_artifacts/scripts/ana_operator_status.py"}]
            }
        },
    })
    monkeypatch.setattr(script, "call_live_code_context_graph_limit_one", lambda mcp_url, timeout=30: {
        "success": True,
        "data": {
            "code_map": {
                "results": [{"file": "ANA_MAX/dev_artifacts/scripts/ana_operator_status.py"}]
            }
        },
    })
    monkeypatch.setattr(script, "disk_error_radar_runtime_count", lambda: 65)

    report = script.build_report()

    assert report["status"] == "WARN"
    assert report["checks"]["error_radar_summary"] is False
    assert report["error_radar"]["summary_present"] is False
