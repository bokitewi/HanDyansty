# -*- coding: utf-8 -*-
"""自制城池所在县：隐藏原版治所（城堡/城市/寺庙/部落/游牧）模型。

做法：把原版治所建筑文件原名复制进 mod（整文件覆盖），在每个治所建筑的
assets 里插入一条只限这些省份的隐形模型 asset（provinces = {...}，
原版说明：省份优先级高于美术区域）。隐形模型 = 原版中式城堡 mesh 缩到 0.001。

原版更新后重跑本脚本即可：python tools/gen_hide_holding_under_city.py
"""
import os
import re

VANILLA = r"D:\SteamLibrary\steamapps\common\Crusader Kings III\game\common\buildings"
MOD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "common", "buildings")

# 省份 -> 城池（注释用）
PROVINCES = {
    4282: "成都 金官城",
    2000: "合肥",
    787: "洛阳",
    1172: "邺城",
    1389: "左国",
    1961: "寿春",
    1788: "襄阳",
    7062: "扬州（广陵）",
    1733: "宛城",
    867: "长安（服装 mod 地图物件）",
    4389: "建康 石头城（槽位）",
    351: "晋阳（槽位）",
    2221: "临淄（槽位）",
    4430: "彭城（槽位）",
    6769: "关城（槽位，无治所）",
    1434: "统万（槽位）",
    2455: "鱼复（槽位）",
    3203: "白帝（槽位）",
}

FILES = {
    "00_castle_buildings.txt": ["castle_01", "castle_02", "castle_03", "castle_04"],
    "00_city_buildings.txt": ["city_01", "city_02", "city_03", "city_04"],
    "00_temple_buildings.txt": ["temple_01", "temple_02", "temple_03", "temple_04"],
    "00_tribal_buildings.txt": ["tribe_01", "tribe_02"],
    "00_nomad_buildings.txt": ["nomadic_camp_01", "herder_camp_01"],
}

MARK = "# HD_HIDE_HOLDING_UNDER_CITY"


def strip_comment(line):
    i = line.find("#")
    return line if i < 0 else line[:i]


def block_end(lines, start):
    depth = 0
    opened = False
    for i in range(start, len(lines)):
        s = strip_comment(lines[i])
        if "{" in s:
            opened = True
        depth += s.count("{") - s.count("}")
        if opened and depth == 0:
            return i
    raise ValueError("unclosed block at %d" % start)


def sub_blocks(lines, start, end, pattern):
    """返回 [start,end] 内匹配 pattern 的子块 (s,e)。"""
    out = []
    i = start + 1
    while i < end:
        if re.match(pattern, strip_comment(lines[i])):
            e = block_end(lines, i)
            out.append((i, e))
            i = e + 1
        else:
            i += 1
    return out


def pick_template(lines, assets):
    # 优先取中式模型（看 name 行，不看 graphical_cultures 列表）作插画/音效参考
    for s, e in assets:
        if any(re.match(r'^\s*name\s*=\s*"[^"]*chinese', l) for l in lines[s:e + 1]):
            return s, e
    return assets[0]


def make_asset(lines, tpl, indent):
    s, e = tpl
    illu = None
    sound = None
    for l in lines[s:e + 1]:
        t = l.strip()
        if illu is None and t.startswith("illustration"):
            illu = t
        if sound is None and t.startswith("soundeffect"):
            sound = t
    ids = " ".join(str(p) for p in PROVINCES)
    out = [
        indent + MARK + "：自制城池所在县不显示原版治所模型（tools/gen_hide_holding_under_city.py 生成）\n",
        indent + "asset = {\n",
        indent + "\ttype = pdxmesh\n",
        indent + "\tname = \"hd_hidden_holding_mesh\"\n",
    ]
    if illu:
        out.append(indent + "\t" + illu + "\n")
    if sound:
        out.append(indent + "\t" + sound + "\n")
    out.append(indent + "\tprovinces = { " + ids + " }\n")
    out.append(indent + "}\n")
    return out


def process(fname, keys):
    with open(os.path.join(VANILLA, fname), encoding="utf-8-sig") as f:
        lines = f.readlines()
    done = []
    for key in keys:
        start = next(i for i, l in enumerate(lines) if re.match(r"^%s\s*=\s*\{" % key, l))
        end = block_end(lines, start)
        ab = sub_blocks(lines, start, end, r"^\s*assets\s*=\s*\{")
        if ab:
            a_s, a_e = ab[0]
            assets = sub_blocks(lines, a_s, a_e, r"^\s*asset\s*=\s*\{")
            insert_at = a_s + 1
        else:
            assets = sub_blocks(lines, start, end, r"^\s*asset\s*=\s*\{")
            insert_at = assets[0][0]
        indent = re.match(r"^(\s*)", lines[assets[0][0]]).group(1)
        new = make_asset(lines, pick_template(lines, assets), indent)
        lines[insert_at:insert_at] = new
        done.append(key)
    header = "# 汉晋春秋：原版文件整份复制，仅在各治所建筑 assets 首位插入 %s 一条（原版更新后重跑生成器）\n" % MARK
    with open(os.path.join(MOD, fname), "w", encoding="utf-8-sig", newline="\n") as f:
        f.write(header)
        f.writelines(lines)
    print(fname, "->", ", ".join(done))


if __name__ == "__main__":
    for fn, ks in FILES.items():
        process(fn, ks)
