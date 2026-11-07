import sys, os
sys.path.insert(0, r"E:\documents\Paradox Interactive\Crusader Kings III\mod\HanDyansty\docs\服装穿模审计_20261022\tools")
import numpy as np
from pdxlib import pdx_data
D = r"E:\documents\Paradox Interactive\Crusader Kings III\mod\HanDyansty\docs"
B19 = D + r"\头饰外扩_备份_20261019"; B25 = D + r"\头饰带子贴合_备份_20261025"
CL = r"E:\documents\Paradox Interactive\Crusader Kings III\mod\HanJIn_Clothes\gfx\models\portraits\m_headgear"
OUT = sys.argv[1]
ITEMS = [("hd_pingjinze_01","m"),("hd_belka_guan_yu_01","m"),("hd_belka_guan_yu_01","f"),
         ("hd_eastern_han_armor_02","m"),("hd_eastern_han_armor_02","f"),("hd_pingshangze_01","m")]
def meshes(root):
    return [m for o in root for s in o for m in [s.find("mesh")] if m is not None]
def P(m): return np.array(m.attrib["p"], dtype=np.float64).reshape(-1,3)
for folder, sex in ITEMS:
    for suf in ("", "_bs_fat"):
        fn = f"{sex}_headgear_{folder}{suf}.mesh"
        cur = pdx_data.read_meshfile(os.path.join(CL, folder, fn))
        b19 = meshes(pdx_data.read_meshfile(os.path.join(B19, folder, fn)))
        p25 = os.path.join(B25, folder, fn)
        b25 = meshes(pdx_data.read_meshfile(p25)) if os.path.exists(p25) else None
        cm = meshes(cur); assert len(cm) == len(b19)
        for i, m in enumerate(cm):
            c = P(m); o = P(b19[i]); assert c.shape == o.shape, (fn, i)
            a = P(b25[i]) if b25 else c
            strap = np.linalg.norm(c - a, axis=1) > 1e-5
            d = a - o
            n = c.copy(); n[~strap] -= 0.5 * d[~strap]
            m.attrib["p"] = [float(v) for v in n.reshape(-1)]
            mv = np.linalg.norm(d, axis=1)
            print(fn, i, "verts", len(c), "inflated", int((mv > 1e-4).sum()), "max", round(mv.max(), 3), "strap kept", int(strap.sum()))
        os.makedirs(os.path.join(OUT, folder), exist_ok=True)
        pdx_data.write_meshfile(os.path.join(OUT, folder, fn), cur)
