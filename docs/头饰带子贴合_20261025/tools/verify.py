import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from strapfit import *  # noqa
stage = sys.argv[1]
rep = json.load(open(os.path.join(stage, "report.json"), encoding="utf-8"))
heads = {"m": HeadModel("m"), "f": HeadModel("f")}
bad = 0
for key, v in rep.items():
    if not v["stats"]:
        continue
    folder, sex = key.split("|")
    fn = f"{sex}_headgear_{folder}.mesh"
    src, new = v["src"], os.path.join(stage, folder, fn)
    _, a = shapes(src); _, b = shapes(new)
    ra = pdx_data.read_meshfile(src); rb = pdx_data.read_meshfile(new)
    na = [s for o in ra for s in o if s.find("mesh") is not None]; nb_ = [s for o in rb for s in o if s.find("mesh") is not None]
    H = heads[sex]
    msg = []
    for sa, sb, xa, xb in zip(a, b, na, nb_):
        ma, mb = xa.find("mesh"), xb.find("mesh")
        for k in ("u0", "u1", "tri"):
            if k in ma.attrib and list(ma.attrib[k]) != list(mb.attrib[k]):
                msg.append(f"{k} changed"); bad += 1
        moved = np.linalg.norm(sb["P"] - sa["P"], axis=1) > 1e-6
        if sb["ix"] is not None:
            ws = sb["w"].sum(1)
            if np.abs(ws - 1).max() > 1e-4: msg.append("wsum"); bad += 1
            ixv = sb["ix"][sb["w"] > 0]
            if ixv.min() < 0 or ixv.max() >= len(sb["bones"]): msg.append("ix range"); bad += 1
            wchg = (np.abs(sb["w"] - sa["w"]).sum(1) > 1e-6) | (sb["ix"] != sa["ix"]).any(1)
            if (wchg & ~moved).sum():
                msg.append(f"weights changed on {int((wchg & ~moved).sum())} unmoved verts")
        nn = np.array(mb.attrib["n"]).reshape(-1, 3)
        if np.abs(np.linalg.norm(nn, axis=1) - 1).max() > 1e-3: msg.append("normal len"); bad += 1
        if moved.any():
            # fat check
            ffn = os.path.join(stage, folder, fn[:-5] + "_bs_fat.mesh")
            if os.path.exists(ffn):
                _, fb = shapes(ffn)
                fs = [x for x in fb if x["name"] == sb["name"]][0]
                Pf = fs["P"][moved]
                # signed distance to the fat head surface: project on base, offset by fat delta (approx)
                q, n, d, tri, bary = H.project(Pf - np.array([H.fat_at(np.array([t]), np.array([bb])) for t, bb in zip(*H.project(sb["P"][moved], "all")[3:5])]), "all")
                msg.append(f"{sb['name'][-16:]} moved={int(moved.sum())} fat_gap_min={d.min():.2f} p05={np.percentile(d,5):.2f}")
    print(f"{key:48s} " + "; ".join(msg))
print("BAD", bad)
