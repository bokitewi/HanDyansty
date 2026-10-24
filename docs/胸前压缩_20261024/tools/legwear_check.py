"""Rest-pose check: does the paired legwear now show in front of the (compressed) clothes?
python legwear_check.py      (uses list_all_m/f.txt: label_o|orig;legwear  label_n|new;legwear)
Per 0.5-unit (x, y) ray in |x|<30, 30<y<110: front-most z of the clothes (all shapes) vs of the legwear.
Counts rays where the clothes were in front (or level) before and the legwear is now >0.1 in front.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402

import zbuf_check as Z  # noqa: E402
from pdxlib import pdx_data  # noqa: E402

Z.G, Z.X0, Z.X1, Z.Y0, Z.Y1 = 0.5, -30.0, 30.0, 30.0, 110.0
Z.NX, Z.NY = int((Z.X1 - Z.X0) / Z.G) + 1, int((Z.Y1 - Z.Y0) / Z.G) + 1


def front(path):
    root = pdx_data.read_meshfile(path)
    F = np.full((Z.NY, Z.NX), np.inf)
    for o in root.iter("object"):
        for s in o:
            m = s.find("mesh")
            if m is None:
                continue
            p = np.array(m.attrib["p"], dtype=np.float64).reshape(-1, 3)
            t = np.array(m.attrib["tri"], dtype=np.int64).reshape(-1, 3)
            F = np.minimum(F, Z.zbuf(p, t))
    return F


def main():
    for sx in "mf":
        lines = [l.strip().split("|", 1) for l in open(os.path.join(HERE, "list_all_%s.txt" % sx), encoding="utf-8") if "|" in l]
        d = dict(lines)
        for lab, paths in lines:
            if not lab.endswith("_o") or ";" not in paths:
                continue
            g = lab[:-2]
            co, leg = paths.split(";")
            cn = d[g + "_n"].split(";")[0]
            L, A, B = front(leg), front(co), front(cn)
            ok = np.isfinite(L) & np.isfinite(A) & np.isfinite(B)
            was = ok & (A <= L + 0.05)
            now = was & (B > L + 0.1)
            ys = (np.nonzero(now)[0] * Z.G + Z.Y0) if now.any() else np.array([])
            print("%s %-24s rays both %5d  clothes-in-front before %5d  legwear now in front %4d  max %.2f  y %s" % (
                sx, g, int(ok.sum()), int(was.sum()), int(now.sum()), float((B - L)[now].max()) if now.any() else 0.0,
                "%.0f-%.0f" % (ys.min(), ys.max()) if len(ys) else "-"), flush=True)


if __name__ == "__main__":
    main()
