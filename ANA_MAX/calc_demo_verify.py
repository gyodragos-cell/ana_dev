import subprocess
import time
import json
import urllib.request

MCP_URL = "http://127.0.0.1:8765/mcp"

def call_mcp(method, params):
    payload = {"jsonrpc": "2.0", "id": int(time.time()), "method": method, "params": params}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(MCP_URL, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.load(resp)

def check_calc():
    r = call_mcp("tools/call", {"name": "windows_uia_bridge", "arguments": {"action": "inspect_window", "window_title": "Calculator"}})
    c = json.loads(r["result"]["content"][0]["text"])
    return c.get("success", False)

def click_button(title):
    try:
        r = call_mcp("tools/call", {"name": "windows_uia_bridge", "arguments": {"action": "click_element", "window_title": "Calculator", "element_title": title, "control_type": "Button"}})
        c = json.loads(r["result"]["content"][0]["text"])
        if c.get("success"):
            print(f"  ✅ {title}")
            return True
        else:
            print(f"  ❌ {title}: {c.get('error')}")
            return False
    except Exception as e:
        print(f"  ❌ {title}: {e}")
        return False

print("🎬 ANA MAX DEMO - Calculator")
print("\n1️⃣  Deschid Calculator...")
subprocess.Popen(["calc.exe"])
time.sleep(5)

if not check_calc():
    print("  ❌ Calculator nu s-a deschis!")
    exit(1)

print("  ✅ Calculator vizibil!")

print("\n2️⃣  CALCUL: 5 × 5 = 25")
click_button("Five")
time.sleep(0.8)
click_button("Multiply by")
time.sleep(0.8)
click_button("Five")
time.sleep(0.8)
click_button("Equals")
time.sleep(1)

print("\n3️⃣  CALCUL: 100 ÷ 4 = 25")
click_button("Clear")
time.sleep(0.5)
click_button("One")
time.sleep(0.8)
click_button("Zero")
time.sleep(0.8)
click_button("Zero")
time.sleep(0.8)
click_button("Divide by")
time.sleep(0.8)
click_button("Four")
time.sleep(0.8)
click_button("Equals")
time.sleep(1)

print("\n4️⃣  CALCUL: 789 + 11 = 800")
click_button("Clear")
time.sleep(0.5)
click_button("Seven")
time.sleep(0.8)
click_button("Eight")
time.sleep(0.8)
click_button("Nine")
time.sleep(0.8)
click_button("Plus")
time.sleep(0.8)
click_button("One")
time.sleep(0.8)
click_button("One")
time.sleep(0.8)
click_button("Equals")
time.sleep(1)

print("\n✅ DEMO COMPLETAT!")
