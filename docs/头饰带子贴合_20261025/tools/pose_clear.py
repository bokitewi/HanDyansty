"""python pose_clear.py <npzdir> <list.txt> : strap-triangle interior clearance vs deformed head per pose."""
import sys, os, glob, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from strapfit import *  # noqa
npzdir, lst = sys.argv[1], sys.argv[2]
items = [l.strip().split("|", 1) for l in open(lst, encoding="utf-8") if "|" in l]
def vnorm(P, T):
    return vertex_normals(P, T)
res = {}
for label, path in items:
    m = re.match(r"(.+)_([mf])_(old|new)$", label)
    folder, sex, ver = m.group(1), m.group(2), m.group(3)
    _, sh = shapes(path)
    sel = select(folder, sex, sh)
    for f in sorted(glob.glob(os.path.join(npzdir, label + "__*.npz"))):
        tag = f.split("__")[-1][:-4]
        z = np.load(f)
        hk = [k for k in z.files if k.startswith("HEAD|")][0]
        HP = z[hk]; HT = z["HEADTRI|" + hk[5:]]
        hn = vnorm(HP, HT)
        a, b, c = (HP[HT[:, i]] for i in range(3))
        pts, nrm = [], []
        for i in range(7):
            for j in range(7 - i):
                u, v = i / 6, j / 6
                pts.append(a * (1 - u - v) + b * u + c * v)
                nrm.append(hn[HT[:, 0]] * (1 - u - v) + hn[HT[:, 1]] * u + hn[HT[:, 2]] * v)
        pts = np.concatenate(pts); nrm = np.concatenate(nrm)
        kd = cKDTree(pts)
        hats = {k: z[k] for k in z.files if k.startswith("HAT|")}
        worst = []
        for s, r in zip(sh, sel):
            if not r["mask"].any():
                continue
            cand = [k for k, v in hats.items() if len(v) == len(s["P"])]
            if len(cand) > 1:
                cand = [k for k in cand if k.split("|", 1)[1] in s["name"] or s["name"] in k] or cand
            Q = hats[cand[0]]
            T = s["T"][r["mask"][s["T"]].all(1)]
            qa, qb, qc = (Q[T[:, i]] for i in range(3))
            sp = []
            for i in range(5):
                for j in range(5 - i):
                    u, v = i / 4, j / 4
                    sp.append(qa * (1 - u - v) + qb * u + qc * v)
            sp = np.concatenate(sp)
            dd, ii = kd.query(sp)
            sd = np.einsum("ij,ij->i", sp - pts[ii], nrm[ii]) / np.maximum(np.linalg.norm(nrm[ii], axis=1), 1e-9)
            sd = np.where(dd < 3, sd, dd)
            worst.append(sd)
        sd = np.concatenate(worst)
        res[(label, tag)] = (sd.min(), np.percentile(sd, 1), int((sd < 0).sum()), len(sd))
for (label, tag), (mn, p1, neg, n) in sorted(res.items()):
    print(f"{label:52s} {tag:16s} min {mn:6.2f} p01 {p1:6.2f} neg {neg:5d}/{n}")
