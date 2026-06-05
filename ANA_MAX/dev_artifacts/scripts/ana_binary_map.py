"""Static binary map for ANA MAX lab.

Analyzes executable/library files without executing them. This first pass uses
stdlib-only parsers for PE/ELF basics and printable strings. Optional LIEF can be
added later behind the same output contract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MAX_BYTES_DEFAULT = 25 * 1024 * 1024
STRING_RE = re.compile(rb"[ -~]{4,}")


@dataclass
class BinaryMap:
    schema: str
    path: str
    size: int
    sha256: str
    format: str
    architecture: str
    entry_point: str | None
    imports: list[str]
    exports: list[str]
    sections: list[dict[str, Any]]
    strings: list[str]
    metadata: dict[str, Any]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_limited(path: Path, max_bytes: int) -> bytes:
    size = path.stat().st_size
    if size > max_bytes:
        raise ValueError(f"Binary too large: {size} bytes > limit {max_bytes}")
    return path.read_bytes()


def extract_strings(data: bytes, limit: int = 80) -> list[str]:
    values = []
    seen = set()
    for match in STRING_RE.finditer(data):
        text = match.group(0).decode("utf-8", errors="ignore").strip()
        if not text or text in seen:
            continue
        if _looks_noisy(text):
            continue
        seen.add(text)
        values.append(text[:180])
        if len(values) >= limit:
            break
    return values


def _looks_noisy(text: str) -> bool:
    if len(text) > 180:
        return True
    alpha = sum(ch.isalpha() for ch in text)
    return alpha < 2 and not any(mark in text.lower() for mark in (".dll", ".so", ".exe"))


def parse_binary(path: Path, max_bytes: int = MAX_BYTES_DEFAULT, strings_limit: int = 80) -> BinaryMap:
    data = read_limited(path, max_bytes)
    fmt = "unknown"
    arch = "unknown"
    entry = None
    imports: list[str] = []
    exports: list[str] = []
    sections: list[dict[str, Any]] = []
    metadata: dict[str, Any] = {"generated_at": now_iso()}

    if data.startswith(b"MZ"):
        fmt, arch, entry, sections, imports, exports, metadata = parse_pe(data)
    elif data.startswith(b"\x7fELF"):
        fmt, arch, entry, sections, imports, exports, metadata = parse_elf(data)
    else:
        metadata["magic"] = data[:8].hex()

    return BinaryMap(
        schema="ana.binary_map.v1",
        path=str(path),
        size=len(data),
        sha256=sha256_bytes(data),
        format=fmt,
        architecture=arch,
        entry_point=entry,
        imports=imports[:120],
        exports=exports[:120],
        sections=sections[:80],
        strings=extract_strings(data, strings_limit),
        metadata=metadata,
    )


def parse_pe(data: bytes) -> tuple[str, str, str | None, list[dict[str, Any]], list[str], list[str], dict[str, Any]]:
    metadata: dict[str, Any] = {"generated_at": now_iso()}
    if len(data) < 0x40:
        return "pe", "unknown", None, [], [], [], metadata
    pe_offset = u32(data, 0x3C)
    if pe_offset <= 0 or pe_offset + 0x18 >= len(data) or data[pe_offset:pe_offset + 4] != b"PE\x00\x00":
        metadata["warning"] = "MZ header present but PE signature not found"
        return "pe", "unknown", None, [], [], [], metadata

    machine = u16(data, pe_offset + 4)
    number_sections = u16(data, pe_offset + 6)
    timestamp = u32(data, pe_offset + 8)
    optional_size = u16(data, pe_offset + 20)
    optional_offset = pe_offset + 24
    optional_magic = u16(data, optional_offset)
    is_pe32_plus = optional_magic == 0x20B
    arch = {
        0x014C: "x86",
        0x8664: "x64",
        0x01C0: "arm",
        0xAA64: "arm64",
    }.get(machine, f"unknown:0x{machine:04x}")
    address_of_entry = u32(data, optional_offset + 16) if optional_offset + 20 <= len(data) else 0
    image_base_offset = optional_offset + (24 if is_pe32_plus else 28)
    image_base = u64(data, image_base_offset) if is_pe32_plus else u32(data, image_base_offset)
    entry = f"0x{image_base + address_of_entry:x}" if address_of_entry else None

    section_offset = optional_offset + optional_size
    sections = []
    for index in range(number_sections):
        off = section_offset + index * 40
        if off + 40 > len(data):
            break
        name = data[off:off + 8].split(b"\x00", 1)[0].decode("ascii", errors="replace")
        virtual_size = u32(data, off + 8)
        virtual_address = u32(data, off + 12)
        raw_size = u32(data, off + 16)
        raw_ptr = u32(data, off + 20)
        sections.append({
            "name": name,
            "virtual_address": f"0x{virtual_address:x}",
            "virtual_size": virtual_size,
            "raw_size": raw_size,
            "raw_ptr": raw_ptr,
        })

    imports = parse_pe_imports(data, optional_offset, is_pe32_plus, sections)
    exports = parse_pe_exports(data, optional_offset, sections)
    metadata.update({
        "machine": f"0x{machine:04x}",
        "sections_count": number_sections,
        "timestamp": timestamp,
        "image_base": f"0x{image_base:x}",
        "optional_magic": f"0x{optional_magic:04x}",
    })
    return "pe", arch, entry, sections, imports, exports, metadata


def parse_pe_imports(data: bytes, optional_offset: int, is_pe32_plus: bool, sections: list[dict[str, Any]]) -> list[str]:
    data_dir_offset = optional_offset + (112 if is_pe32_plus else 96)
    if data_dir_offset + 16 > len(data):
        return []
    import_rva = u32(data, data_dir_offset + 8)
    if not import_rva:
        return []
    import_off = rva_to_offset(import_rva, sections)
    if import_off is None:
        return []
    imports = []
    for index in range(256):
        off = import_off + index * 20
        if off + 20 > len(data):
            break
        original_first_thunk = u32(data, off)
        name_rva = u32(data, off + 12)
        first_thunk = u32(data, off + 16)
        if original_first_thunk == 0 and name_rva == 0 and first_thunk == 0:
            break
        name_off = rva_to_offset(name_rva, sections)
        if name_off is None:
            continue
        name = read_c_string(data, name_off)
        if name:
            imports.append(name)
    return sorted(set(imports))


def parse_pe_exports(data: bytes, optional_offset: int, sections: list[dict[str, Any]]) -> list[str]:
    data_dir_offset = optional_offset + 96
    if u16(data, optional_offset) == 0x20B:
        data_dir_offset = optional_offset + 112
    if data_dir_offset + 8 > len(data):
        return []
    export_rva = u32(data, data_dir_offset)
    if not export_rva:
        return []
    export_off = rva_to_offset(export_rva, sections)
    if export_off is None or export_off + 40 > len(data):
        return []
    number_names = u32(data, export_off + 24)
    names_rva = u32(data, export_off + 32)
    names_off = rva_to_offset(names_rva, sections)
    if names_off is None:
        return []
    exports = []
    for index in range(min(number_names, 512)):
        ptr_off = names_off + index * 4
        if ptr_off + 4 > len(data):
            break
        name_off = rva_to_offset(u32(data, ptr_off), sections)
        if name_off is None:
            continue
        name = read_c_string(data, name_off)
        if name:
            exports.append(name)
    return sorted(set(exports))


def rva_to_offset(rva: int, sections: list[dict[str, Any]]) -> int | None:
    for section in sections:
        va = int(str(section["virtual_address"]), 16)
        size = max(int(section["virtual_size"]), int(section["raw_size"]))
        if va <= rva < va + size:
            return int(section["raw_ptr"]) + (rva - va)
    return None


def parse_elf(data: bytes) -> tuple[str, str, str | None, list[dict[str, Any]], list[str], list[str], dict[str, Any]]:
    elf_class = data[4] if len(data) > 5 else 0
    endian = "<" if data[5] == 1 else ">"
    is_64 = elf_class == 2
    arch_code = unpack(data, 18, "H", endian)
    entry = unpack(data, 24, "Q" if is_64 else "I", endian)
    arch = {
        0x03: "x86",
        0x3E: "x64",
        0x28: "arm",
        0xB7: "arm64",
    }.get(arch_code, f"unknown:0x{arch_code:04x}")
    metadata = {
        "generated_at": now_iso(),
        "elf_class": "ELF64" if is_64 else "ELF32",
        "endianness": "little" if endian == "<" else "big",
        "machine": f"0x{arch_code:04x}",
    }
    imports = sorted({text for text in extract_strings(data, 300) if text.endswith(".so") or ".so." in text})
    return "elf", arch, f"0x{entry:x}" if entry else None, [], imports, [], metadata


def u16(data: bytes, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0] if offset + 2 <= len(data) else 0


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0] if offset + 4 <= len(data) else 0


def u64(data: bytes, offset: int) -> int:
    return struct.unpack_from("<Q", data, offset)[0] if offset + 8 <= len(data) else 0


def unpack(data: bytes, offset: int, fmt: str, endian: str) -> int:
    size = struct.calcsize(fmt)
    return struct.unpack_from(endian + fmt, data, offset)[0] if offset + size <= len(data) else 0


def read_c_string(data: bytes, offset: int, limit: int = 260) -> str:
    chunk = data[offset:offset + limit]
    raw = chunk.split(b"\x00", 1)[0]
    return raw.decode("utf-8", errors="ignore").strip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze a binary file statically.")
    parser.add_argument("path")
    parser.add_argument("--max-bytes", type=int, default=MAX_BYTES_DEFAULT)
    parser.add_argument("--strings-limit", type=int, default=80)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = parse_binary(Path(args.path).resolve(), max_bytes=args.max_bytes, strings_limit=args.strings_limit)
    print(json.dumps(asdict(result), indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
