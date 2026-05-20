"""
ANA MAX - Live Voice Bridge

Small, low-noise wrapper around pyttsx3 for local voice feedback.
This module is intentionally lazy: importing it must not start speech.
"""

from __future__ import annotations

import logging
import threading
import time

import pyttsx3

logger = logging.getLogger(__name__)

# comtypes can emit verbose DEBUG messages for optional SAPI events.
logging.getLogger("comtypes").setLevel(logging.WARNING)

_engine = None
_engine_lock = threading.Lock()
_enabled = True


def _create_engine(rate: int = 150, volume: float = 0.7):
    engine = pyttsx3.init()
    engine.setProperty("rate", rate)
    engine.setProperty("volume", volume)

    voices = engine.getProperty("voices") or []
    for voice in voices:
        if "Zira" in voice.name:
            engine.setProperty("voice", voice.id)
            break

    return engine


def get_engine():
    """Return the shared pyttsx3 engine, creating it on first use."""
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                _engine = _create_engine()
                logger.info("Live voice bridge initialized")
    return _engine


class LiveVoiceBridge:
    """Compatibility wrapper used by older callers."""

    def __init__(self, rate: int = 150, volume: float = 0.7):
        self.enabled = True
        self.engine = _create_engine(rate=rate, volume=volume)

    def speak(self, text: str):
        if not self.enabled or not text:
            return
        with _engine_lock:
            self.engine.say(text)
            self.engine.runAndWait()

    def enable(self):
        self.enabled = True
        print("Voice enabled")

    def disable(self):
        self.enabled = False
        print("Voice disabled")

    def stop(self):
        return None


def speak(text: str):
    """Speak text immediately. Errors are logged without noisy tracebacks."""
    if not _enabled or not text:
        return

    try:
        engine = get_engine()
        with _engine_lock:
            engine.say(text)
            engine.runAndWait()
    except Exception as exc:
        logger.warning("Voice speak failed: %s", exc)
        print(f"Voice error: {exc}")


def speak_async(text: str):
    """Speak text in a background thread."""
    if not text:
        return
    thread = threading.Thread(target=speak, args=(text,), daemon=True)
    thread.start()


def get_live_voice():
    """Return a compatibility LiveVoiceBridge instance."""
    return LiveVoiceBridge()


def enable():
    global _enabled
    _enabled = True
    print("Voice enabled")


def disable():
    global _enabled
    _enabled = False
    print("Voice disabled")


def cleanup():
    """Placeholder for callers that expect a cleanup hook."""
    logger.info("Voice cleanup complete")


if __name__ == "__main__":
    print("Testing live voice bridge...\n")
    speak("Hello. This is the live voice bridge working.")
    time.sleep(1)
    speak("Test complete. Voice bridge is ready.")
    print("\nTest complete. Voice bridge is working.")
