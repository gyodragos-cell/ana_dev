#!/usr/bin/env python3
"""
JokerForge/ANA MAX - Health Diagnostics Script
==============================================
Performs quick vitals check of the system.
Must be ASCII-only to pass quality gate.
"""

import sys
import os
import sqlite3
import socket
from pathlib import Path

# Add parent directory to path to allow imports
project_root = Path(__file__).parent.resolve()
sys.path.insert(0, str(project_root))

print("=" * 60)
print("  JOKERFORGE / ANA MAX - HEALTH DIAGNOSTICS")
print("=" * 60)

failed = False

# 1. Config Loader Check
print("\n[1] Configuration Check...")
try:
    from core.config import config
    port = config.get("mcp.port", 8765)
    db_path = config.get("memory.database_path", "memory/ana_brain.db")
    print(f"    [OK] Configuration loaded.")
    print(f"         Port: {port}")
    print(f"         DB Path: {db_path}")
except Exception as e:
    print(f"    [FAIL] Failed to load configuration: {e}")
    failed = True

# 2. SQLite Database Check
print("\n[2] Memory Database Check...")
try:
    full_db_path = project_root / db_path
    if not full_db_path.exists():
        # Try relative to current working dir
        full_db_path = Path(db_path)
        
    if full_db_path.exists():
        conn = sqlite3.connect(str(full_db_path))
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        print(f"    [OK] Database connected. Found {len(tables)} tables.")
        for t in tables[:5]:
            print(f"         - {t}")
        if len(tables) > 5:
            print(f"         - ... and {len(tables)-5} more tables")
    else:
        print(f"    [WARN] Database file does not exist yet at {full_db_path}")
        print(f"           It will be initialized automatically on first startup.")
except Exception as e:
    print(f"    [FAIL] SQLite check failed: {e}")
    failed = True

# 3. Port Availability Check
print("\n[3] Port Listener Check...")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1.0)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    
    if result == 0:
        print(f"    [OK] Server is actively listening on port {port}.")
    else:
        print(f"    [INFO] Port {port} is free (Server is not running).")
except Exception as e:
    print(f"    [WARN] Could not inspect port: {e}")

# 4. Logs Directory Check
print("\n[4] Logs Directory Check...")
try:
    log_dir = project_root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    print(f"    [OK] Logs directory is writable: {log_dir}")
except Exception as e:
    print(f"    [FAIL] Logs directory check failed: {e}")
    failed = True

# Final verdict
print("\n" + "=" * 60)
if failed:
    print("  DIAGNOSTIC STATUS: [FAIL] - Please resolve the issues above.")
    print("=" * 60)
    sys.exit(1)
else:
    print("  DIAGNOSTIC STATUS: [PASS] - All vitals are healthy.")
    print("=" * 60)
    sys.exit(0)
