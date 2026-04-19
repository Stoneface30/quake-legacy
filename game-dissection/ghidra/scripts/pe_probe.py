#!/usr/bin/env python3
"""
pe_probe.py — minimal PE header + strings extractor.

No external deps. Reads a PE/COFF binary (EXE/DLL), prints:
  - Machine arch, timestamp, section layout (name/size/flags)
  - Debug directory pointer (whether symbols/PDB refs are present)
  - Import table (DLL names + up to 50 imported symbols per DLL)
  - ASCII + UTF-16LE printable strings >= min_len (default 6), deduped

Usage:
  python pe_probe.py <binary> [--strings-min 6] [--grep TOKEN1,TOKEN2,...]

Output is plain text — redirect to a file for reports.

This script is safe to run on copyrighted binaries: it does NOT disassemble,
does NOT dump code, and extracts only metadata + printable strings.
"""
from __future__ import annotations

import argparse
import re
import struct
import sys
from pathlib import Path

IMAGE_DOS_SIGNATURE = 0x5A4D  # "MZ"
IMAGE_NT_SIGNATURE = 0x00004550  # "PE\0\0"

MACHINE_MAP = {
    0x014C: "x86 (I386)",
    0x8664: "x86_64 (AMD64)",
    0x01C0: "ARM",
    0xAA64: "ARM64",
}

SECTION_FLAGS = [
    (0x00000020, "CODE"),
    (0x00000040, "INITIALIZED_DATA"),
    (0x00000080, "UNINITIALIZED_DATA"),
    (0x20000000, "EXECUTE"),
    (0x40000000, "READ"),
    (0x80000000, "WRITE"),
]


def parse_pe(path: Path):
    data = path.read_bytes()
    if len(data) < 0x40 or struct.unpack_from("<H", data, 0)[0] != IMAGE_DOS_SIGNATURE:
        raise ValueError("not a PE file (no MZ)")
    e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    if struct.unpack_from("<I", data, e_lfanew)[0] != IMAGE_NT_SIGNATURE:
        raise ValueError("not a PE file (no PE\\0\\0)")

    # COFF file header (20 bytes) right after "PE\0\0"
    coff = e_lfanew + 4
    machine, n_sections, timestamp, _ptr_symtab, _n_symtab, size_opt, characteristics = (
        struct.unpack_from("<HHIIIHH", data, coff)
    )
    opt = coff + 20
    magic = struct.unpack_from("<H", data, opt)[0]  # 0x10B = PE32, 0x20B = PE32+
    is_pe32_plus = magic == 0x20B

    # image base / entry point
    if is_pe32_plus:
        image_base = struct.unpack_from("<Q", data, opt + 24)[0]
    else:
        image_base = struct.unpack_from("<I", data, opt + 28)[0]

    # data directories start: opt + (96 for PE32, 112 for PE32+)
    dd_off = opt + (112 if is_pe32_plus else 96)
    # there are 16 data directories, each 8 bytes (RVA + Size)
    data_dirs = []
    for i in range(16):
        rva, size = struct.unpack_from("<II", data, dd_off + i * 8)
        data_dirs.append((rva, size))

    # section table starts after optional header
    sec_off = opt + size_opt
    sections = []
    for i in range(n_sections):
        base = sec_off + i * 40
        name = data[base:base + 8].rstrip(b"\x00").decode("latin1", errors="replace")
        virt_size, virt_addr, raw_size, raw_ptr = struct.unpack_from("<IIII", data, base + 8)
        flags = struct.unpack_from("<I", data, base + 36)[0]
        sections.append({
            "name": name, "vsize": virt_size, "vaddr": virt_addr,
            "rsize": raw_size, "rptr": raw_ptr, "flags": flags,
        })

    # DEBUG dir is data_dirs[6]
    debug_rva, debug_size = data_dirs[6]
    # IMPORT dir is data_dirs[1]
    import_rva, import_size = data_dirs[1]

    return {
        "data": data,
        "machine": MACHINE_MAP.get(machine, f"0x{machine:04x}"),
        "timestamp": timestamp,
        "is_pe32_plus": is_pe32_plus,
        "image_base": image_base,
        "characteristics": characteristics,
        "sections": sections,
        "data_dirs": data_dirs,
        "debug_rva": debug_rva,
        "debug_size": debug_size,
        "import_rva": import_rva,
        "import_size": import_size,
    }


def rva_to_offset(rva: int, sections):
    for s in sections:
        if s["vaddr"] <= rva < s["vaddr"] + max(s["vsize"], s["rsize"]):
            return s["rptr"] + (rva - s["vaddr"])
    return None


