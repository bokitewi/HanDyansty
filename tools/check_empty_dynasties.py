# -*- coding: utf-8 -*-
"""
检查模组中是否存在「孤儿宗族/家族」：
- 在 common/dynasties 或 common/dynasty_houses 中定义了 ID，
- 但在 history/characters 中没有任何角色（含历史角色）引用它。

同时输出：
- house -> dynasty 映射中指向不存在 dynasty 的悬空引用
- 角色引用不存在 house 的悬空引用

用法: python check_empty_dynasties.py [模组根目录]
"""
import os
import re
import sys
from collections import defaultdict

MOD_ROOT = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
DYNASTY_DIR = os.path.join(MOD_ROOT, "common", "dynasties")
HOUSE_DIR = os.path.join(MOD_ROOT, "common", "dynasty_houses")
CHAR_DIR = os.path.join(MOD_ROOT, "history", "characters")

# ---------------- 基础解析 ----------------

def strip_comments(text):
    """去掉以 # 开头（前面只有空白）的注释行。保留引号内内容（极少数情况），这里简单处理。"""
    out = []
    for line in text.split("\n"):
        # 找到行首注释
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        out.append(line)
    return "\n".join(out)


def parse_top_level_blocks(text):
    """解析顶层键值块：id = { ... }。返回 {id: 块内文本}。"""
    text = strip_comments(text)
    blocks = {}
    i = 0
    n = len(text)
    # 匹配顶层键
    while i < n:
        # 跳过空白和标点
        m = re.compile(r"^\s*([A-Za-z0-9_]+)\s*=\s*\{", re.M).search(text, i)
        if not m:
            break
        key = m.group(1)
        start = m.end() - 1  # 指向 '{'
        depth = 0
        j = start
        while j < n:
            c = text[j]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        block = text[start + 1:j]
        blocks[key] = block
        i = j + 1
    return blocks


def load_defs(directory, file_suffix):
    """加载目录下所有定义文件的顶层块。返回 {id: 块内容}"""
    defs = {}
    if not os.path.isdir(directory):
        return defs
    for fn in sorted(os.listdir(directory)):
        if fn.endswith(".txt"):
            with open(os.path.join(directory, fn), encoding="utf-8-sig", errors="replace") as f:
                text = f.read()
            for key, block in parse_top_level_blocks(text).items():
                defs[key] = block
    return defs


def extract_house_of_block(block):
    """从 house 定义块中提取 dynasty 引用。返回 dynasty id 或 None。"""
    m = re.search(r"\bdynasty\s*=\s*[\"']?([A-Za-z0-9_]+)[\"']?", block)
    return m.group(1) if m else None


def load_character_house_refs(directory):
    """加载所有角色文件中引用的 house/dynasty id。返回 (house_refs, dynasty_refs)"""
    house_refs = set()
    dynasty_refs = set()
    if not os.path.isdir(directory):
        return house_refs, dynasty_refs
    for fn in sorted(os.listdir(directory)):
        if fn.endswith(".txt"):
            with open(os.path.join(directory, fn), encoding="utf-8-sig", errors="replace") as f:
                text = f.read()
            text = strip_comments(text)
            for m in re.finditer(r"\bdynasty_house\s*=\s*[\"']?([A-Za-z0-9_]+)[\"']?", text):
                house_refs.add(m.group(1))
            for m in re.finditer(r"\bhouse\s*=\s*[\"']?([A-Za-z0-9_]+)[\"']?", text):
                house_refs.add(m.group(1))
            for m in re.finditer(r"\bdynasty\s*=\s*[\"']?([A-Za-z0-9_]+)[\"']?", text):
                dynasty_refs.add(m.group(1))
    return house_refs, dynasty_refs


# ---------------- 主流程 ----------------

print("=" * 70)
print("模组根目录:", MOD_ROOT)
print("=" * 70)

dynasty_defs = load_defs(DYNASTY_DIR, ".txt")
house_defs = load_defs(HOUSE_DIR, ".txt")
print(f"宗族(dynasty)定义总数: {len(dynasty_defs)}")
print(f"家族(house)定义总数:   {len(house_defs)}")

