from pathlib import Path
from ana.tools.registry.skill_engine import SkillEngine

text = Path("SKILL.md").read_text(encoding="utf-8")
engine = SkillEngine()
spec = engine.parse(text)

print("Title:", spec.title)
print("Sections found:", spec.sections)
print("Required sections:", engine.required_sections)
print("Missing:", set(engine.required_sections) - set(spec.sections))
