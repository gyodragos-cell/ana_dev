#!/usr/bin/env python3
"""
Capture desktop screenshot and save to file
"""

import sys
import json
import base64
from pathlib import Path
from datetime import datetime

# Add ANA_MAX to path
ana_max_dir = Path(__file__).resolve().parents[4] / "ANA_MAX"
sys.path.insert(0, str(ana_max_dir))

from tools.qoder_ana_integration import ANAToolClient

def main():
    print("Capturing desktop...\n")
    
    ana = ANAToolClient()
    
    if not ana.is_server_running():
        print("✗ MCP Server is NOT running!")
        return 1
    
    # Capture desktop
    result = ana.call_tool("desktop_capture")
    
    if result.get("content"):
        text = result["content"][0].get("text", "{}")
        data = json.loads(text)
        
        if data.get("success"):
            # Save screenshot
            screenshot_dir = ana_max_dir / "screenshots"
            screenshot_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"capture_{timestamp}.png"
            filepath = screenshot_dir / filename
            
            # Extract base64 image
            image_data = data.get("data", {}).get("image", "")
            if image_data:
                # Remove data URL prefix if present
                if "," in image_data:
                    image_data = image_data.split(",")[1]
                
                # Decode and save
                image_bytes = base64.b64decode(image_data)
                filepath.write_bytes(image_bytes)
                
                print(f"✓ Screenshot saved: {filepath}")
                print(f"✓ Resolution: {data.get('data', {}).get('width', 'N/A')}x{data.get('data', {}).get('height', 'N/A')}")
            else:
                print("✓ Desktop captured (no image data)")
                print(f"  Message: {data.get('message', 'N/A')}")
        else:
            print(f"✗ Capture failed: {data.get('error', 'Unknown error')}")
    else:
        print("✗ No response from tool")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
