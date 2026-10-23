"""Probe heavy_dark shapes: bbox, offset profile vs shrunk body, slice widths, dominant skin bones.
blender -b --factory-startup --python probe_hd.py
"""
import json
import sys
from pathlib import Path

HERE = r"D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\65b27fb1-3a2f-45e9-9491-843d03c69887\scratchpad"
exec(open(HERE + r"\audit_fit_core.py", encoding="utf-8").read())

MODF = Path(r"E:\documents\Paradox Interactive\Crusader Kings III\mod\HanJIn_Clothes\gfx\models\portraits\m_clothes\hd_frontier_xiongnu_heavy_dark\m_clothes_hd_frontier_xiongnu_heavy_dark.mesh")
VANF = Path(r"D:\SteamLibrary\steamapps\common\Crusader Kings III\game\gfx\models\portraits\m_clothes\tgp_chinese\war_nob_01\m_clothes_sec_tgp_chinese_war_nob_01.mesh")
VAN2 = Path(r"D:\SteamLibrary\steamapps\common\Crusader Kings III\game\gfx\models\portraits\m_clothes\tgp_chinese\war_02\m_clothes_sec_tgp_chinese_war_02.mesh")

bvh = body_bvh("base", ["arms", "chest", "belly"])
bvh_raw = body_bvh("base", [])


def bone_names(path):
    root = pdx_data.read_meshfile(str(path))
    names = {}
    for sk in root.iter("skeleton"):
        for j in sk:
            names[int(j.attrib["ix"][0])] = j.tag
    return names


def width_depth(p, y, tol=1.5):
    s = p[np.abs(p[:, 1] - y) < tol]
    s = s[np.abs(s[:, 0]) < 40]
    if len(s) < 5:
        return None
    return [round(float(s[:, 0].min()), 1), round(float(s[:, 0].max()), 1), round(float(s[:, 2].min()), 1), round(float(s[:, 2].max()), 1)]


print("BODY slices (unshrunk) y=100/110/120/130: [xmin,xmax,zmin,zmax]")
for y in (100, 110, 120, 130):
    print("  y", y, width_depth(P0, y))

for tag, path in (("MOD", MODF), ("VAN_war_nob_01", VANF), ("VAN_war_02", VAN2)):
    names = bone_names(path)
    root = pdx_data.read_meshfile(str(path))
    for obj in root.iter("object"):
        for shape in obj:
            mesh = shape.find("mesh")
            if mesh is None:
                continue
            p = np.array(mesh.attrib["p"], dtype=np.float64).reshape(-1, 3)
            tri = np.array(mesh.attrib["tri"], dtype=np.int64).reshape(-1, 3)
            d = signed(bvh, p)
            skin = mesh.find("skin")
            ix = np.array(skin.attrib["ix"], dtype=np.int64).reshape(-1, 4)
            w = np.array(skin.attrib["w"], dtype=np.float64).reshape(-1, 4)
            dom = ix[np.arange(len(ix)), w.argmax(1)]
            cnt = {}
            for b in dom:
                nm = names.get(int(b), str(b))
                cnt[nm] = cnt.get(nm, 0) + 1
            top = sorted(cnt.items(), key=lambda kv: -kv[1])[:5]
            mat = shape.find("mesh").find("material")
            print("%s %-60s v=%5d tri=%5d bbox=%s..%s" % (tag, shape.tag[-60:], len(p), len(tri), np.round(p.min(0), 1).tolist(), np.round(p.max(0), 1).tolist()))
            print("    offset pct5/25/50/75/95: %s  neg=%.3f  skin_top=%s  shader=%s" % (np.round(np.percentile(d, [5, 25, 50, 75, 95]), 1).tolist(), float((d < 0).mean()), top, mat.attrib.get("shader") if mat is not None else None))
            if "chest" in shape.tag or "war_nob_01Shape" in shape.tag or "war_02Shape" in shape.tag:
                for y in (100, 110, 120, 130):
                    print("    slice y=%d %s" % (y, width_depth(p, y)))
