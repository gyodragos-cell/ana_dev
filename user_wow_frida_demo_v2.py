import subprocess
import sys
import time
from pathlib import Path

import frida


HOOK = r"""
const messageBox = Module.getExportByName("user32.dll", "MessageBoxW");

Interceptor.attach(messageBox, {
  onEnter(args) {
    const originalTitle = args[2].readUtf16String();
    const originalText = args[1].readUtf16String();

    send("LIVE API CALL: user32.dll!MessageBoxW");
    send("Original title: " + originalTitle);
    send("Original text: " + originalText);

    Memory.writeUtf16String(args[2], "AFTER: ANA MAX Runtime Control");
    Memory.writeUtf16String(
      args[1],
      "ANA MAX changed this live window before Windows displayed it. This is authorized local runtime instrumentation."
    );

    send("Changed title before display.");
    send("Changed text before display.");
  }
});
"""


def say(text):
    print(f"ANA: {text}", flush=True)
    try:
        import win32com.client

        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        speaker.Rate = 0
        speaker.Volume = 100
        speaker.Speak(text)
    except Exception:
        try:
            import ctypes

            ctypes.windll.kernel32.Beep(880, 160)
        except Exception:
            pass


def on_message(message, data):
    if message["type"] == "send":
        payload = message["payload"]
        print("[FRIDA]", payload, flush=True)
        if payload.startswith("LIVE API CALL"):
            say("I intercepted a live Windows API call.")
        elif payload.startswith("Changed text"):
            say("The window text was changed before Windows displayed it.")
    elif message["type"] == "error":
        print("[FRIDA ERROR]", message.get("stack", message), flush=True)


def main():
    here = Path(__file__).resolve().parent
    target = here / "target_live_window_v2.py"

    print("=" * 76, flush=True)
    print("ANA MAX - USER WOW DEMO (IMPROVED)", flush=True)
    print("=" * 76, flush=True)
    print(flush=True)
    print("One simple idea:", flush=True)
    print("A text-only AI can talk about a window.", flush=True)
    print("ANA MAX with tools can observe and change authorized live runtime behavior.", flush=True)
    print(flush=True)

    say("A text only AI can talk. ANA MAX with tools can act on an authorized live system.")

    proc = subprocess.Popen(
        [sys.executable, str(target)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    print(f"Started authorized local target PID: {proc.pid}", flush=True)
    say("Starting a local demo app.")
    time.sleep(0.5)

    print("Attaching Frida to the local target...", flush=True)
    say("Attaching Frida to the local target.")
    session = frida.attach(proc.pid)
    script = session.create_script(HOOK)
    script.on("message", on_message)
    script.load()

    print("Hook loaded on user32.dll!MessageBoxW", flush=True)
    print("Watch the window that appears - it should show CHANGED text!", flush=True)
    print(flush=True)
    say("Hook loaded. Watch the window title and text.")

    try:
        while proc.poll() is None:
            line = proc.stdout.readline() if proc.stdout else ""
            if line:
                print("[TARGET]", line.rstrip(), flush=True)
            time.sleep(0.1)
    finally:
        try:
            session.detach()
        except Exception:
            pass

    print(flush=True)
    print("=" * 76, flush=True)
    print("PROOF COMPLETE", flush=True)
    print("=" * 76, flush=True)
    print("The live app asked Windows to show one message.", flush=True)
    print("Frida changed it before Windows displayed it.", flush=True)
    print(flush=True)
    say("Proof complete. ANA MAX gives agents runtime awareness and control when the task needs it.")

    print("Press any key to exit...", flush=True)
    input()


if __name__ == "__main__":
    main()
