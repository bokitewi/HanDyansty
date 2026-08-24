#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Batch convert project text files to UTF-8 with BOM.

Safety rules:
- EXCLUDES VCS / IDE / agent internal dirs (.git, .vscode, .workbuddy, __pycache__).
- Only touches text files; binary files are detected and skipped.
- For files that are valid UTF-8 without BOM, we prepend a BOM byte-for-byte
  (content unchanged, only BOM added) -> zero risk of corruption.
- Files already UTF-8-BOM are left untouched.
- Files in another encoding (rare) are decoded with a best-effort fallback and
  re-encoded as UTF-8-BOM; these are reported separately for review.
- A timestamped backup of every changed file is written OUTSIDE the mod folder
  so the operation is fully reversible.
"""
import os
import shutil
import datetime

ROOT = r"E:\documents\Paradox Interactive\Crusader Kings III\mod\HanDyansty"
TS = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_ROOT = os.path.join(
    r"E:\documents\Paradox Interactive\Crusader Kings III",
    f"utf8bom_backup_{TS}",
)

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


def is_probably_binary(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in BINARY_EXTS:
        return True
    if ext not in TEXT_EXTS:
        try:
            with open(path, "rb") as f:
                chunk = f.read(4096)
            if b"\x00" in chunk:
                return True
        except Exception:
            return True
    return False


def categorize(raw):
    """Return one of: 'bom', 'utf8', 'other:<enc>', 'binary-safe'."""
    if raw.startswith(BOM):
        return "bom"
    try:
        raw.decode("utf-8")
        return "utf8"
    except UnicodeDecodeError:
        pass
    for enc in ("gbk", "gb18030", "cp1252", "latin-1"):
        try:
            raw.decode(enc)
            return "other:" + enc
        except UnicodeDecodeError:
            continue
    return "other:unknown"


def main():
    converted = []          # (src, backup, mode)
    skipped_bom = 0
    skipped_binary = 0
    other_files = []        # need decode+reencode
    errors = []

    for dirpath, dirnames, filenames in os.walk(ROOT):
        rel = os.path.relpath(dirpath, ROOT)
        parts = rel.split(os.sep)
        if any(p in EXCLUDE_DIRS for p in parts):
            continue
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            if is_probably_binary(full):
                skipped_binary += 1
                continue
            try:
                with open(full, "rb") as f:
                    raw = f.read()
            except Exception as e:
                errors.append((full, str(e)))
                continue
            if len(raw) == 0:
                # empty file: nothing to add; treat as already-correct
                skipped_bom += 1
                continue
            cat = categorize(raw)
            if cat == "bom":
                skipped_bom += 1
                continue
            if cat == "utf8":
                # byte-exact: prepend BOM only
                backup = os.path.join(BACKUP_ROOT, rel, fn)
                os.makedirs(os.path.dirname(backup), exist_ok=True)
                shutil.copy2(full, backup)
                try:
                    with open(full, "wb") as f:
                        f.write(BOM + raw)
                    converted.append((full, backup, "add_bom"))
                except Exception as e:
                    errors.append((full, str(e)))
                continue
            # other encoding
            enc = cat.split(":", 1)[1]
            other_files.append((full, enc))

    # Handle "other" encodings (decode + reencode) if any
    for full, enc in other_files:
        try:
            with open(full, "rb") as f:
                raw = f.read()
            text = raw.decode(enc)
            backup = os.path.join(BACKUP_ROOT, os.path.relpath(full, ROOT))
            os.makedirs(os.path.dirname(backup), exist_ok=True)
            shutil.copy2(full, backup)
            with open(full, "w", encoding="utf-8-sig", newline="") as f:
                f.write(text)
            converted.append((full, backup, f"reencode:{enc}"))
        except Exception as e:
            errors.append((full, f"{enc}:{e}"))

    # Write a manifest of what was converted
    os.makedirs(BACKUP_ROOT, exist_ok=True)
    manifest = os.path.join(BACKUP_ROOT, "CONVERTED_MANIFEST.txt")
    with open(manifest, "w", encoding="utf-8") as f:
        f.write(f"UTF-8-BOM conversion @ {TS}\n")
        f.write(f"Source root: {ROOT}\n")
        f.write(f"Backup root: {BACKUP_ROOT}\n")
        f.write(f"Total converted: {len(converted)}\n\n")
        for src, backup, mode in converted:
            f.write(f"[{mode}] {src}\n    backup -> {backup}\n")

    print("=" * 70)
    print("UTF-8-BOM CONVERSION COMPLETE")
    print("=" * 70)
    print(f"Files converted      : {len(converted)}")
    print(f"  - add_bom only     : {sum(1 for c in converted if c[2]=='add_bom')}")
    print(f"  - reencoded        : {sum(1 for c in converted if c[2].startswith('reencode'))}")
    print(f"Already UTF-8-BOM    : {skipped_bom}")
    print(f"Binary skipped       : {skipped_binary}")
    print(f"Non-UTF8 (reencoded) : {len(other_files)}")
    print(f"Errors               : {len(errors)}")
    print(f"Backup root          : {BACKUP_ROOT}")
    if errors:
        print("\nERRORS:")
        for p, e in errors:
            print("  ", p, "->", e)
    print("=" * 70)


if __name__ == "__main__":
    main()
