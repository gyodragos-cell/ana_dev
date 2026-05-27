"""
Speak ANA's last response automatically.
Run this after each chat response to hear it spoken.
"""
import sys
from pathlib import Path

# Add ANA_MAX to path
sys.path.insert(0, str(Path(__file__).parent))

from tools.live_voice_bridge import speak_async

def speak_response(text):
    """Speak the given text asynchronously."""
    if not text:
        return
    speak_async(text)
    print(f"âœ“ Speaking: {text[:50]}...")

if __name__ == "__main__":
    # Test
    speak_response("Voice is working! I can hear ANA speaking now!")
