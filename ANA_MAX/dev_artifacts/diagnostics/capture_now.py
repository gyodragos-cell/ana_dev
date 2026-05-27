"""Capture desktop screenshot to see what's on screen"""
import mss
from PIL import Image

with mss.mss() as sct:
    monitor = sct.monitors[1]  # Primary monitor
    screenshot = sct.grab(monitor)

    # Convert to PIL Image
    img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

    # Save
    output_path = "screenshots/current_desktop.png"
    img.save(output_path)

    print(f"Screenshot captured: {monitor['width']}x{monitor['height']}")
    print(f"Saved to: {output_path}")
    print(f"File size: {round(output_path.__sizeof__() / 1024, 1)} KB")
