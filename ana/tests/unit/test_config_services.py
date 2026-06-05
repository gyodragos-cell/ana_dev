from pathlib import Path

import pytest

from ana.config.loader import ConfigLoader
from ana.core.error_model.errors import BoundaryViolation, RoutingFailure
from ana.services.fs.service import FSService
from ana.services.http.service import FakeHTTPService, HTTPResponse
from ana.services.llm.service import DeterministicLLMService
from ana.services.shell.service import DeterministicShellService


def test_config_loader_reads_defaults():
    config = ConfigLoader().load(
        Path("ana/config/defaults.yaml"),
        Path("ana/config/schema.json"),
    )

    assert config.mode == "dev"
    assert config.services == ("fs", "http", "shell", "llm")
    assert config.event_bus_replay_limit == 100


def test_fs_service_is_root_bounded(tmp_path):
    service = FSService(tmp_path)
    service.write_text({"path": "note.txt", "text": "hello"})

    assert service.read_text({"path": "note.txt"})["text"] == "hello"
    with pytest.raises(BoundaryViolation):
        service.read_text({"path": "../outside.txt"})


def test_fake_services_require_registered_inputs():
    http = FakeHTTPService()
    http.register("GET", "https://ana.local/health", HTTPResponse(200, {"ok": True}))
    assert http.request({"url": "https://ana.local/health"})["status"] == 200
    with pytest.raises(RoutingFailure):
        http.request({"url": "https://ana.local/missing"})

    shell = DeterministicShellService()
    shell.register(("ana", "health"), lambda command: {"stdout": "ok", "code": 0})
    assert shell.run({"command": ["ana", "health"]})["stdout"] == "ok"
    with pytest.raises(RoutingFailure):
        shell.run({"command": ["ana", "unknown"]})

    llm = DeterministicLLMService()
    llm.register("ping", "pong")
    assert llm.complete({"prompt": "ping"})["text"] == "pong"
    with pytest.raises(RoutingFailure):
        llm.complete({"prompt": "missing"})
