#!/usr/bin/env python3
"""
JokerForge/ANA MAX - Performance Benchmarks
===========================================
Measures server startup, SQLite transactions, and vector search operations.
Must be ASCII-only to pass quality gate.
"""

import time
import sys
import os
import random
import math
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.resolve()
sys.path.insert(0, str(project_root))

print("=" * 60)
print("  JOKERFORGE / ANA MAX - PERFORMANCE BENCHMARK")
print("=" * 60)

# 1. Startup Latency
t0 = time.perf_counter()
import main
from tools.base import registry
t1 = time.perf_counter()
startup_sec = t1 - t0
print(f"Benchmark 1: Startup Latency")
print(f"  - Registry initialization: {startup_sec:.4f} seconds")

# 2. SQLite Database Speed
print(f"\nBenchmark 2: Database Operations Speed (100 operations)")
try:
    import sqlite3
    db_path = project_root / "memory" / "ana_brain.db"
    
    # Ensure folder exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE IF NOT EXISTS benchmark_temp (id INTEGER PRIMARY KEY, value TEXT)")
    
    t0 = time.perf_counter()
    for i in range(100):
        conn.execute("INSERT INTO benchmark_temp (value) VALUES (?)", (f"benchmark_{i}",))
    conn.commit()
    t1 = time.perf_counter()
    insert_latency = (t1 - t0) * 1000  # ms
    
    t0 = time.perf_counter()
    cursor = conn.execute("SELECT * FROM benchmark_temp LIMIT 100")
    rows = cursor.fetchall()
    t1 = time.perf_counter()
    select_latency = (t1 - t0) * 1000  # ms
    
    # Cleanup
    conn.execute("DROP TABLE benchmark_temp")
    conn.commit()
    conn.close()
    
    print(f"  - 100 Inserts: {insert_latency:.2f} ms ({insert_latency/100:.3f} ms/op)")
    print(f"  - 100 Selects: {select_latency:.2f} ms ({select_latency/100:.3f} ms/op)")
except Exception as e:
    print(f"  - [FAIL] DB benchmark failed: {e}")

# 3. Vector Memory Speed simulation (dim=384)
print(f"\nBenchmark 3: Memory Vector Matching latency (100 cosine calculations)")
try:
    def cosine_similarity(v1, v2):
        dot_product = sum(x*y for x, y in zip(v1, v2))
        magnitude1 = math.sqrt(sum(x*x for x in v1))
        magnitude2 = math.sqrt(sum(y*y for y in v2))
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        return dot_product / (magnitude1 * magnitude2)
        
    vectors = [[random.random() for _ in range(384)] for _ in range(100)]
    query = [random.random() for _ in range(384)]
    
    t0 = time.perf_counter()
    similarities = [cosine_similarity(query, v) for v in vectors]
    similarities.sort(reverse=True)
    t1 = time.perf_counter()
    vector_latency = (t1 - t0) * 1000  # ms
    
    print(f"  - Match query against 100 vectors: {vector_latency:.4f} ms")
    print(f"  - Top result similarity: {similarities[0]:.4f}")
except Exception as e:
    print(f"  - [FAIL] Vector search simulation failed: {e}")

print("\n" + "=" * 60)
print("  BENCHMARK COMPLETED")
print("=" * 60)
