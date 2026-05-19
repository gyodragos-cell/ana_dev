"""
Simple voice test - no dependencies
"""
import pyttsx3

print("Starting voice test...")
print("Initializing engine...")

engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('volume', 0.7)

# Set Zira voice
voices = engine.getProperty('voices')
for voice in voices:
    if 'Zira' in voice.name:
        engine.setProperty('voice', voice.id)
        print(f"Using voice: {voice.name}")
        break

print("\nTest 1: Speaking 'Hello colleague!'")
engine.say('Hello colleague!')
engine.runAndWait()
print("Test 1 complete!\n")

print("Test 2: Speaking 'This is message two!'")
engine.say('This is message two!')
engine.runAndWait()
print("Test 2 complete!\n")

print("Test 3: Speaking 'Voice system is working perfectly!'")
engine.say('Voice system is working perfectly!')
engine.runAndWait()
print("Test 3 complete!\n")

print("="*50)
print("ALL TESTS COMPLETE!")
print("You should have heard 3 messages!")
print("="*50)
