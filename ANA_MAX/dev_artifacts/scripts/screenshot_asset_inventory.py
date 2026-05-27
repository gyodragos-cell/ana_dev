"""Inventory screenshot candidates without publishing them.

The script scans ANA_MAX/sandbox/screenshots and writes a JSON inventory next
to the raw screenshots. It uses only the Python standard library.
"""

from __future__ import annotations

import hashlib
import json
import struct
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


ROOT = Path(__file__).resolve().parents[3]
SCREENSHOT_DIR = ROOT / "ANA_MAX" / "sandbox" / "screenshots"
OUTPUT = SCREENSHOT_DIR / "asset_inventory.json"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _png_size(data: bytes) -> Optional[Tuple[int, int]]:
    if len(data) < 24 or not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return None
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def _jpeg_size(data: bytes) -> Optional[Tuple[int, int]]:
    if len(data) < 4 or not data.startswith(b"\xff\xd8"):
        return None
    index = 2
    while index + 9 < len(data):
        if data[index] != 0xFF:
            index += 1
            continue
        marker = data[index + 1]
        index += 2
        if marker in {0xD8, 0xD9}:
            continue
        if index + 2 > len(data):
            return None
        segment_length = struct.unpack(">H", data[index : index + 2])[0]
        if segment_length < 2:
            return None
        if marker in range(0xC0, 0xC4) or marker in range(0xC5, 0xC8) or marker in range(0xC9, 0xCC) or marker in range(0xCD, 0xD0):
            if index + 7 <= len(data):
                height, width = struct.unpack(">HH", data[index + 3 : index + 7])
                return width, height
        index += segment_length
    return None


def _image_size(path: Path) -> Optional[Tuple[int, int]]:
    data = path.read_bytes()[:1024 * 512]
    return _png_size(data) or _jpeg_size(data)


def _entry(path: Path) -> Dict[str, Any]:
    stat = path.stat()
    size = _image_size(path)
    return {
        "file": path.name,
        "relative_path": str(path.relative_to(ROOT)),
        "bytes": stat.st_size,
        "last_modified_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        "sha256": _sha256(path),
        "dimensions": {"width": size[0], "height": size[1]} if size else None,
        "public_safe_review": "pending",
        "recommended_use": "pending",
        "notes": "",
    }


def main() -> int:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    images = sorted(
        path
        for path in SCREENSHOT_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )
    inventory = {
        "schema": "ana.visual_asset_inventory.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_folder": str(SCREENSHOT_DIR),
        "image_count": len(images),
        "images": [_entry(path) for path in images],
    }
    OUTPUT.write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT} with {len(images)} image(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

