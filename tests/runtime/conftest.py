from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ANA_MAX_DIR = ROOT / "ANA_MAX"


def _prefer_ana_max_imports() -> None:
    ana_path = str(ANA_MAX_DIR)
    sys.path[:] = [path for path in sys.path if path != ana_path]
    sys.path.insert(0, ana_path)

    for module_name in ("core", "tools"):
        module = sys.modules.get(module_name)
        if module is None:
            continue
        module_file = str(getattr(module, "__file__", "") or "")
        module_paths = [str(path) for path in getattr(module, "__path__", [])]
        if module_file.startswith(ana_path) or any(path.startswith(ana_path) for path in module_paths):
            continue
        sys.modules.pop(module_name, None)

    import core  # noqa: PLC0415

    legacy_core = str(ROOT / "core")
    core_paths = getattr(core, "__path__", None)
    if core_paths is not None and legacy_core not in [str(path) for path in core_paths]:
        core_paths.append(legacy_core)


_prefer_ana_max_imports()
