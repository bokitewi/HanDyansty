import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from strapfit import *  # noqa
stage = sys.argv[1]
rep = json.load(open(os.path.join(stage, "report.json"), encoding="utf-8"))
def fat_head(sex):
    h = HeadModel(sex)
    h.P = h.P + h.fat
    h.vn = vertex_normals(h.P, h.T)
    tris = np.arange(len(h.T)); pts, tid = [], []
    a, b, c = (h.P[h.T[tris, i]] for i in range(3))
    for i in range(5):
        for j in range(5 - i):
            u, v = i / 4, j / 4
            pts.append(a * (1 - u - v) + b * u + c * v); tid.append(tris)
    h.kd["all"] = (cKDTree(np.concatenate(pts)), np.concatenate(tid))
    return h
FH = {"m": fat_head("m"), "f": fat_head("f")}
for key, v in rep.items():
    if not v["stats"]:
        continue
    folder, sex = key.split("|")
    fn = f"{sex}_headgear_{folder}.mesh"
    src = v["src"]
    _, a = shapes(src); _, b = shapes(os.path.join(stage, folder, fn))
    fa_p = os.path.join(os.path.dirname(src), fn[:-5] + "_bs_fat.mesh")
    _, fa = shapes(fa_p); _, fb = shapes(os.path.join(stage, folder, fn[:-5] + "_bs_fat.mesh"))
    out = []
    for sa, sb, xa, xb in zip(a, b, fa, fb):
        moved = np.linalg.norm(sb["P"] - sa["P"], axis=1) > 1e-6
        if not moved.any(): continue
        d_old = FH[sex].project(xa["P"][moved], "all")[2]
        d_new = FH[sex].project(xb["P"][moved], "all")[2]
        dn_base = HeadModel.project(FH[sex], sb["P"][moved], "all")[2]  # (unused) sanity
        out.append(f"fat gap old min {d_old.min():.2f} p05 {np.percentile(d_old,5):.2f} med {np.median(d_old):.2f} | new min {d_new.min():.2f} p05 {np.percentile(d_new,5):.2f} med {np.median(d_new):.2f} n<0: {(d_new<0).sum()}")
    print(f"{key:44s} " + "; ".join(out))
