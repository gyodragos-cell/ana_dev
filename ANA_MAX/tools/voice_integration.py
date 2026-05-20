"""
ANA MAX - Voice Integration Helper

Lazy helper for speaking status messages. Importing this module must stay quiet.
"""

from __future__ import annotations

import logging
import threading

from tools.edge_tts_voice import EdgeTTSVoice

logger = logging.getLogger(__name__)

_voice_instance = None
_voice_lock = threading.Lock()


def get_voice():
    """Get or create the shared voice instance."""
    global _voice_instance
    if _voice_instance is None:
        with _voice_lock:
            if _voice_instance is None:
                try:
                    _voice_instance = EdgeTTSVoice()
                except Exception as exc:
                    logger.warning("Voice init failed: %s", exc)
                    return None
    return _voice_instance


def speak(text: str, async_mode: bool = True):
    """Speak text with optional background execution."""
    if not text:
        return

    voice = get_voice()
    if not voice:
        return

    def _run():
        try:
            voice.execute("speak", text=text)
        except Exception as exc:
            logger.warning("Voice speak failed: %s", exc)

    if async_mode:
        threading.Thread(target=_run, daemon=True).start()
    else:
        _run()


def test_voice():
    """Run a small manual voice test."""
    print("\nTesting voice integration...\n")
    speak("Hello. This is a voice integration test.", async_mode=False)
    speak("Voice integration is working.", async_mode=False)
    print("Voice test complete.")


if __name__ == "__main__":
    test_voice()
