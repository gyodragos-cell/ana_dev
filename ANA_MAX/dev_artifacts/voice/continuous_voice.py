"""
ANA MAX - Simple Continuous Voice Bridge
Speaks everything written to voice_queue.txt - runs forever
"""
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tools.live_voice_bridge import speak

QUEUE_FILE = Path(__file__).parent / "voice_queue.txt"

print("=" * 70)
print("ANA MAX - CONTINUOUS VOICE BRIDGE")
print("=" * 70)
print(f"Monitoring: {QUEUE_FILE}")
print("Every line added will be spoken automatically")
print("Press Ctrl+C to stop")
print("=" * 70)

# Initial test
speak("Voice bridge is now running continuously!")

last_size = 0
if QUEUE_FILE.exists():
    last_size = QUEUE_FILE.stat().st_size

loop_count = 0

while True:
    try:
        loop_count += 1

        # Check if file has new content
        if QUEUE_FILE.exists():
            current_size = QUEUE_FILE.stat().st_size

            if current_size > last_size:
                # Read only the new content
                with QUEUE_FILE.open("r", encoding="utf-8", errors="ignore") as f:
                    f.seek(last_size)
                    new_text = f.read().strip()
                    last_size = current_size

                if new_text and len(new_text) > 5:  # Skip very short text
                    print(f"\n[{loop_count}] Speaking: {new_text[:60]}...")
                    try:
                        speak(new_text)
                        print(f"[{loop_count}] Done!")
                    except Exception as e:
                        print(f"[{loop_count}] Voice error: {e}")

        # Check twice per second
        time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\nStopping voice bridge...")
        speak("Voice bridge stopped.")
        break
    except Exception as e:
        print(f"\nError in loop {loop_count}: {e}")
        time.sleep(1)  # Wait before retrying

print("Voice bridge stopped.")
