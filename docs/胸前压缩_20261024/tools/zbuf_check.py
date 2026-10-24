"""Exact layer-order check along z rays: per shape, rasterize triangles to a 0.5-unit (x, y) grid keeping the
front-most z; for every pair of shapes hit by the same ray, compare order before/after (x, y unchanged by the fit).
python zbuf_check.py <orig.mesh> <new.mesh>
"""
import sys

sys.path.insert(0, r"E:\documents\Paradox Interactive\Crusader Kings III\mod\HanDyansty\docs\服装穿模审计_20261022\tools")
import numpy as np  # noqa: E402

from pdxlib import pdx_data  # noqa: E402

G = 0.5
X0, X1, Y0, Y1 = -26.0, 26.0, 80.0, 152.0
NX, NY = int((X1 - X0) / G) + 1, int((Y1 - Y0) / G) + 1


def zbuf(p, tri):
    Z = np.full((NY, NX), np.inf)
    for t in tri:
        a, b, c = p[t[0]], p[t[1]], p[t[2]]
        xmin, xmax = min(a[0], b[0], c[0]), max(a[0], b[0], c[0])
        ymin, ymax = min(a[1], b[1], c[1]), max(a[1], b[1], c[1])
        if xmax < X0 or xmin > X1 or ymax < Y0 or ymin > Y1:
            continue
        i0, i1 = max(0, int(np.ceil((ymin - Y0) / G))), min(NY - 1, int(np.floor((ymax - Y0) / G)))
        j0, j1 = max(0, int(np.ceil((xmin - X0) / G))), min(NX - 1, int(np.floor((xmax - X0) / G)))
        if i1 < i0 or j1 < j0:
            continue
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        yy, xx = np.mgrid[i0:i1 + 1, j0:j1 + 1]
        X, Y = X0 + xx * G, Y0 + yy * G
        l1 = ((b[1] - c[1]) * (X - c[0]) + (c[0] - b[0]) * (Y - c[1])) / den
        l2 = ((c[1] - a[1]) * (X - c[0]) + (a[0] - c[0]) * (Y - c[1])) / den
        l3 = 1 - l1 - l2
        ins = (l1 >= -1e-9) & (l2 >= -1e-9) & (l3 >= -1e-9)
        if not ins.any():
            continue
        z = l1 * a[2] + l2 * b[2] + l3 * c[2]
        sub = Z[i0:i1 + 1, j0:j1 + 1]
        np.minimum(sub, np.where(ins, z, np.inf), out=sub)
    return Z


def load(path):
    root = pdx_data.read_meshfile(path)
    out = {}
    for o in root.iter("object"):
        for s in o:
            m = s.find("mesh")
            if m is None:
                continue
            p = np.array(m.attrib["p"], dtype=np.float64).reshape(-1, 3)
            t = np.array(m.attrib["tri"], dtype=np.int64).reshape(-1, 3)
            out[s.tag] = zbuf(p, t)
    return out


def main():
    a, b = load(sys.argv[1]), load(sys.argv[2])
    tags = list(a)
    tot = flips = coll = 0
    worst = []
    for i in range(len(tags)):
        for j in range(i + 1, len(tags)):
            A0, B0, A1, B1 = a[tags[i]], a[tags[j]], b[tags[i]], b[tags[j]]
            ok = np.isfinite(A0) & np.isfinite(B0) & np.isfinite(A1) & np.isfinite(B1)
            d0, d1 = (A0 - B0)[ok], (A1 - B1)[ok]
            big = np.abs(d0) >= 0.2
            tot += int(big.sum())
            fl = big & (np.sign(d0) != np.sign(d1))
            flips += int(fl.sum())
            coll += int((big & ~fl & (np.abs(d1) < 0.1)).sum())
            if fl.any():
                worst.append((float(np.abs(d1[fl]).max()), int(fl.sum()), tags[i][-26:], tags[j][-26:]))
    print("ray-pairs %d  flips %d (%.2f%%)  collapses<0.1 %d" % (tot, flips, 100.0 * flips / max(tot, 1), coll))
    for w in sorted(worst, reverse=True)[:6]:
        print("   flip maxdepth %.2f n=%d %s | %s" % w)


if __name__ == "__main__":
    main()
