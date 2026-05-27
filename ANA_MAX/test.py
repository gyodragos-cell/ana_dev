import requests
import json
import time

BRIDGE_URL = "http://127.0.0.1:8790/tools"

def call_tool(tool_name, params):
    try:
        payload = {
            "tool": tool_name,
            "params": params
        }
        start = time.time()
        r = requests.post(f"{BRIDGE_URL}/call", json=payload, timeout=15)
        elapsed = round(time.time() - start, 3)

        return {
            "status": r.status_code,
            "elapsed": elapsed,
            "ok": r.status_code == 200,
            "response": r.text[:5000]  # limit output
        }
    except Exception as e:
        return {
            "status": "EXCEPTION",
            "elapsed": None,
            "ok": False,
            "response": str(e)
        }

def generate_minimal_params(schema):
    params = {}
    props = schema.get("properties", {})

    for key, spec in props.items():
        if spec.get("required", False):
            # required param → generate minimal valid value
            if spec["type"] == "string":
                params[key] = spec.get("default", "") or ""
            elif spec["type"] == "integer":
                params[key] = spec.get("default", 0)
            elif spec["type"] == "boolean":
                params[key] = spec.get("default", False)
            else:
                params[key] = spec.get("default", None)
        else:
            # optional param → skip for minimal test
            pass

    return params

def main():
    print("\n=== ANA MAX FULL TOOL TESTER ===\n")

    # 1. Get tool list
    r = requests.get(f"{BRIDGE_URL}/list")
    tools = r.json().get("tools", [])
    print(f"Found {len(tools)} tools.\n")

    results = []

    # 2. Test each tool
    for tool in tools:
        name = tool["name"]
        schema = tool["input_schema"]

        print(f"Testing: {name} ...")

        params = generate_minimal_params(schema)
        result = call_tool(name, params)

        results.append({
            "tool": name,
            "ok": result["ok"],
            "status": result["status"],
            "elapsed": result["elapsed"]
        })

        status = "PASS" if result["ok"] else "FAIL"
        print(f" → {status} ({result['status']}) in {result['elapsed']}s\n")

    # 3. Summary
    passed = sum(1 for r in results if r["ok"])
    failed = len(results) - passed

    print("\n=== SUMMARY ===")
    print(f"PASS: {passed}")
    print(f"FAIL: {failed}")
    print("\nDetailed results:")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
