"""Outermost-front protrusion survey, mod vs vanilla, both sexes.
python survey_front.py <out.json>
For every garment (all shapes together), per y band: gap = body_front_z(y, |x|) - min z of vertices with |x|<14 in band.
Positive gap = garment front sits that far in front of the (unshrunk) body front.
"""
import glob
import json
import os
import sys

TOOLS = r"E:\documents\Paradox Interactive\Crusader Kings III\mod\HanDyansty\docs\服装穿模审计_20261022\tools"
sys.path.insert(0, TOOLS)
import numpy as np  # noqa: E402

import apply_fit as A  # noqa: E402
from pdxlib import pdx_data  # noqa: E402

MOD = r"E:\documents\Paradox Interactive\Crusader Kings III\mod\HanJIn_Clothes\gfx\models\portraits"
VAN = r"D:\SteamLibrary\steamapps\common\Crusader Kings III\game\gfx\models\portraits"
BANDS = {"m": [96, 102, 108, 114, 120, 126, 132], "f": [90, 96, 102, 108, 114, 120, 126]}


def all_pts(path):
    root = pdx_data.read_meshfile(path)
    ps = []
    for o in root.iter("object"):
        for s in o:
            m = s.find("mesh")
            if m is None:
                continue
            p = np.array(m.attrib["p"], dtype=np.float64).reshape(-1, 3)
            if len(p):
                ps.append(p)
    return np.concatenate(ps) if ps else None


def prof(body, p, bands):
    out = []
    for y in bands:
        s = p[(np.abs(p[:, 1] - y) < 3) & (np.abs(p[:, 0]) < 14)]
        if len(s) < 3:
            out.append(None)
            continue
        bz = body.front_z(np.array([float(y)]), np.array([4.0]))[0]
        out.append(round(float(bz - s[:, 2].min()), 2))
    return out


def main():
    res = {}
    for sex in ("m", "f"):
        body = A.BodyModel(A.SEX[sex])
        for src, base in (("mod", MOD), ("van", VAN)):
            sub = "" if src == "mod" else "%s_clothes" % sex
            files = sorted(glob.glob(os.path.join(base, sub, "**", "%s_clothes_*.mesh" % sex), recursive=True))
            for f in files:
                bn = os.path.basename(f)
                if "_bs_" in bn:
                    continue
                try:
                    p = all_pts(f)
                except Exception as e:  # noqa: BLE001
                    print("ERR", bn, e)
                    continue
                if p is None:
                    continue
                res["%s|%s|%s" % (src, sex, bn[:-5])] = prof(body, p, BANDS[sex])
            print("done", sex, src, len(files), flush=True)
    json.dump(res, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("WROTE", sys.argv[1])


if __name__ == "__main__":
    main()
