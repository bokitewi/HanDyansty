"""Per-garment bulk: signed distance (outside +) of torso-band vertices vs base body with shrink(arms,chest,belly).
blender -b --factory-startup --python audit_bulk2.py -- out.json list.txt   (list = label|mesh lines)
"""
import json
import sys
from pathlib import Path

HERE = r"D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\65b27fb1-3a2f-45e9-9491-843d03c69887\scratchpad"
exec(open(HERE + r"\audit_fit_core.py", encoding="utf-8").read())

out_path = Path(sys.argv[sys.argv.index("--") + 1])
items = [l.strip().split("|", 1) for l in open(sys.argv[sys.argv.index("--") + 2], encoding="utf-8") if "|" in l]
bvh = body_bvh("base", ["arms", "chest", "belly"])
res = {}
for label, path in items:
    try:
        shapes = read_shapes(Path(path))
    except Exception as exc:  # noqa: BLE001
        print("FAIL", label, exc)
        continue
    if not [1 for _, pp, _ in shapes if len(pp)]:
        print("EMPTY", label)
        continue
    allp = np.concatenate([p for _, p, _ in shapes if len(p)])
    sel = allp[(allp[:, 1] > 85) & (allp[:, 1] < 135) & (np.abs(allp[:, 0]) < 32)]
    if len(sel) < 30:
        print("SKIP", label, len(sel))
        continue
    d = signed(bvh, sel)
    q = np.percentile(d, [10, 50, 90, 99])
    res[label] = {"n": int(len(sel)), "p10": round(float(q[0]), 2), "p50": round(float(q[1]), 2), "p90": round(float(q[2]), 2), "p99": round(float(q[3]), 2),
                  "frac_gt14": round(float((d > 14).mean()), 3), "frac_neg": round(float((d < 0).mean()), 3)}
    print(label, res[label], flush=True)
out_path.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print("BULK_OK")