# house -> dynasty 映射
house_dynasty = {}
for hid, block in house_defs.items():
    d = extract_house_of_block(block)
    house_dynasty[hid] = d

# 角色引用
house_refs, dynasty_refs = load_character_house_refs(CHAR_DIR)
print(f"角色引用的 house 数量: {len(house_refs)}")
print(f"角色直接引用的 dynasty 数量: {len(dynasty_refs)}")

# ---- 1. 空 house ----
empty_houses = sorted(set(house_defs) - house_refs)
# ---- 2. 空 dynasty ----
# 有成员 house 的 dynasty
used_dynasties = set(dynasty_refs)
for hid in house_refs:
    if hid in house_dynasty:
        used_dynasties.add(house_dynasty[hid])
empty_dynasties = sorted(set(dynasty_defs) - used_dynasties)

# ---- 3. 悬空引用检查 ----
dangling_house_def = sorted(h for h, d in house_dynasty.items() if d is not None and d not in dynasty_defs)
dangling_char_house = sorted(house_refs - set(house_defs))
dangling_char_dyn = sorted(dynasty_refs - set(dynasty_defs))

print()
print("-" * 70)
print("【结论】完全空的家族(house) —— 已定义但无任何角色（含历史角色）引用:")
print("-" * 70)
if empty_houses:
    print(f"共 {len(empty_houses)} 个:\n")
    for hid in empty_houses:
        d = house_dynasty.get(hid)
        d_str = f" -> 宗族 {d}" if d else " -> (无 dynasty 字段)"
        print(f"  {hid}{d_str}")
else:
    print("  (无)")

print()
print("-" * 70)
print("【结论】完全空的宗族(dynasty) —— 已定义、无角色直接引用、且其下属 house 也无人引用:")
print("-" * 70)
if empty_dynasties:
    print(f"共 {len(empty_dynasties)} 个:\n")
    for did in empty_dynasties:
        print(f"  {did}")
else:
    print("  (无)")

print()
print("-" * 70)
print("【悬空引用】house 定义中指向不存在 dynasty 的引用:")
print("-" * 70)
if dangling_house_def:
    for h in dangling_house_def:
        print(f"  house {h} -> dynasty {house_dynasty[h]} (未在 common/dynasties 中找到)")
else:
    print("  (无)")

print()
print("-" * 70)
print("【悬空引用】角色引用了不存在的 house:")
print("-" * 70)
if dangling_char_house:
    print(f"共 {len(dangling_char_house)} 个（可能引用原版 house，需人工确认）:")
    for h in dangling_char_house[:50]:
        print(f"  {h}")
    if len(dangling_char_house) > 50:
        print(f"  ... 等共 {len(dangling_char_house)} 个")
else:
    print("  (无)")

print()
print("-" * 70)
print("【悬空引用】角色直接引用了不存在的 dynasty:")
print("-" * 70)
if dangling_char_dyn:
    for d in dangling_char_dyn:
        print(f"  {d}")
else:
    print("  (无)")

# 保存详细报告
report_path = os.path.join(MOD_ROOT, "tools", "empty_dynasty_report.txt")
with open(report_path, "w", encoding="utf-8") as f:
    f.write("完全空的家族(house) 共 %d 个:\n" % len(empty_houses))
    for hid in empty_houses:
        d = house_dynasty.get(hid)
        f.write(f"  {hid}" + (f" -> 宗族 {d}" if d else "") + "\n")
    f.write("\n完全空的宗族(dynasty) 共 %d 个:\n" % len(empty_dynasties))
    for did in empty_dynasties:
        f.write(f"  {did}\n")
    f.write("\nhouse->dynasty 悬空引用:\n")
    for h in dangling_house_def:
        f.write(f"  {h} -> {house_dynasty[h]}\n")
    f.write("\n角色引用不存在的 house:\n")
    for h in dangling_char_house:
        f.write(f"  {h}\n")
    f.write("\n角色直接引用不存在的 dynasty:\n")
    for d in dangling_char_dyn:
        f.write(f"  {d}\n")
print(f"\n详细报告已保存: {report_path}")
