from __future__ import annotations

import importlib.util
import struct
import sys
from pathlib import Path


ANA_MAX_DIR = Path(__file__).resolve().parents[2] / "ANA_MAX"
if str(ANA_MAX_DIR) not in sys.path:
    sys.path.insert(0, str(ANA_MAX_DIR))

from tools.binary_map_tool import BinaryMapTool  # noqa: E402


SCRIPT = ANA_MAX_DIR / "dev_artifacts" / "scripts" / "ana_binary_map.py"


def load_module():
    spec = importlib.util.spec_from_file_location("ana_binary_map", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def make_minimal_pe(path: Path) -> None:
    data = bytearray(0x800)
    data[0:2] = b"MZ"
    struct.pack_into("<I", data, 0x3C, 0x80)
    pe = 0x80
    data[pe:pe + 4] = b"PE\x00\x00"
    struct.pack_into("<H", data, pe + 4, 0x8664)
    struct.pack_into("<H", data, pe + 6, 1)
    struct.pack_into("<I", data, pe + 8, 123456)
    struct.pack_into("<H", data, pe + 20, 0xF0)
    opt = pe + 24
    struct.pack_into("<H", data, opt, 0x20B)
    struct.pack_into("<I", data, opt + 16, 0x1000)
    struct.pack_into("<Q", data, opt + 24, 0x140000000)
    # Import data directory: RVA 0x1100
    struct.pack_into("<I", data, opt + 112 + 8, 0x1100)
    struct.pack_into("<I", data, opt + 112 + 12, 40)
    sec = opt + 0xF0
    data[sec:sec + 8] = b".text\x00\x00\x00"
    struct.pack_into("<I", data, sec + 8, 0x1000)
    struct.pack_into("<I", data, sec + 12, 0x1000)
    struct.pack_into("<I", data, sec + 16, 0x400)
    struct.pack_into("<I", data, sec + 20, 0x200)
    # Import descriptor at RVA 0x1100 -> file 0x300
    imp = 0x300
    struct.pack_into("<I", data, imp + 12, 0x1128)
    data[0x328:0x328 + len(b"KERNEL32.dll\x00")] = b"KERNEL32.dll\x00"
    data[0x360:0x360 + len(b"CreateFileW diagnostics\x00")] = b"CreateFileW diagnostics\x00"
    path.write_bytes(data)


def test_ana_binary_map_parses_minimal_pe(tmp_path: Path) -> None:
    binary = tmp_path / "sample.dll"
    make_minimal_pe(binary)

    result = load_module().parse_binary(binary, strings_limit=10)

    assert result.format == "pe"
    assert result.architecture == "x64"
    assert result.entry_point == "0x140001000"
    assert result.imports == ["KERNEL32.dll"]
    assert result.sections[0]["name"] == ".text"
    assert result.sha256
    assert any("CreateFileW" in item for item in result.strings)


def test_binary_map_tool_blocks_missing_file() -> None:
    result = BinaryMapTool().execute(path="does-not-exist.exe")

    assert not result.is_success
    assert "not found" in (result.error or "").lower()
