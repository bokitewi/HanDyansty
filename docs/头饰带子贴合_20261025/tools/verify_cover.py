import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from strapfit import *  # noqa
stage = sys.argv[1]
rep = json.load(open(os.path.join(stage, "report.json"), encoding="utf-8"))
H = {"m": HeadModel("m"), "f": HeadModel("f")}
for key, v in rep.items():
    if not v["stats"]:
        continue
    folder, sex = key.split("|"); fn = f"{sex}_headgear_{folder}.mesh"
    _, a = shapes(v["src"]); _, b = shapes(os.path.join(stage, folder, fn))
    sel = select(folder, sex, a)
    body = []
    for s_, r_ in zip(a, sel):
        if "plume" in s_["name"].lower(): continue
        keep = ~r_["mask"]; T_ = s_["T"][keep[s_["T"]].all(1)]
        if len(T_): body.append(s_["P"][T_])
    body = np.concatenate(body) if body else np.zeros((0, 3, 3))
    cov_moved = cov_n = cross = 0
    for sa, sb, r in zip(a, b, sel):
        mi = np.where(np.array([r["kind"][c] == "main" for c in r["comp"]]))[0]
        if not len(mi): continue
        q = H[sex].project(sa["P"][mi])[0]
        for k, g in enumerate(mi):
            dp = np.linalg.norm(sb["P"][g] - sa["P"][g])
            if seg_hits(sa["P"][g], q[k], body):
                cov_n += 1
                if dp > 1e-5: cov_moved += 1
            if dp > 1e-5 and seg_first_hit(sa["P"][g], sb["P"][g], body) is not None:
                cross += 1
    print(f"{key:44s} covered {cov_n:4d} moved-among-covered {cov_moved:3d}   paths crossing hat body {cross:3d}")
