"""Live Voice Debug - Shows real-time voice activity"""
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from tools.live_voice_bridge import speak

print("=" * 70)
print("ANA MAX - LIVE VOICE DEBUG MONITOR")
print("=" * 70)
print("This window shows real-time voice activity")
print("Every message spoken will appear here")
print("Press Ctrl+C to stop")
print("=" * 70)

# Speak initial message
speak("Live voice debug monitor is now active!")

counter = 0
while True:
    try:
        counter += 1
        print(f"\n[{counter}] Voice monitor active - waiting for messages...")
        time.sleep(5)
    except KeyboardInterrupt:
        speak("Voice debug monitor stopped.")
        print("\nStopped.")
        break
