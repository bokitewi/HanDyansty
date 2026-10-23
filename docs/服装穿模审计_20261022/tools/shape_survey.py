"""Per-shape survey of all mod male garments vs vanilla baseline.
python shape_survey.py   (run from scratchpad)
Metrics per shape: verts, shader, front gap (central |x|<15, y 100..130: body_front - zmin, avg & max),
offset to shrunk body (p5/p50/p95), inside fraction (d<0), float fraction (d>10), top dominant bones.
"""
import glob
import json
import os
import sys

sys.path.insert(0, ".")
import numpy as np

import apply_fit as A
from pdxlib import pdx_data

body = A.BodyModel(A.SEX["m"])
YB = [100, 106, 112, 118, 124, 130]
MOD = r"E:\documents\Paradox Interactive\Crusader Kings III\mod\HanJIn_Clothes\gfx\models\portraits\m_clothes"
VAN = r"D:\SteamLibrary\steamapps\common\Crusader Kings III\game\gfx\models\portraits\m_clothes"


def shapes_of(path):
    root = pdx_data.read_meshfile(path)
    jn = A.joint_names(root)
    out = []
    for o in root.iter("object"):
        for s in o:
            m = s.find("mesh")
            if m is None:
                continue
            p = np.array(m.attrib["p"], dtype=np.float64).reshape(-1, 3)
            if not len(p):
                continue
            mat = m.find("material")
            sh = mat.attrib.get("shader", [""])[0] if mat is not None else ""
            skin = m.find("skin")
            dom = None
            if skin is not None:
                ix = np.array(skin.attrib["ix"], dtype=np.int64).reshape(-1, 4)
                w = np.array(skin.attrib["w"], dtype=np.float64).reshape(-1, 4)
                d = ix[np.arange(len(ix)), w.argmax(1)]
                cnt = {}
                for b in d:
                    nm = jn.get(int(b), str(b)).split(":")[-1]
                    cnt[nm] = cnt.get(nm, 0) + 1
                dom = sorted(cnt.items(), key=lambda kv: -kv[1])[:2]
            out.append((s.tag, p, sh, dom))
    return out


def front_gap(p):
    gaps = []
    for y in YB:
        s = p[(np.abs(p[:, 1] - y) < 3) & (np.abs(p[:, 0]) < 15)]
        if len(s) < 3:
            continue
        bz = body.front_z(np.array([float(y)]), np.array([4.0]))[0]
        gaps.append(bz - s[:, 2].min())
    return (float(np.mean(gaps)), float(np.max(gaps))) if gaps else (None, None)


def survey(path):
    rows = []
    for tag, p, sh, dom in shapes_of(path):
        g = front_gap(p)
        sel = p[(p[:, 1] > 80) & (p[:, 1] < 156)]
        if len(sel) > 20:
            q, n = body.nearest(sel)
            d = ((sel - q) * n).sum(1)
            pc = np.percentile(d, [5, 50, 95]).round(1).tolist()
            ins, flt = float((d < 0).mean()), float((d > 10).mean())
        else:
            pc, ins, flt = None, None, None
        rows.append(dict(tag=tag, n=len(p), shader=sh, gap_avg=g[0], gap_max=g[1], pct=pc, inside=ins, floaty=flt, dom=dom))
    return rows


res = {}
if len(sys.argv) > 1 and sys.argv[1] == "van":
    # vanilla: front gap only (cheap), max over shapes per garment
    gaps = []
    for f in sorted(glob.glob(VAN + "/**/m_clothes_*.mesh", recursive=True)):
        if "_bs_" in os.path.basename(f):
            continue
        try:
            sh = shapes_of(f)
        except Exception:
            continue
        g = [front_gap(p) for _, p, _, _ in sh]
        g = [x for x in g if x[0] is not None]
        if g:
            gaps.append((os.path.basename(f), max(x[0] for x in g), max(x[1] for x in g)))
    a = np.array([x[1] for x in gaps])
    b = np.array([x[2] for x in gaps])
    print("VANILLA garments", len(gaps), "front gap avg: pct10/50/75/90/max", np.percentile(a, [10, 50, 75, 90]).round(1).tolist(), a.max().round(1), "| gap max: pct50/75/90", np.percentile(b, [50, 75, 90]).round(1).tolist())
    sys.exit()

for f in sorted(glob.glob(MOD + "/**/m_clothes_*.mesh", recursive=True)):
    if "_bs_" in os.path.basename(f):
        continue
    key = os.path.basename(f)[:-5].replace("m_clothes_", "").replace("sec_", "")
    res[key] = survey(f)
    print("done", key, flush=True)
json.dump(res, open("shape_survey.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("WROTE shape_survey.json")
