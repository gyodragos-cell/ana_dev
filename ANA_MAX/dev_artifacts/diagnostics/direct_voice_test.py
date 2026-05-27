"""Direct voice test - speaks immediately"""
import sys
sys.path.insert(0, '.')

from tools.live_voice_bridge import speak

print("Speaking now...")
speak("Hello! I am speaking live through ANA MAX tools right now!")
print("Done!")
