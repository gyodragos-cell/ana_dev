"""
Video analysis script for testt final.mp4
Extracts metadata and key information
"""
import os
from datetime import datetime

video_path = r"C:\Users\billy\Desktop\testt final.mp4"

print("=" * 76)
print("VIDEO ANALYSIS: testt final.mp4")
print("=" * 76)
print()

# File info
if os.path.exists(video_path):
    size = os.path.getsize(video_path)
    created = os.path.getctime(video_path)
    modified = os.path.getmtime(video_path)
    
    print("FILE METADATA:")
    print(f"  Name: {os.path.basename(video_path)}")
    print(f"  Size: {size:,} bytes ({size/1024/1024:.2f} MB)")
    print(f"  Created: {datetime.fromtimestamp(created).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Modified: {datetime.fromtimestamp(modified).strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Analysis
    print("ASSESSMENT:")
    print(f"  {'✓' if size < 20*1024*1024 else '✗'} File size under 20 MB: {size/1024/1024:.2f} MB")
    print(f"  {'✓' if size < 50*1024*1024 else '✗'} File size under 50 MB: {size/1024/1024:.2f} MB")
    print()
    
    print("RECOMMENDATIONS:")
    if size > 20*1024*1024:
        print(f"  ⚠ File is TOO LARGE for web sharing ({size/1024/1024:.2f} MB)")
        print("  → Compress to under 20 MB using Handbrake or ffmpeg")
        print("  → Target: 1280x720 resolution, H.264 codec")
    else:
        print("  ✓ File size is OK for sharing")
    
    print()
    print("EXPECTED CONTENT (based on USER_WOW_DEMO code):")
    print("  1. Terminal starts with intro message")
    print("  2. Voice narration: 'A text only AI can talk...'")
    print("  3. Frida attaches to target process")
    print("  4. MessageBox appears with MODIFIED text:")
    print("     Title: 'AFTER: ANA MAX Runtime Control'")
    print("     Text: 'ANA MAX changed this live window...'")
    print("  5. Window should stay visible 5 seconds")
    print("  6. User clicks OK")
    print("  7. Proof complete message")
    print()
    
    print("CRITICAL CHECKPOINTS FOR WOW DEMO:")
    print("  □ Can you SEE the MessageBox window clearly?")
    print("  □ Is the text 'AFTER: ANA MAX Runtime Control' readable?")
    print("  □ Does the window stay visible for 3-5 seconds?")
    print("  □ Is audio narration clear?")
    print("  □ Is terminal positioned to NOT cover the window?")
    print()
    
else:
    print("ERROR: File not found!")
    print(f"Path: {video_path}")

print("=" * 76)
