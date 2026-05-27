"""Live capture Rihanna Umbrella video - 3 frames"""
import time
import pyautogui
from tools.desktop_capture import DesktopCaptureTool
from tools.live_voice_bridge import speak

print("=" * 60)
print("LIVE VIDEO ANALYSIS - RIHANNA UMBRELLA")
print("=" * 60)

# Make sure Chrome is in focus
print("\nBringing Chrome to focus...")
pyautogui.hotkey('alt', 'tab')
time.sleep(2)

# Capture 3 frames
for i in range(1, 4):
    print(f"\n>>> Capturing Frame {i}...")
    capture = DesktopCaptureTool()
    result = capture.execute(operation='capture', output_file=f'rihanna_video_frame_{i}.png')
    print(f"Frame {i} SAVED!")

    if i < 3:
        print(f"Waiting 5 seconds for next frame...")
        time.sleep(5)

print("\n" + "=" * 60)
print("ALL 3 FRAMES CAPTURED!")
print("=" * 60)

# Speak result
speak('Capture complete! I have taken 3 screenshots of the Rihanna Umbrella video playing on your screen. Now I will analyze each frame and describe what I see including her clothes, hair color, subtitles, and any visual effects like fireworks.')
