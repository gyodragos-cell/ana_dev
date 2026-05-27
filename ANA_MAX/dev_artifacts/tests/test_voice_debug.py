"""
Voice Debug Test - Shows EXACTLY what happens
"""
import logging
import sys

# Enable DEBUG for all voice modules
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

print("=" * 70)
print("VOICE DEBUG TEST")
print("=" * 70)

try:
    print("\n[1] Importing voice_integration...")
    from tools.voice_integration import speak, get_voice

    print("[2] Getting voice instance...")
    voice = get_voice()

    if voice:
        print(f"[3] Voice instance: {voice}")
        print(f"[4] Voice definition: {voice.get_definition()}")

        print("\n[5] Calling speak() with async_mode=False...")
        speak("This is a debug test - if you hear this, voice works!")

        print("[6] speak() call completed!")
        print("\nâœ“ Voice executed successfully")
    else:
        print("âœ— Voice instance is None - initialization failed!")

except Exception as e:
    print(f"\nâœ— ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
