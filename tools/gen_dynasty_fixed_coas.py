# -*- coding: utf-8 -*-
"""给没有纹章的王朝生成固定纹章 -> common/coat_of_arms/coat_of_arms/zz_hd_dynasty_fixed_coas.txt

背景：2026-10-18 玩家反馈展示「郑宗族旗」(dynasty 旗)必闪退，该王朝原无纹章、开局随机生成。
规则（已与 boki 确认）：
  1. 下属家族有手写纹章 -> 照抄家族纹章
  2. 东亚以外文化 -> 照抄同文化(或同区域)原版王朝纹章
  3. 姓氏可对上字图 -> 姓氏印章（纯色底 + 外圈纹框 + 姓氏字）
  4. 其余 -> 纹框 + 图腾兜底
配色/纹框/图腾按王朝键 crc32 选取，可重复生成；跳过 256x252 非常规贴图。
用法：python -I tools/gen_dynasty_fixed_coas.py
"""
import os, re, sys, zlib, struct, collections

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODS = os.path.dirname(MOD)
CLOTHES = os.path.join(MODS, "HanJIn_Clothes")
VAN = "D:/SteamLibrary/steamapps/common/Crusader Kings III/game"
OUT_NAME = "zz_hd_dynasty_fixed_coas.txt"
OUT = os.path.join(MOD, "common/coat_of_arms/coat_of_arms", OUT_NAME)
GEN_FAMILY = os.path.join(MOD, "common/coat_of_arms/coat_of_arms/zz_dm_bce_generated_family_coas.txt")

# 东亚以外文化 -> 地区样式（原版图案列表：外框列表, 中心图案列表, 底纹列表）
REGION_STYLE = {
    "south_asia": ("indian_circled_frame_list", "indian_centered_symbol_list", None),
    "west_regions": ("mena_circled_frame_list", "mena_base_charges_list", None),
    "maghreb": ("mena_circled_frame_list", "base_islamic_charge_list", None),
    "southeast_asia": (None, "khmer_central", None),
    "europe": (None, "hr_medium_charges_list", "basic_division"),
}
FOREIGN = {
    "kashmiri": "south_asia",
    "sogdian": "west_regions", "saka": "west_regions", "tocharian": "west_regions",
    "kucha": "west_regions", "shule": "west_regions", "khotan": "west_regions", "cheshi": "west_regions",
    "dayuan": "west_regions", "kangju": "west_regions", "wusun": "west_regions",
    "khmer": "southeast_asia", "mon": "southeast_asia", "tagalog": "southeast_asia", "iloko": "southeast_asia",
    "welsh": "europe", "castilian": "europe", "maghrebi": "maghreb",
}


def read(p):
    return open(p, encoding="utf-8-sig", errors="ignore").read()


def strip_comments(t):
    return re.sub(r"#[^\n]*", "", t)


def top_blocks(text):
    """顶层 key = { ... }，返回 [(key, body_without_outer_braces)]；忽略 key = value 别名。"""
    t = strip_comments(text)
    out, i, n = [], 0, len(t)
    pat = re.compile(r"([A-Za-z0-9_\.\-@]+)\s*=\s*(\{)?")
    depth = 0
    while i < n:
        c = t[i]
        if depth == 0:
            m = pat.match(t, i)
            if m:
                if m.group(2):
                    key, j, d = m.group(1), m.end(), 1
                    while j < n and d:
                        if t[j] == "{": d += 1
                        elif t[j] == "}": d -= 1
                        j += 1
                    out.append((key, t[m.end():j - 1]))
                    i = j
                    continue
                i = m.end()
                continue
        i += 1
    return out


def dds_ok(p):
    try:
        b = open(p, "rb").read(20)
        if b[:4] != b"DDS ": return False
        h, w = struct.unpack("<II", b[12:20])
        return h == w  # 排除 256x252 等非方形图；600x600 BC7 已证实可在旗上渲染
    except OSError:
        return False


# ---------- 贴图 ----------
tex_ok = {}
for root in (VAN, MOD, CLOTHES):
    for k in ("colored_emblems", "patterns", "textured_emblems"):
        d = os.path.join(root, "gfx/coat_of_arms", k)
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.lower().endswith(".dds"):
                    tex_ok[f.lower()] = dds_ok(os.path.join(d, f)) or root == VAN


def textures_fine(body):
    for tx in re.findall(r'(?:texture|pattern)\s*=\s*"([^"]+)"', body):
        if not tex_ok.get(tx.lower(), False):
            return False
    return True


# ---------- 已有纹章键 ----------
coa_keys = set()
for root in (VAN, MOD, CLOTHES):
    d = os.path.join(root, "common/coat_of_arms/coat_of_arms")
    if not os.path.isdir(d): continue
    for f in os.listdir(d):
        if f.endswith(".txt") and f != OUT_NAME:
            coa_keys |= set(re.findall(r"^([A-Za-z0-9_\.\-]+)\s*=", read(os.path.join(d, f)), re.M))

