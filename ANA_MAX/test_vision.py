"""
Quick test: ANA vision tools
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

print("="*70)
print("👁️  Testing ANA Vision Tools")
print("="*70)

# Test 1: Desktop Capture
print("\n[1/3] Testing desktop_capture...")
try:
    from tools.desktop_capture import DesktopCaptureTool
    tool = DesktopCaptureTool()
    result = tool.execute(operation='capture')
    
    if result.is_success:
        screenshot_path = result.data.get('file', 'N/A') if result.data else 'N/A'
        print(f"  ✅ SUCCESS! Screenshot saved: {screenshot_path}")
    else:
        print(f"  ❌ FAILED: {result.error}")
except Exception as e:
    print(f"  ❌ ERROR: {e}")

# Test 2: UIA Bridge
print("\n[2/3] Testing windows_uia_bridge...")
try:
    from tools.windows_uia_bridge import WindowsUiaBridgeTool
    tool = WindowsUiaBridgeTool()
    result = tool.execute(action='list_windows')
    
    if result.is_success:
        controls = result.data.get('controls_count', 0) if result.data else 0
        print(f"  ✅ SUCCESS! Found {controls} UI controls")
        # Show first few controls
        controls_list = result.data.get('controls', []) if result.data else []
        if controls_list:
            print(f"  First control: {controls_list[0].get('name', 'N/A')}")
    else:
        print(f"  ❌ FAILED: {result.error}")
except Exception as e:
    print(f"  ❌ ERROR: {e}")

# Test 3: OCR
print("\n[3/3] Testing ocr_tool...")
try:
    import tools.ocr_tool as ocr_module
    from tools.desktop_capture import DesktopCaptureTool
    
    # First capture screenshot
    capture = DesktopCaptureTool()
    cap_result = capture.execute(operation='capture')
    
    if cap_result.is_success:
        screenshot_path = cap_result.data.get('file') if cap_result.data else None
        result = ocr_module.run({"action": "file", "image_path": screenshot_path})
        
        if result.get('status') == 'success':
            text = result.get('text', '')[:100]
            print(f"  ✅ SUCCESS! OCR found text: {text}...")
        else:
            print(f"  ❌ FAILED: {result.get('error')}")
    else:
        print(f"  ⏭️  SKIPPED (capture failed)")
except Exception as e:
    print(f"  ❌ ERROR: {e}")

print("\n" + "="*70)
print("✅ Vision Tools Test Complete")
print("="*70)
