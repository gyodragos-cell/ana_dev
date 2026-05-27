"""
ANA MAX - Auto Voice for Chat
Monitors voice_queue.txt and speaks every line automatically.
This is what makes ANA speak every response in chat.
"""
from __future__ import annotations
import logging
import sys
import time
from pathlib import Path
from tools.live_voice_bridge import speak

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)

QUEUE_FILE = Path(__file__).parent / "voice_queue.txt"

def speak_new_lines():
    """Read new lines from queue and speak them."""
    QUEUE_FILE.touch(exist_ok=True)

    # Get file size
    with QUEUE_FILE.open("r", encoding="utf-8") as f:
        f.seek(0, 2)  # Go to end
        file_size = f.tell()

    last_pos = 0

    print("=" * 70)
    print("ANA MAX - AUTO VOICE FOR CHAT")
    print("=" * 70)
    print(f"Monitoring: {QUEUE_FILE}")
    print("Add text to voice_queue.txt and I'll speak it!")
    print("Press Ctrl+C to stop")
    print("=" * 70)

    speak("Auto voice bridge is active. I will speak every response!")

    try:
        while True:
            # Check for new content
            current_size = QUEUE_FILE.stat().st_size

            if current_size > last_pos:
                with QUEUE_FILE.open("r", encoding="utf-8") as f:
                    f.seek(last_pos)
                    new_text = f.read().strip()
                    last_pos = current_size

                if new_text:
                    print(f"\n[Speaking] {new_text[:80]}...")
                    speak(new_text)
                    print("[Done]")

            time.sleep(0.5)  # Check twice per second

    except KeyboardInterrupt:
        speak("Auto voice bridge stopped.")
        print("\nStopped.")
        return 0

if __name__ == "__main__":
    sys.exit(speak_new_lines())
