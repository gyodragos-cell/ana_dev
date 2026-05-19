#!/usr/bin/env python3
"""
ANA v18 MAX - MCP wrapper.
"""

from __future__ import annotations

import io
import os
import sys
from pathlib import Path





BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
CONFIG_PATH = BASE_DIR / "config" / "settings.yaml"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.chdir(BASE_DIR)

from core.config import config  # noqa: E402

config.load(str(CONFIG_PATH))

import main as ana_main
# Activeaza logging-ul centralizat in ana_max.log
ana_main._configure_logging(debug=True)
ana_main._register_all_tools()

from core.mcp_server import start_mcp_with_bridge  # noqa: E402


if __name__ == "__main__":
    start_mcp_with_bridge()
