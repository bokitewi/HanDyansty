#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 CK3 捏人/Ruler Designer 导出的 DNA 文件（ruler_designer_xxx = { genes={...} override={...} }）
转换为本 mod 的 common/dna_data 格式（hand_<name>_dna = { portrait_info = { genes = {...} } }）。

同时把 override 里的 portrait_modifier_overrides 抽出来，写到
tools/laosanguo_portrait_overrides.txt，供手动插入 history/characters 时使用。

用法：
  python tools/import_ruler_dna.py
可改下面的 SRC / OUT 配置。
"""
import re
import os

MOD = r"E:\documents\Paradox Interactive\Crusader Kings III\mod\HanDyansty"
DESKTOP = r"C:\Users\15550\Desktop\老三国DNA补完计划"

# 人物键名 -> 桌面上的 DNA 源文件
SRC_FILES = {
    "sun_quan":  os.path.join(DESKTOP, "【叁】孙权-吴晓东", "DNA.txt"),
    "zhou_yu":   os.path.join(DESKTOP, "【肆】袁绍＆周瑜-洪宇宙", "周瑜.txt"),
    "dong_zhuo": os.path.join(DESKTOP, "董卓.txt"),
    "liu_bei":   os.path.join(DESKTOP, "【贰】刘备-孙彦军", "DNA_20260509_112641.txt"),
}

DNA_DATA_DIR = os.path.join(MOD, "common", "dna_data")
OUT_DNA_FILE = os.path.join(DNA_DATA_DIR, "hand_laosanguo_dna.txt")
OUT_OV_FILE = os.path.join(MOD, "tools", "laosanguo_portrait_overrides.txt")


def extract_block(text, key):
    """找到 `key={` 并做括号匹配，返回内部文本（不含首尾花括号）。"""
    m = re.search(re.escape(key) + r"\s*=\s*\{", text)
    if not m:
        return None
    start = m.end() - 1  # 第一个 '{' 的位置
    depth = 0
    i = start
    while i < len(text):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1:i]
        i += 1
    return None


def reindent(inner, add="\t"):
    inner = inner.strip("\n")
    out = []
    for line in inner.split("\n"):
        if line.strip() == "":
            out.append("")
        else:
            out.append(add + line)
    return "\n".join(out)


def main():
    entries = {}
    overrides = {}

    for name, path in SRC_FILES.items():
        if not os.path.exists(path):
            print(f"[跳过] 找不到源文件: {path}")
            continue
        with open(path, encoding="utf-8") as f:
            text = f.read()

        genes_inner = extract_block(text, "genes")
        pmo_inner = extract_block(text, "portrait_modifier_overrides")

        if genes_inner is None:
            print(f"[警告] {name}: 未找到 genes 块")
            continue

        wrapped = (
            f"hand_{name}_dna = {{\n"
            f"\tportrait_info = {{\n"
            f"\t\tgenes = {{\n"
            f"{reindent(genes_inner, chr(9))}\n"
            f"\t\t}}\n"
            f"\t}}\n"
            f"}}"
        )
        entries[name] = wrapped

        if pmo_inner is not None:
            ov = (
                "\tportrait_override = {\n"
                "\t\tportrait_modifier_overrides = {\n"
                f"{reindent(pmo_inner, chr(9))}\n"
                "\t\t}\n"
                "\t}"
            )
            overrides[name] = ov

    # 写 dna_data 文件
    os.makedirs(DNA_DATA_DIR, exist_ok=True)
    with open(OUT_DNA_FILE, "w", encoding="utf-8") as f:
        f.write(
            "# DNA 从桌面“老三国DNA补完计划”导入（Ruler Designer 导出，已转为 portrait_info/genes 格式）。\n"
            "# 键名：hand_sun_quan_dna / hand_zhou_yu_dna / hand_dong_zhuo_dna / hand_liu_bei_dna\n"
            "# 对应人物：sun_quan / zhou_yu / dong_zhuo / liu_bei\n\n"
        )
        for name in SRC_FILES:
            if name in entries:
                f.write(entries[name] + "\n\n")

    # 写 override 片段（供插入 history/characters）
    with open(OUT_OV_FILE, "w", encoding="utf-8") as f:
        f.write(
            "# 以下 portrait_override 片段需手动插入对应人物的 history/characters 块\n"
            "# （与 dna = 行同级，放在 name= 之后即可）\n\n"
        )
        for name in SRC_FILES:
            f.write(f"# ===== {name} =====\n")
            if name in overrides:
                f.write(overrides[name] + "\n\n")
            else:
                f.write("# (无 override)\n\n")

    print(f"已写入 DNA 数据: {OUT_DNA_FILE}")
    print(f"已写入 override: {OUT_OV_FILE}")
    for name in SRC_FILES:
        print(f"  {name}: dna={'Y' if name in entries else 'N'}  override={'Y' if name in overrides else 'N'}")


if __name__ == "__main__":
    main()
