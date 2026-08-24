#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scan project text files and categorize their encoding.
Read-only: does NOT modify anything. Reports counts + per-encoding file lists.
"""
import os
import sys

ROOT = r"E:\documents\Paradox Interactive\Crusader Kings III\mod\HanDyansty"

# Extensions we treat as text and may convert.
TEXT_EXTS = {
    ".txt", ".yml", ".gui", ".mod", ".csv", ".json", ".info", ".lua",
    ".bce_source", ".ionfo", ".disabled", ".map", ".cfg", ".cfg",
}

# Known binary extensions to always skip (defensive).
BINARY_EXTS = {
    ".dds", ".png", ".jpg", ".jpeg", ".bmp", ".tga", ".tif", ".tiff",
    ".mesh", ".asset", ".blend", ".blend1", ".obj", ".fbx", ".wav", ".ogg",
    ".mp3", ".ttf", ".bin", ".exe", ".dll", ".zip", ".7z", ".rar",
}

def is_probably_binary(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in BINARY_EXTS:
        return True
    # If extension not in TEXT_EXTS, sniff content.
    if ext not in TEXT_EXTS:
        try:
            with open(path, "rb") as f:
                chunk = f.read(4096)
            if b"\x00" in chunk:
                return True
        except Exception:
            return True
    return False

def classify(raw):
    """Return category string for raw bytes."""
    if raw.startswith(b"\xef\xbb\xbf"):
        return "utf8_bom"
    # Try decode as UTF-8
    try:
        raw.decode("utf-8")
        return "utf8_nobom"
    except UnicodeDecodeError:
        pass
    # Try common fallbacks
    for enc in ("utf-8-sig", "cp1252", "gbk", "gb18030", "latin-1"):
        try:
            raw.decode(enc)
            return "other:" + enc
        except UnicodeDecodeError:
            continue
    return "other:unknown"

def main():
    stats = {
        "total_files": 0,
        "binary_skipped": 0,
        "utf8_bom": [],
        "utf8_nobom": [],
        "other": {},  # enc -> list
        "unknown_ext_text": [],  # text-extension files we still processed
    }

    for dirpath, dirnames, filenames in os.walk(ROOT):
        # Skip .workbuddy and tools output artifacts just in case
        if ".workbuddy" in dirpath:
            continue
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            ext = os.path.splitext(fn)[1].lower()
            stats["total_files"] += 1
            if is_probably_binary(full):
                stats["binary_skipped"] += 1
                continue
            try:
                with open(full, "rb") as f:
                    raw = f.read()
            except Exception as e:
                stats["binary_skipped"] += 1
                continue
            if len(raw) == 0:
                # empty file: treat as utf8_bom (no content to add bom, leave as-is)
                stats["utf8_bom"].append(full)
                continue
            cat = classify(raw)
            if cat == "utf8_bom":
                stats["utf8_bom"].append(full)
            elif cat == "utf8_nobom":
                stats["utf8_nobom"].append(full)
            elif cat.startswith("other:"):
                enc = cat.split(":", 1)[1]
                stats["other"].setdefault(enc, []).append(full)
            else:
                stats["other"].setdefault("unknown", []).append(full)

    # Report
    print("="*70)
    print("ENCODING SCAN REPORT")
    print("Root:", ROOT)
    print("="*70)
    print(f"Total files scanned : {stats['total_files']}")
    print(f"Binary skipped      : {stats['binary_skipped']}")
    print(f"UTF-8 BOM (ok)      : {len(stats['utf8_bom'])}")
    print(f"UTF-8 no BOM        : {len(stats['utf8_nobom'])}  <-- safe to add BOM")
    for enc, lst in sorted(stats["other"].items()):
        print(f"Other [{enc}]       : {len(lst)}  <-- need decode+reencode")
    print()
    print("--- UTF-8 no BOM files (will just get a BOM added) ---")
    for p in stats["utf8_nobom"]:
        print("  ", p)
    print()
    for enc, lst in sorted(stats["other"].items()):
        print(f"--- Other [{enc}] files (need decode+reencode) ---")
        for p in lst:
            print("  ", p)
    print()
    # Summary counts
    need_conv = len(stats["utf8_nobom"]) + sum(len(v) for v in stats["other"].values())
    print(f"TOTAL files needing conversion: {need_conv}")
    print("="*70)

if __name__ == "__main__":
    main()
