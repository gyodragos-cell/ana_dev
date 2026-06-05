from pathlib import Path

import pytest

from ana.core.error_model.errors import RoutingFailure, ValidationError
from ana.tools.registry.registry import ToolRegistry, ToolSpec
from ana.tools.registry.skill_engine import SkillEngine
from ana.tools.router.router import ToolRouter


def test_registry_router_selects_lowest_priority_then_name():
    registry = ToolRegistry()
    registry.register(ToolSpec("z_tool", "fs.read", lambda payload: payload, priority=20))
    registry.register(ToolSpec("a_tool", "fs.read", lambda payload: payload, priority=10))

    selected = ToolRouter().route("fs.read", registry)

    assert selected.name == "a_tool"
    with pytest.raises(RoutingFailure):
        ToolRouter().route("missing.capability", registry)


def test_skill_engine_validates_os_v2_skill():
    text = Path("SKILL.md").read_text(encoding="utf-8")
    spec = SkillEngine().validate_os_v2_skill(text)

    assert spec.title == "ANA_SKILL.md"
    assert spec.tasks == tuple("ABCDEFGHIJK")


def test_skill_engine_rejects_missing_sections():
    with pytest.raises(ValidationError):
        SkillEngine().validate_os_v2_skill("# Missing\n")
