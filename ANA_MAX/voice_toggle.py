"""
ANA MAX - Voice Auto-Start Script
Starts JARVIS voice and keeps it running in background
Run this when you start working with Qoder
"""

from tools.edge_tts_voice import EdgeTTSVoice
import sys

print("\n" + "="*70)
print("🎙️  ANA MAX - JARVIS VOICE AUTO-START")
print("="*70 + "\n")

print("Starting voice engine...")
voice = EdgeTTSVoice(rate=150, volume=0.7)

# Voice greeting - speaks immediately
print("✅ Voice engine ready!")
print(f"   - Voice: Microsoft Zira (female, warm)")
print(f"   - Rate: 150 (calm, friendly)")
print(f"   - Volume: 0.7 (clear, not loud)")
print()

# Auto greeting
voice.execute('speak', text='Voice is now always on! I will speak everything Qoder writes. We are a team, working together!')

print("="*70)
print("✅ VOICE IS ALWAYS ON NOW!")
print("="*70)
print()
print("How it works:")
print("  • Qoder works → Ana speaks automatically")
print("  • You SEE the text + HEAR the voice")
print("  • No extra clicks needed!")
print()
print("This window must stay open for voice to work.")
print("Minimize it and forget about it!")
print()
print("To disable voice: Close this window (Ctrl+C)")
print("="*70)
print()

# Keep alive for voice playback
try:
    while True:
        import time
        time.sleep(1)
except KeyboardInterrupt:
    voice.execute('speak', text='Voice deactivated. See you later, colleague!')
    print("\n✅ Voice deactivated. See you later!")
    sys.exit(0)
