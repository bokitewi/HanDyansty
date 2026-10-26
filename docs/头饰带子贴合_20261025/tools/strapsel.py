"""Strap selection for TW3K-converted headgear (2026-10-25)."""
import sys, os, json
sys.path.insert(0, r"D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\56745149-66b1-475a-8105-eeaf35fa0c2a\scratchpad\hg")
from hglib import *

CLOTHES = r"E:\documents\Paradox Interactive\Crusader Kings III\mod\HanJIn_Clothes\gfx\models\portraits\m_headgear"
BACKUP = r"E:\documents\Paradox Interactive\Crusader Kings III\mod\HanDyansty\docs\头饰外扩_备份_20261019"
CHIN_Y = {"m": 34.1, "f": 32.8}

# folder -> options. cap: hair visible under it (keep strap above hairline). src: 'backup' = revert 10-19 inflate first.
HATS = {
    "hd_liu_shi_crown_01": dict(cap=True, src="backup"),
    "hd_belka_lu_bu_01": dict(cap=True, src="backup"),
    "hd_eastern_han_armor_02": dict(),
    "hd_eastern_han_armor_03": dict(),
    "hd_pingshangze_01": dict(),
    "hd_historic_formation_breakers_01": dict(),
    "hd_historic_sabre_light_01": dict(),
    "hd_historic_sabre_militia_wrap_01": dict(),
    "hd_historic_spear_guards_01": dict(),
    "hd_historic_yulin_crossbow_helmet_01": dict(),
    "hd_historic_heaven_guards_01": dict(),
    "hd_historic_jian_guards_01": dict(),
    "hd_yulin_helmet_01": dict(),
    "hd_frontier_crossbow_cap": dict(),
    "hd_frontier_xiongnu_noble_cap": dict(),
    "hd_frontier_xiongnu_bronze": dict(),
    "hd_frontier_xiongnu_iron": dict(),
    "hd_frontier_xianbei_iron": dict(),
    "hd_frontier_xianbei_long": dict(),
    "hd_frontier_xianbei_pattern": dict(),
}
# manual corrections after visual review: (folder, sex, shape-suffix, comp) -> True include / False exclude
OVERRIDE = {
    ("hd_historic_sabre_militia_wrap_01", "m", "wrapShape", 0): False,
    ("hd_historic_sabre_militia_wrap_01", "f", "wrapShape", 0): False,
    ("hd_historic_spear_guards_01", "m", "headclothShape", 2): False,
    ("hd_historic_spear_guards_01", "f", "headclothShape", 2): False,
    ("hd_frontier_crossbow_cap", "f", "b0c706dcShape", 12): False,
}

def files_for(folder):
    out = []
    for sex in ("m", "f"):
        fn = f"{sex}_headgear_{folder}.mesh"
        cur = os.path.join(CLOTHES, folder, fn)
        if os.path.exists(cur):
            out.append((sex, fn))
    return out

def src_path(folder, fn):
    if HATS[folder].get("src") == "backup":
        b = os.path.join(BACKUP, folder, fn)
        if os.path.exists(b):
            return b
    return os.path.join(CLOTHES, folder, fn)

def select(folder, sex, sh):
    """returns per shape: dict(mask, comp, kind) where kind[c] in {'main','knot',None}"""
    chin = CHIN_Y[sex]
    res = []
    for s in sh:
        P, T = s["P"], s["T"]
        comp = components(P, T)
        nc = comp.max() + 1
        kind = [None] * nc
        rope = "ropeShape" in s["name"]
        plume = "plume" in s["name"].lower()
        for c in range(nc):
            m = comp == c; Q = P[m]
            lo, hi = Q.min(0), Q.max(0)
            ov = OVERRIDE.get((folder, sex, s["name"].split("_")[-1], c))
            if plume and ov is None:
                continue
            knot = hi[1] < chin + 1.5 and np.abs(Q[:, 0]).max() < 7 and lo[2] < -5 and m.sum() <= 120
            if rope or HATS[folder].get("cap") and "headcloth" in s["name"]:
                cand = True
            else:
                cand = knot or (lo[1] < 37.5 and lo[2] < -5 and 10 <= m.sum() < 400 and hi[2] - lo[2] <= 16)
            if ov is not None:
                cand = ov
            if not cand:
                continue
            kind[c] = "knot" if knot else "main"
        res.append(dict(comp=comp, kind=kind))
    if not any(k == "main" for r in res for k in r["kind"]):
        for r in res:
            r["kind"] = [None] * len(r["kind"])
    for r in res:
        r["mask"] = np.array([r["kind"][c] is not None for c in r["comp"]])
    return res

if __name__ == "__main__":
    out = {}
    for folder in HATS:
        for sex, fn in files_for(folder):
            path = src_path(folder, fn)
            _, sh = shapes(path)
            sel = select(folder, sex, sh)
            key = f"{folder}|{sex}"
            out[key] = dict(path=path, shapes={s["name"]: np.where(r["mask"])[0].tolist() for s, r in zip(sh, sel)})
            desc = []
            for s, r in zip(sh, sel):
                ks = [(c, k) for c, k in enumerate(r["kind"]) if k]
                if ks:
                    desc.append(f"{s['name'].split('_')[-1]}: " + " ".join(f"c{c}{'k' if k == 'knot' else ''}" for c, k in ks))
            print(f"{key:48s} {'; '.join(desc)}")
    json.dump(out, open(os.path.join(os.path.dirname(__file__), "sel.json"), "w"))
