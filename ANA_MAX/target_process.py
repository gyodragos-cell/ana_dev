import ctypes
import time
import sys

# Load C standard library on Windows
try:
    libc = ctypes.CDLL("msvcrt.dll")
except Exception:
    try:
        libc = ctypes.CDLL("ucrtbase.dll")
    except Exception:
        libc = ctypes.cdll.msvcrt

print("Target process running...")
sys.stdout.flush()

while True:
    val = libc.rand()
    print(f"Random: {val}")
    sys.stdout.flush()
    time.sleep(1)
