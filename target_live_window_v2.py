import ctypes
import os
import time


MB_OK = 0x00000000
MB_ICONINFORMATION = 0x00000040
MB_TOPMOST = 0x00040000
MB_SETFOREGROUND = 0x00010000


def main():
    user32 = ctypes.windll.user32

    # This text will be changed by Frida BEFORE the window appears
    text_buffer = ctypes.create_unicode_buffer(
        "BEFORE: Normal app message - this is what the app wanted to show",
        512,
    )
    title_buffer = ctypes.create_unicode_buffer("BEFORE: Normal Local App", 256)

    print("Local visual target started.", flush=True)
    print(f"PID: {os.getpid()}", flush=True)
    print("Frida has 2 seconds to attach before the window appears.", flush=True)
    time.sleep(2)

    # If Frida attached, it will rewrite these buffers in memory
    # The window will show the MODIFIED text, not the original
    print("Showing MessageBox now - if Frida is attached, you will see changed text...", flush=True)
    
    user32.MessageBoxW(
        None,
        text_buffer,
        title_buffer,
        MB_OK | MB_ICONINFORMATION | MB_TOPMOST | MB_SETFOREGROUND,
    )

    print("MessageBox closed - demo complete.", flush=True)


if __name__ == "__main__":
    main()
