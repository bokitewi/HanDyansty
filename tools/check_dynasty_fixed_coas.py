# -*- coding: utf-8 -*-
"""自检 zz_hd_dynasty_fixed_coas.txt：覆盖、重名、贴图、颜色、括号。"""
import os, re, struct, collections
MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLOTHES = os.path.join(os.path.dirname(MOD), "HanJIn_Clothes")
VAN = "D:/SteamLibrary/steamapps/common/Crusader Kings III/game"
NEW = os.path.join(MOD, "common/coat_of_arms/coat_of_arms/zz_hd_dynasty_fixed_coas.txt")
rd = lambda p: open(p, encoding="utf-8-sig", errors="ignore").read()
tex = {}
for r in (VAN, MOD, CLOTHES):
    for k in ("colored_emblems", "patterns", "textured_emblems"):
        d = os.path.join(r, "gfx/coat_of_arms", k)
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.lower().endswith(".dds"):
                    b = open(os.path.join(d, f), "rb").read(20)
                    hh, ww = struct.unpack("<II", b[12:20]) if b[:4] == b"DDS " else (0, 1)
                    tex[f.lower()] = (ww, hh)
colors = set()
for r in (VAN, MOD, CLOTHES):
    d = os.path.join(r, "common/named_colors")
    if os.path.isdir(d):
        for f in os.listdir(d):
            colors |= set(re.findall(r"^\s*([A-Za-z0-9_]+)\s*=", re.sub(r"#[^\n]*", "", rd(os.path.join(d, f))), re.M))
others = collections.Counter()
for r in (VAN, MOD, CLOTHES):
    d = os.path.join(r, "common/coat_of_arms/coat_of_arms")
    if os.path.isdir(d):
        for f in os.listdir(d):
            if f.endswith(".txt") and f != os.path.basename(NEW):
                for k in re.findall(r"^([A-Za-z0-9_\.\-]+)\s*=", rd(os.path.join(d, f)), re.M): others[k] += 1
t = re.sub(r"#[^\n]*", "", rd(NEW))
errs = []
if t.count("{") != t.count("}"): errs.append(f"括号不配平 {t.count('{')} vs {t.count('}')}")
keys = re.findall(r"^([A-Za-z0-9_\.\-]+)\s*=\s*\{", t, re.M)
dup = [k for k, c in collections.Counter(keys).items() if c > 1]
clash = [k for k in keys if k in others]
for tx in re.findall(r'(?:texture|pattern)\s*=\s*"([^"]+)"', t):
    s = tex.get(tx.lower())
    if not s: errs.append("缺贴图 " + tx)
    elif s[0] != s[1]: errs.append("非方形贴图 " + tx)
for c in re.findall(r"color\d\s*=\s*\"?([A-Za-z_][A-Za-z0-9_]*)", t):
    if c not in colors and not re.fullmatch(r"color\d", c): errs.append("未定义颜色 " + c)
# 覆盖
allk = set(others) | set(keys)
miss = []
dd = os.path.join(MOD, "common/dynasties")
for f in os.listdir(dd):
    if f.endswith(".txt"):
        for k in re.findall(r"^([A-Za-z0-9_\.\-]+)\s*=\s*\{", re.sub(r"#[^\n]*", "", rd(os.path.join(dd, f))), re.M):
            if k not in allk: miss.append(k)
print("条目", len(keys), "重复", dup[:5], "与已有重名", clash[:5], "仍无纹章王朝", len(miss), miss[:10])
print("错误", len(errs), collections.Counter(errs).most_common(10))