def parse_imports(info):
    data = info["data"]
    sections = info["sections"]
    rva = info["import_rva"]
    if rva == 0:
        return []
    off = rva_to_offset(rva, sections)
    if off is None:
        return []
    imports = []
    # each IMAGE_IMPORT_DESCRIPTOR is 20 bytes; last is all zeros
    i = 0
    while True:
        base = off + i * 20
        if base + 20 > len(data):
            break
        fields = struct.unpack_from("<IIIII", data, base)
        (orig_first_thunk, _ts, _fwdchain, name_rva, first_thunk) = fields
        if all(f == 0 for f in fields):
            break
        name_off = rva_to_offset(name_rva, sections)
        dll_name = "?"
        if name_off is not None:
            end = data.find(b"\x00", name_off)
            dll_name = data[name_off:end].decode("latin1", errors="replace")
        # walk ILT (orig_first_thunk) for symbol names
        ilt_rva = orig_first_thunk if orig_first_thunk else first_thunk
        syms = []
        if ilt_rva:
            ilt_off = rva_to_offset(ilt_rva, sections)
            if ilt_off is not None:
                j = 0
                while j < 500:  # safety cap
                    entry_off = ilt_off + j * 4  # PE32; PE32+ would be 8
                    if info["is_pe32_plus"]:
                        entry_off = ilt_off + j * 8
                        if entry_off + 8 > len(data):
                            break
                        thunk = struct.unpack_from("<Q", data, entry_off)[0]
                        ord_flag = thunk & 0x8000000000000000
                        name_addr = thunk & 0x7FFFFFFF
                    else:
                        if entry_off + 4 > len(data):
                            break
                        thunk = struct.unpack_from("<I", data, entry_off)[0]
                        ord_flag = thunk & 0x80000000
                        name_addr = thunk & 0x7FFFFFFF
                    if thunk == 0:
                        break
                    if ord_flag:
                        syms.append(f"<ordinal {thunk & 0xFFFF}>")
                    else:
                        hint_off = rva_to_offset(name_addr, sections)
                        if hint_off is not None:
                            # hint = 2 bytes, then null-terminated name
                            nm_off = hint_off + 2
                            end = data.find(b"\x00", nm_off)
                            if end >= 0:
                                syms.append(data[nm_off:end].decode("latin1", errors="replace"))
                    j += 1
        imports.append((dll_name, syms))
        i += 1
    return imports


ASCII_RE = re.compile(rb"[\x20-\x7e]{6,}")
UTF16_RE = re.compile(rb"(?:[\x20-\x7e]\x00){6,}")


def extract_strings(data: bytes, min_len: int = 6):
    ascii_hits = {m.group(0).decode("latin1") for m in ASCII_RE.finditer(data)}
    utf16_hits = set()
    for m in UTF16_RE.finditer(data):
        try:
            utf16_hits.add(m.group(0).decode("utf-16le"))
        except UnicodeDecodeError:
            pass
    all_hits = ascii_hits | utf16_hits
    # filter by length on post-decode
    return sorted(s for s in all_hits if len(s) >= min_len)


def flag_string(flags: int):
    return "|".join(n for bit, n in SECTION_FLAGS if flags & bit)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("binary")
    ap.add_argument("--strings-min", type=int, default=6)
    ap.add_argument("--grep", default="")
    ap.add_argument("--strings-limit", type=int, default=500,
                    help="when --grep is empty, cap string output to this many lines")
    args = ap.parse_args()

    p = Path(args.binary)
    info = parse_pe(p)

    print(f"# PE probe: {p.name}")
    print(f"- size: {p.stat().st_size:,} bytes")
    print(f"- machine: {info['machine']}")
    print(f"- pe32+: {info['is_pe32_plus']}")
    print(f"- image_base: 0x{info['image_base']:x}")
    print(f"- timestamp: {info['timestamp']} (unix epoch)")
    print(f"- characteristics: 0x{info['characteristics']:04x}")
    print(f"- debug_dir: rva=0x{info['debug_rva']:x} size={info['debug_size']} (0 = no debug info / stripped)")
    print(f"- import_dir: rva=0x{info['import_rva']:x} size={info['import_size']}")
    print()
    print("## Sections")
    for s in info["sections"]:
        print(f"  {s['name']:<10} vaddr=0x{s['vaddr']:08x} vsize=0x{s['vsize']:08x} "
              f"rsize=0x{s['rsize']:08x} flags=[{flag_string(s['flags'])}]")
    print()
    print("## Imports (DLL -> first 50 symbols)")
    for dll, syms in parse_imports(info):
        print(f"  {dll}")
        for s in syms[:50]:
            print(f"    {s}")
        if len(syms) > 50:
            print(f"    ... ({len(syms) - 50} more)")
    print()

    strings = extract_strings(info["data"], args.strings_min)
    print(f"## Strings  (ASCII + UTF-16LE, min_len={args.strings_min}, total={len(strings):,})")
    if args.grep:
        tokens = [t.strip().lower() for t in args.grep.split(",") if t.strip()]
        for s in strings:
            low = s.lower()
            if any(t in low for t in tokens):
                print(f"  {s}")
    else:
        for s in strings[:args.strings_limit]:
            print(f"  {s}")
        if len(strings) > args.strings_limit:
            print(f"  ... ({len(strings) - args.strings_limit} more strings truncated)")


if __name__ == "__main__":
    main()