# mod 纹章块（供照抄家族）
mod_coa_body = {}
for root in (MOD, CLOTHES):
    d = os.path.join(root, "common/coat_of_arms/coat_of_arms")
    if not os.path.isdir(d): continue
    for f in sorted(os.listdir(d)):
        if f.endswith(".txt") and f != OUT_NAME:
            for k, b in top_blocks(read(os.path.join(d, f))):
                mod_coa_body[k] = b

# ---------- 王朝 ----------
dyn = collections.OrderedDict()
dd = os.path.join(MOD, "common/dynasties")
for f in sorted(os.listdir(dd)):
    if not f.endswith(".txt"): continue
    for k, b in top_blocks(read(os.path.join(dd, f))):
        c = re.search(r'culture\s*=\s*"?([A-Za-z0-9_]+)', b)
        nm = re.search(r'name\s*=\s*"?([^"\s]+)', b)
        dyn.setdefault(k, (f, c.group(1) if c else "", nm.group(1) if nm else ""))
missing = [k for k in dyn if k not in coa_keys]

# ---------- 本地化 ----------
loc = {}
for L in (os.path.join(MOD, "localization/simp_chinese"), os.path.join(VAN, "localization/simp_chinese")):
    for root, _, fs in os.walk(L):
        if "replace" in root.replace("\\", "/").split("/") and L.startswith(VAN): continue
        for f in fs:
            if f.endswith(".yml"):
                for line in read(os.path.join(root, f)).splitlines():
                    m = re.match(r'\s*([^\s:#]+):\d*\s*"(.*)"', line)
                    if m: loc.setdefault(m.group(1), m.group(2))

# ---------- 现有生成纹章：姓氏字图、样式 ----------
gen = read(GEN_FAMILY)
surname_tex = collections.defaultdict(collections.Counter)
seal_styles, totem_styles, totem_emblems = [], [], set()
EMB = re.compile(r'colored_emblem\s*=\s*\{\s*color1\s*=\s*(\w+)\s*color2\s*=\s*(\w+)\s*texture\s*=\s*"([^"]+)"')
HEAD = re.compile(r'pattern\s*=\s*"([^"]+)"\s*color1\s*=\s*(\w+)\s*color2\s*=\s*(\w+)\s*color3\s*=\s*(\w+)')
for m in re.finditer(r"# dynasty (\S+): (surname seal|BCE totem fallback)\n[A-Za-z0-9_\.\-]+ = \{(.*?)\n\}", gen, re.S):
    body = m.group(3)
    h = HEAD.search(body); es = EMB.findall(body)
    if not h or len(es) != 2: continue
    rot = re.findall(r"rotation\s*=\s*(\d+)", body)
    style = (h.groups(), es[0], (es[1][0], es[1][1]), rot[0] if rot else "0")
    if not textures_fine(body): continue
    if m.group(2) == "surname seal":
        s = loc.get(m.group(1), "")
        if s: surname_tex[s][es[1][2]] += 1
        seal_styles.append(style)
    else:
        totem_styles.append(style)
        totem_emblems.add(es[1][2])
surname_tex = {s: c.most_common(1)[0][0] for s, c in surname_tex.items()}
seal_styles = sorted(set(seal_styles)); totem_styles = sorted(set(totem_styles))
totem_emblems = sorted(totem_emblems)

# ---------- 原版图案列表（东亚以外） ----------
def van_lists(fname):
    t = strip_comments(read(os.path.join(VAN, "common/coat_of_arms/template_lists", fname)))
    res, stack = collections.defaultdict(list), []
    for m in re.finditer(r'([A-Za-z0-9_]+)\s*=\s*\{|\{|\}|\d+\s*=\s*"?([A-Za-z0-9_\.]+)"?', t):
        g = m.group(0)
        if g == "}":
            if stack: stack.pop()
        elif m.group(1):
            stack.append(m.group(1))
        elif g == "{":
            stack.append(None)
        elif m.group(2) and len(stack) >= 2:
            res[stack[1]].append(m.group(2))
    return res
VL = van_lists("colored_emblem_lists.txt")
PL = van_lists("pattern_lists.txt")
CL = van_lists("color_lists.txt")
def uniq_ok(xs, tex=True):
    out = []
    for x in xs:
        if x not in out and (not tex or tex_ok.get(x.lower(), False)): out.append(x)
    return out
NORMAL = uniq_ok(CL["normal_colors"], tex=False)
METAL = uniq_ok(CL["metal_colors"], tex=False)

# ---------- 家族纹章 ----------
house_for = {}
hd = os.path.join(MOD, "common/dynasty_houses")
for f in sorted(os.listdir(hd)):
    if not f.endswith(".txt"): continue
    for k, b in top_blocks(read(os.path.join(hd, f))):
        m = re.search(r'dynasty\s*=\s*"?([A-Za-z0-9_\.\-]+)', b)
        if not m or k not in mod_coa_body: continue
        dk = m.group(1)
        if dk in house_for and not k.endswith(dk): continue
        if textures_fine(mod_coa_body[k]): house_for[dk] = k


