"""Layer-order / gap-collapse check between an original and a staged garment mesh.
python layer_check.py <orig.mesh> <new.mesh>
Per shape: front-most z per 1x1 cell (triangle-sampled), |x|<26, 80<y<152.
For every pair of shapes covering a cell: order flips (|d0|>=0.3, sign change) and collapses (|d0|>=0.3, |d1|<0.3).
Also prints the front-most z of the whole garment across |x| for a few heights (flank check).
"""
import sys

sys.path.insert(0, r"E:\documents\Paradox Interactive\Crusader Kings III\mod\HanDyansty\docs\服装穿模审计_20261022\tools")
import numpy as np  # noqa: E402

from pdxlib import pdx_data  # noqa: E402


def fields(path):
    root = pdx_data.read_meshfile(path)
    out = {}
    for o in root.iter("object"):
        for s in o:
            m = s.find("mesh")
            if m is None:
                continue
            p = np.array(m.attrib["p"], dtype=np.float64).reshape(-1, 3)
            t = np.array(m.attrib["tri"], dtype=np.int64).reshape(-1, 3)
            a, b, c = (p[t[:, i]] for i in range(3))
            pts = []
            n = 3
            for i in range(n + 1):
                for j in range(n + 1 - i):
                    u, v = i / n, j / n
                    pts.append(a * (1 - u - v) + b * u + c * v)
            q = np.concatenate(pts)
            q = q[(np.abs(q[:, 0]) < 26) & (q[:, 1] > 80) & (q[:, 1] < 152)]
            key = np.round(q[:, 0]).astype(int) * 1000 + np.round(q[:, 1]).astype(int)
            order = np.lexsort((q[:, 2], key))
            k2, z2 = key[order], q[order, 2]
            first = np.ones(len(k2), bool)
            first[1:] = k2[1:] != k2[:-1]
            out[s.tag] = dict(zip(k2[first].tolist(), z2[first].tolist()))
    return out


def main():
    f0, f1 = fields(sys.argv[1]), fields(sys.argv[2])
    tags = list(f0)
    flips = collapse = pairs_cells = 0
    worst = []
    ratios = []
    for i in range(len(tags)):
        for j in range(i + 1, len(tags)):
            A0, B0, A1, B1 = f0[tags[i]], f0[tags[j]], f1[tags[i]], f1[tags[j]]
            for k in set(A0) & set(B0) & set(A1) & set(B1):
                d0, d1 = A0[k] - B0[k], A1[k] - B1[k]
                if abs(d0) < 0.3:
                    continue
                pairs_cells += 1
                if abs(d0) < 6:
                    ratios.append(abs(d1) / abs(d0))
                if np.sign(d0) != np.sign(d1):
                    flips += 1
                    worst.append((abs(d1), tags[i][-28:], tags[j][-28:], k // 1000, k % 1000, round(d0, 2), round(d1, 2)))
                elif abs(d1) < 0.3:
                    collapse += 1
    print("pair-cells %d  flips %d  collapses(<0.3) %d  gap ratio median %.2f p10 %.2f" % (
        pairs_cells, flips, collapse, float(np.median(ratios)) if ratios else 1, float(np.percentile(ratios, 10)) if ratios else 1))
    for w in sorted(worst, reverse=True)[:8]:
        print("   flip", w)
    for y in (100, 110, 120, 130):
        for lab, f in (("orig", f0), ("new ", f1)):
            row = []
            for x in range(0, 26, 2):
                zs = [f[t].get((x * 1000 + y) if x >= 0 else 0) for t in f]
                zs += [f[t].get(-x * 1000 + y) for t in f]
                zs = [z for z in zs if z is not None]
                row.append("%6.1f" % min(zs) if zs else "   .  ")
            print("y=%d %s %s" % (y, lab, " ".join(row)))


if __name__ == "__main__":
    main()
