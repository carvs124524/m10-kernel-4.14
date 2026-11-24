#!/usr/bin/env python3
"""Patch a 4.14.133 vendor .ko for a 4.14.336 kernel.

- Rewrites __versions CRCs with the values from the kernel Module.symvers.
- Rewrites the vermagic version string (same length).
The file size is unchanged.
"""
import argparse
import hashlib
import struct
import sys
from pathlib import Path

MODVERSION_ENTRY = 64  # unsigned long crc + char name[56] on arm64


def elf_sections(data):
    assert data[:4] == b"\x7fELF"
    e_shoff = struct.unpack_from("<Q", data, 0x28)[0]
    e_shentsize = struct.unpack_from("<H", data, 0x3A)[0]
    e_shnum = struct.unpack_from("<H", data, 0x3C)[0]
    e_shstrndx = struct.unpack_from("<H", data, 0x3E)[0]
    shdrs = []
    for i in range(e_shnum):
        off = e_shoff + i * e_shentsize
        (name, typ, flags, addr, offset, size, link, info, align, entsize) = \
            struct.unpack_from("<IIQQQQIIQQ", data, off)
        shdrs.append({
            "index": i, "name_off": name, "type": typ, "offset": offset,
            "size": size, "entsize": entsize, "shdr_offset": off,
        })
    strtab_off = shdrs[e_shstrndx]["offset"]
    strtab = data[strtab_off:strtab_off + shdrs[e_shstrndx]["size"]]
    for s in shdrs:
        end = strtab.find(b"\0", s["name_off"])
        s["name"] = strtab[s["name_off"]:end].decode(errors="replace")
    return shdrs


def read_symvers(path):
    syms = {}
    for line in Path(path).read_text().splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0].startswith("0x"):
            syms[parts[1]] = int(parts[0], 16)
    return syms


def patch(input_path, output_path, symvers, old_version, new_version):
    data = bytearray(Path(input_path).read_bytes())
    secs = elf_sections(data)
    by_name = {s["name"]: s for s in secs}
    versions = by_name.get("__versions")
    modinfo = by_name.get(".modinfo")
    if not versions:
        raise SystemExit(f"{input_path}: __versions ausente")
    if not modinfo:
        raise SystemExit(f"{input_path}: .modinfo ausente")

    entries = versions["size"] // MODVERSION_ENTRY
    assert versions["size"] % MODVERSION_ENTRY == 0
    missing = []
    mismatched = 0
    for i in range(entries):
        off = versions["offset"] + i * MODVERSION_ENTRY
        old_crc = struct.unpack_from("<Q", data, off)[0]
        name = bytes(data[off + 8:off + 64]).split(b"\0")[0].decode(errors="replace")
        if name not in symvers:
            missing.append(name)
            continue
        new_crc = symvers[name]
        if old_crc != new_crc:
            mismatched += 1
            struct.pack_into("<Q", data, off, new_crc)

    moff, msize = modinfo["offset"], modinfo["size"]
    section = data[moff:moff + msize]
    idx = section.find(b"vermagic=")
    if idx < 0:
        raise SystemExit(f"{input_path}: vermagic ausente")
    end = section.find(b"\0", idx)
    value_start = idx + len(b"vermagic=")
    value = bytes(section[value_start:end])
    old = old_version.encode()
    new = new_version.encode()
    prefix_end = value_start + len(old)
    if not value.startswith(old):
        raise SystemExit(f"{input_path}: vermagic inesperado: {value!r}")
    new_section = bytes(section[:value_start]) + new + bytes(section[prefix_end:])
    new_offset = len(data)
    data.extend(new_section)
    struct.pack_into("<Q", data, modinfo["shdr_offset"] + 24, new_offset)
    struct.pack_into("<Q", data, modinfo["shdr_offset"] + 32, len(new_section))

    Path(output_path).write_bytes(data)
    print(f"{input_path}: {entries} simbolos, {mismatched} CRCs corrigidos, "
          f"{len(missing)} ausentes, vermagic {old_version}->{new_version}")
    if missing:
        print("  ausentes: " + ", ".join(missing[:20]))
    return missing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symvers", required=True)
    ap.add_argument("--old-version", default="4.14.133")
    ap.add_argument("--new-version", default="4.14.336")
    ap.add_argument("input", nargs="+")
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()
    syms = read_symvers(args.symvers)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    all_missing = {}
    for p in args.input:
        out = outdir / Path(p).name
        missing = patch(p, out, syms, args.old_version, args.new_version)
        all_missing[p] = missing
    if any(all_missing.values()):
        sys.exit(2)


if __name__ == "__main__":
    main()
