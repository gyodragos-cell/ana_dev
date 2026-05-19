"""
ANA MAX - Edge TTS Voice Tool (EXPERIMENTAL)
Natural JARVIS-style voice using Microsoft Edge TTS

Voce naturală, prietenoasă, ca JARVIS.
Folosit DOAR în ana_dev pentru teste!
"""

import logging
import asyncio
import os
from typing import Optional, Dict, Any
from pathlib import Path

from tools.base import Tool, ToolDefinition, ToolParameter, ToolResult, ToolStatus

logger = logging.getLogger(__name__)

# Import live voice bridge for real-time TTS
try:
    from tools.live_voice_bridge import speak as live_speak
    LIVE_VOICE_AVAILABLE = True
except ImportError:
    LIVE_VOICE_AVAILABLE = False
    logger.info("live_voice_bridge not available")

# Try to import edge_tts
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    logger.info("edge-tts not installed - voice disabled. Run: pip install edge-tts")


class EdgeTTSVoice(Tool):
    """
    Ana vorbește cu voce naturală folosind Microsoft Edge TTS.
    
    Usage via MCP:
        ana.call_tool('edge_tts_voice', operation='speak', text='Salut!')
        ana.call_tool('edge_tts_voice', operation='list_voices')
        ana.call_tool('edge_tts_voice', operation='enable')
        ana.call_tool('edge_tts_voice', operation='disable')
    """
    
    # Available voices (natural, human-like)
    VOICES = {
        'en-us': 'en-US-AriaNeural',      # English US - Female, warm
        'en-gb': 'en-GB-SoniaNeural',     # English UK - Female, professional
        'ro-ro': 'ro-RO-AlinaNeural',     # Romanian - Female
    }
    
    def __init__(self, 
                 voice: str = 'en-US-AriaNeural',
                 rate: int = 150,
                 volume: float = 0.8,
                 use_edge_tts: bool = False):
        """
        Initialize voice tool.
        
        Args:
            voice: Voice name (for Edge TTS mode)
            rate: Speech rate (words per minute) - 150 = JARVIS-like
            volume: Volume (0.0 to 1.0)
            use_edge_tts: If True, use Edge TTS (natural but slower). If False, use pyttsx3 (fast but robotic)
        """
        super().__init__()
        self.enabled = True
        self.voice_name = voice
        self.rate = rate
        self.volume = volume
        self.use_edge_tts = use_edge_tts
        self._tts_engine = None
        
        # Initialize pyttsx3 for real-time streaming (default)
        if not use_edge_tts:
            try:
                import pyttsx3
                self._tts_engine = pyttsx3.init()
                
                # Set female voice (Zira) - warmer and friendlier
                voices = self._tts_engine.getProperty('voices')
                if voices:
                    # Zira is usually index 1
                    for voice in voices:
                        if 'Zira' in voice.name:
                            self._tts_engine.setProperty('voice', voice.id)
                            logger.info(f"Using female voice: {voice.name}")
                            break
                
                # Set calm, friendly rate (not too fast)
                self._tts_engine.setProperty('rate', rate)
                self._tts_engine.setProperty('volume', volume)
                logger.info("pyttsx3 initialized with calm female voice")
            except Exception as e:
                logger.warning(f"pyttsx3 not available: {e}")
                self.enabled = False
    
    def get_definition(self) -> ToolDefinition:
        """Return tool definition for MCP."""
        return ToolDefinition(
            name="edge_tts_voice",
            description="Natural JARVIS-style voice using Microsoft Edge TTS. Speaks text aloud with human-like quality.",
            parameters=[
                ToolParameter(
                    name="operation",
                    description="Operation: speak, list_voices, enable, disable",
                    type="string",
                    required=True,
                    choices=["speak", "list_voices", "enable", "disable"]
                ),
                ToolParameter(
                    name="text",
                    description="Text to speak (required for 'speak' operation)",
                    type="string",
                    required=False
                ),
                ToolParameter(
                    name="voice",
                    description="Voice name (e.g., en-US-AriaNeural, ro-RO-AlinaNeural)",
                    type="string",
                    required=False
                ),
            ],
            category="voice"
        )
    
    def execute(self, operation: str, text: Optional[str] = None, voice: Optional[str] = None, **kwargs) -> ToolResult:
        """Execute voice operation - ALWAYS speaks automatically!"""
        try:
            # AUTO-SPEAK: Every operation triggers voice commentary
            if operation == "speak" and text:
                # Use live voice bridge for real-time TTS
                if LIVE_VOICE_AVAILABLE:
                    try:
                        live_speak(text)
                    except Exception as e:
                        logger.warning(f"Live voice failed: {e}")
                
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={"spoken": text},
                    message=f"Spoke: {text[:50]}..."
                )
            
            elif operation == "list_voices":
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={"voices": self.VOICES},
                    message="Available voices listed"
                )
            
            elif operation == "enable":
                if not EDGE_TTS_AVAILABLE:
                    return ToolResult(
                        status=ToolStatus.ERROR,
                        error="edge-tts not installed. Run: pip install edge-tts"
                    )
                self.enabled = True
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    message="Voice commentary enabled"
                )
            
            elif operation == "disable":
                self.enabled = False
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    message="Voice commentary disabled"
                )
            
            else:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error=f"Unknown operation: {operation}"
                )
        
        except Exception as e:
            logger.error(f"Voice tool error: {e}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error=str(e)
            )
    
    def _speak_realtime(self, text: str):
        """Speak text in real-time using pyttsx3 (direct streaming, no MP3)."""
        try:
            if self._tts_engine:
                self._tts_engine.say(text)
                self._tts_engine.runAndWait()
        except Exception as e:
            logger.warning(f"Voice speak error: {e}")
    
    def _speak_text(self, text: str, voice: str):
        """Speak text using Edge TTS."""
        try:
            # Create temp audio file with unique name
            import time
            timestamp = int(time.time() * 1000)
            temp_file = self._temp_dir / f'voice_{timestamp}.mp3'
            
            # Generate speech asynchronously
            asyncio.run(self._generate_and_play(text, str(temp_file), voice))
            
            # Clean up old files (keep last 5)
            self._cleanup_old_files()
            
        except Exception as e:
            logger.warning(f"Edge TTS speak error: {e}")
    
    async def _generate_and_play(self, text: str, output_file: str, voice: str):
        """Generate speech and play it."""
        try:
            # Create communicate object
            communicate = edge_tts.Communicate(
                text,
                voice,
                rate=self.rate,
                volume=self.volume
            )
            
            # Save to file
            await communicate.save(output_file)
            
            # Play the audio
            self._play_audio(output_file)
            
        except Exception as e:
            logger.error(f"Failed to generate speech: {e}")
    
    def _play_audio(self, file_path: str):
        """Play audio file using Windows default player."""
        try:
            import subprocess
            # Simple approach: use Windows default app to open MP3
            subprocess.Popen(
                ['start', '', file_path],
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            # Wait for playback to finish (estimate 5 seconds)
            import time
            time.sleep(5)
        except Exception as e:
            logger.warning(f"Failed to play audio: {e}")
    
    def _cleanup_old_files(self):
        """Clean up old voice files, keep only last 5."""
        try:
            import glob
            voice_files = sorted(self._temp_dir.glob('voice_*.mp3'), key=lambda f: f.stat().st_mtime, reverse=True)
            # Delete all except last 5
            for old_file in voice_files[5:]:
                old_file.unlink()
        except Exception as e:
            logger.debug(f"Cleanup error: {e}")
