#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify: after conversion, count any text file in the MOD (excluding VCS/IDE
dirs) that is NOT UTF-8-BOM. Should be 0."""
import os

ROOT = r"E:\documents\Paradox Interactive\Crusader Kings III\mod\HanDyansty"
EXCLUDE_DIRS = {".git", ".vscode", ".workbuddy", "__pycache__"}
TEXT_EXTS = {
    ".txt", ".yml", ".gui", ".mod", ".csv", ".json", ".info", ".lua",
    ".bce_source", ".ionfo", ".disabled", ".map", ".cfg", ".py", ".gitattributes",
    ".gitignore", ".markdown", ".md",
}
BINARY_EXTS = {
    ".dds", ".png", ".jpg", ".jpeg", ".bmp", ".tga", ".tif", ".tiff",
    ".mesh", ".asset", ".blend", ".blend1", ".obj", ".fbx", ".wav", ".ogg",
    ".mp3", ".ttf", ".bin", ".exe", ".dll", ".zip", ".7z", ".rar", ".pyc",
}
BOM = b"\xef\xbb\xbf"


def is_binary(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in BINARY_EXTS:
        return True
    if ext not in TEXT_EXTS:
        try:
            with open(path, "rb") as f:
                if b"\x00" in f.read(4096):
                    return True
        except Exception:
            return True
    return False


bad = []
bom = 0
binary = 0
for dirpath, dirnames, filenames in os.walk(ROOT):
    rel = os.path.relpath(dirpath, ROOT)
    if any(p in EXCLUDE_DIRS for p in rel.split(os.sep)):
        continue
    for fn in filenames:
        full = os.path.join(dirpath, fn)
        if is_binary(full):
            binary += 1
            continue
        try:
            raw = open(full, "rb").read()
        except Exception:
            binary += 1
            continue
        if raw.startswith(BOM):
            bom += 1
        else:
            bad.append(full)

print(f"UTF-8-BOM (ok)      : {bom}")
print(f"Binary skipped      : {binary}")
print(f"NON-BOM text files  : {len(bad)}  <-- should be 0")
for p in bad:
    print("  BAD:", p)
print("VERIFY OK" if not bad else "VERIFY FAILED")
