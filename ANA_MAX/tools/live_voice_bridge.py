"""
ANA MAX - Live Voice Bridge
Speaks everything in real-time during conversation

This bridges Qoder's text output to Ana's voice.
Every message gets spoken automatically.
"""

import pyttsx3
import queue
import threading
import time

class LiveVoiceBridge:
    """
    Automatically speaks text in real-time.
    Uses a queue to handle multiple messages.
    
    Usage:
        bridge = LiveVoiceBridge()
        bridge.speak("This message will be spoken!")
        bridge.speak("This will be spoken next!")
    """
    
    def __init__(self, rate=150, volume=0.7):
        """Initialize live voice bridge."""
        self.enabled = True
        self.message_queue = queue.Queue()
        
        # Initialize pyttsx3 ONCE
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', rate)
        self.engine.setProperty('volume', volume)
        
        # Set female voice (Zira)
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if 'Zira' in voice.name:
                self.engine.setProperty('voice', voice.id)
                break
        
        # DO NOT start background thread yet
        self.speaker_thread = None
        
        print("✅ Live Voice Bridge active!")
        # DO NOT speak on init - let user trigger it
    
    def _speaker_worker(self):
        """Background thread that processes the message queue."""
        while True:
            try:
                # Collect all pending messages
                messages = []
                try:
                    # Get first message (blocking)
                    message = self.message_queue.get(timeout=1)
                    if message is None:  # Poison pill to stop
                        break
                    messages.append(message)
                    
                    # Collect any other pending messages
                    while not self.message_queue.empty():
                        try:
                            msg = self.message_queue.get_nowait()
                            if msg is None:
                                return  # Stop
                            messages.append(msg)
                            self.message_queue.task_done()
                        except queue.Empty:
                            break
                except queue.Empty:
                    continue
                
                # Speak all messages at once
                if self.enabled and messages:
                    for msg in messages:
                        self.engine.say(msg)
                    self.engine.runAndWait()
                    
                    for _ in messages:
                        self.message_queue.task_done()
                        
            except Exception as e:
                print(f"Voice error: {e}")
    
    def speak(self, text: str):
        """
        Speak text immediately (blocking).
        
        Args:
            text: Text to speak
        """
        if not self.enabled or not text:
            return
        
        # Speak directly - blocking call
        self.engine.say(text)
        self.engine.runAndWait()
    
    def _speak_now(self, text: str):
        """Speak immediately (for initialization only)."""
        if self.enabled:
            self.engine.say(text)
            self.engine.runAndWait()
    
    def disable(self):
        """Disable voice."""
        self.enabled = False
        print("Voice disabled")
    
    def enable(self):
        """Enable voice."""
        self.enabled = True
        print("Voice enabled")
    
    def stop(self):
        """Stop the voice bridge."""
        self.message_queue.put(None)  # Poison pill
        self.speaker_thread.join()


# Global instance - always available
_bridge = None

def get_live_voice():
    """Get or create live voice bridge."""
    global _bridge
    if _bridge is None:
        _bridge = LiveVoiceBridge()
    return _bridge

def speak(text: str):
    """
    Quick speak function - use this everywhere!
    
    Usage:
        from tools.live_voice_bridge import speak
        speak("This will be spoken!")
    """
    global _bridge
    
    # Always create fresh engine to avoid threading issues
    import pyttsx3
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.setProperty('volume', 0.7)
    
    # Set Zira voice
    voices = engine.getProperty('voices')
    for voice in voices:
        if 'Zira' in voice.name:
            engine.setProperty('voice', voice.id)
            break
    
    # Speak directly
    engine.say(text)
    engine.runAndWait()
    
    # Force cleanup
    del engine


if __name__ == "__main__":
    # Test
    print("Testing live voice bridge...\n")
    
    speak("Hello! This is the live voice bridge working!")
    time.sleep(2)
    
    speak("I will speak everything automatically now!")
    time.sleep(2)
    
    speak("Test complete! Voice bridge is ready!")
    
    print("\n✅ Test complete! Voice bridge is working!")
    time.sleep(3)
