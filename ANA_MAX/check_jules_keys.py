#!/usr/bin/env python3
"""Check Jules API Keys Status"""
from tools.jules_api_rotator import get_rotator

r = get_rotator()
stats = r.get_stats()

print("\n" + "="*50)
print("  Jules API Key Rotation Status")
print("="*50)
print(f"\nTotal Keys: {stats['total_keys']}")
print(f"Active Keys: {stats['active_keys']}")
print(f"Rate Limited: {stats['rate_limited_keys']}")
print(f"Total Requests: {stats['total_requests']}")
print(f"Success Rate: {stats['success_rate']*100:.1f}%")
print(f"Strategy: {stats['current_strategy']}")
print(f"Max Requests/Key: {stats['max_requests_per_key']}")

print("\n📋 Configured Keys:")
print("-" * 50)
for k in stats['keys']:
    status = "✅ Active" if k['is_active'] else "❌ Inactive"
    print(f"  {k['name']}: {status}")
    print(f"    Requests: {k['request_count']} | Total: {k['total_requests']} | Errors: {k['total_errors']}")
    print(f"    Success Rate: {k['success_rate']*100:.1f}%")
    print()

print("="*50)
print("\n✅ API Key Rotation is READY!")
print("="*50 + "\n")
