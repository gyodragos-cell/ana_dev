"""
ANA MAX - Voice Integration Helper
Automatically speaks Qoder's responses

This module wraps voice commentary into every action.
"""

from tools.edge_tts_voice import EdgeTTSVoice

# Global voice instance - always on
_voice_instance = None


def get_voice():
    """Get or create voice instance."""
    global _voice_instance
    if _voice_instance is None:
        _voice_instance = EdgeTTSVoice()
        # Greeting
        _voice_instance.execute('speak', text='Voice integration ready! I will speak everything Qoder writes!')
    return _voice_instance


def speak(text: str, async_mode: bool = True):
    """
    Speak text immediately.
    
    Usage:
        from tools.voice_integration import speak
        speak("I am fixing the bug now...")
    """
    voice = get_voice()
    
    if async_mode:
        # Non-blocking - speaks in background
        import threading
        def _speak_thread():
            voice.execute('speak', text=text)
        
        thread = threading.Thread(target=_speak_thread, daemon=True)
        thread.start()
    else:
        # Blocking - waits for speech to finish
        voice.execute('speak', text=text)


def test_voice():
    """Test voice integration."""
    print("\n🎙️ Testing voice integration...\n")
    
    speak("Hello colleague! This is a test. Can you hear me?")
    
    import time
    time.sleep(3)  # Wait for speech
    
    speak("Voice integration is working! Now every message will be spoken!")
    
    print("✅ Voice test complete!")


if __name__ == "__main__":
    test_voice()