def h(key, salt):
    return zlib.crc32((salt + key).encode("utf-8"))


def indent(body):
    lines = [l.rstrip() for l in body.strip("\n").splitlines() if l.strip()]
    # 统一缩进为一个 tab 起
    import textwrap
    return "\n".join("\t" + l for l in textwrap.dedent("\n".join(lines)).splitlines())


def layered(key, style, tex2, scale, frame_tex=None):
    (pat, c1, c2, c3), (f1, f2, ftex), (e1, e2), rot = style
    ftex = frame_tex or ftex
    return (f'\tpattern = "{pat}"\n\tcolor1 = {c1}\n\tcolor2 = {c2}\n\tcolor3 = {c3}\n'
            f'\tcolored_emblem = {{\n\t\tcolor1 = {f1}\n\t\tcolor2 = {f2}\n\t\ttexture = "{ftex}"\n'
            f'\t\tinstance = {{\n\t\t\tposition = {{ 0.5 0.5 }}\n\t\t\tscale = {{ 1.0 1.0 }}\n\t\t}}\n\t}}\n'
            f'\tcolored_emblem = {{\n\t\tcolor1 = {e1}\n\t\tcolor2 = {e2}\n\t\ttexture = "{tex2}"\n'
            f'\t\tinstance = {{\n\t\t\tposition = {{ 0.5 0.5 }}\n\t\t\tscale = {{ {scale} {scale} }}\n\t\t\trotation = {rot}\n\t\t}}\n\t}}')


def emblem(c1, c2, tex, scale):
    return ("\tcolored_emblem = {\n"
            f"\t\tcolor1 = {c1}\n\t\tcolor2 = {c2}\n\t\ttexture = \"{tex}\"\n"
            "\t\tinstance = {\n\t\t\tposition = { 0.5 0.5 }\n"
            f"\t\t\tscale = {{ {scale} {scale} }}\n\t\t}}\n\t}}")


def foreign_coa(key, region):
    frame_l, center_l, pat_l = REGION_STYLE[region]
    bg = NORMAL[h(key, "fc1") % len(NORMAL)]
    bg2 = NORMAL[(h(key, "fc1") + 3) % len(NORMAL)]
    mt = METAL[h(key, "fc2") % len(METAL)]
    pats = uniq_ok(PL[pat_l]) if pat_l else []
    pat = pats[h(key, "fp") % len(pats)] if pats else "pattern_solid.dds"
    centers = uniq_ok(VL[center_l])
    ctex = centers[h(key, "fe") % len(centers)]
    parts = [f"\tpattern = \"{pat}\"\n\tcolor1 = {bg}\n\tcolor2 = {bg2}\n\tcolor3 = {mt}"]
    scale = "0.75"
    if frame_l:
        frames = uniq_ok(VL[frame_l])
        parts.append(emblem(mt, bg, frames[h(key, "ff") % len(frames)], "1.0"))
        scale = "0.55"
    parts.append(emblem(mt, bg, ctex, scale))
    return "\n".join(parts)



out, stats, unmatched_foreign = [], collections.Counter(), []
for k in missing:
    f, cul, nm = dyn[k]
    sname = loc.get(nm, "")
    if k in house_for:
        body, kind = indent(mod_coa_body[house_for[k]]), f"照抄家族 {house_for[k]}"
    elif cul in FOREIGN:
        body, kind = foreign_coa(k, FOREIGN[cul]), f"原版图案 {FOREIGN[cul]}"
    elif sname in surname_tex:
        st = seal_styles[h(k, "s") % len(seal_styles)]
        body, kind = layered(k, st, surname_tex[sname], 0.62), f"姓氏印章 {sname}"
    else:
        st = totem_styles[h(k, "t") % len(totem_styles)]
        body, kind = layered(k, st, totem_emblems[h(k, "e") % len(totem_emblems)], 0.58), "纹框图腾"
    stats[kind.split(" ")[0]] += 1
    out.append(f"# {k} | {f} | {cul or '-'} | {sname or nm} | {kind}\n{k} = {{\n{body}\n}}\n")

with open(OUT, "w", encoding="utf-8-sig", newline="\n") as fo:
    fo.write("# 由 tools/gen_dynasty_fixed_coas.py 生成，勿手改；新增王朝后重跑\n"
             "# 给原本无纹章（开局随机生成）的王朝补固定纹章，起因：郑宗族旗展示闪退（2026-10-18）\n\n")
    fo.write("\n".join(out))

print("missing", len(missing), "written", len(out), dict(stats))
print("surname map", len(surname_tex), "seal styles", len(seal_styles), "totem styles", len(totem_styles), "emblems", len(totem_emblems))
print("region lists", {r: [len(uniq_ok(VL[x])) if x in VL or x is None and False else (len(uniq_ok(PL[x])) if x else 0) for x in v] for r, v in REGION_STYLE.items()}, "colors", len(NORMAL), len(METAL))
print("unmatched foreign", unmatched_foreign)
