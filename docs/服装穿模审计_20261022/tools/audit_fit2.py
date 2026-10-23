"""Static fit audit: garment vertices vs vanilla male body under body-type + shrink morphs.

Run: blender --background --python audit_fit.py -- <out.json> <garment.mesh> [<garment.mesh> ...]
Garment morph files are found as <stem>_bs_<key>.mesh next to the base mesh.
Coordinates stay in PDX file space (Y up); body and garments share it.
"""
import json
import sys
from pathlib import Path

import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = Path(r"D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\65b27fb1-3a2f-45e9-9491-843d03c69887\scratchpad")
sys.path.insert(0, str(HERE))
from pdxlib import pdx_data  # noqa: E402

GAME = Path(r"D:\SteamLibrary\steamapps\common\Crusader Kings III\game\gfx\models\portraits")
BODY = GAME / "male_body" / "male_body.mesh"
BS = GAME / "male_body" / "blendshapes"
TYPE_FILES = {
    "fat": "male_bs_body_fat_1.mesh",
    "gaunt": "male_bs_body_gaunt_1.mesh",
    "musc": "male_bs_body_muscular_1.mesh",
    "old": "male_bs_body_old_1.mesh",
    "dwarf": "male_bs_body_dwarf_1.mesh",
}
SHRINK_FILES = {
    "arms": "male_bs_body_shrink_arms.mesh",
    "chest": "male_bs_body_shrink_chest.mesh",
    "belly": "male_bs_body_shrink_belly.mesh",
    "legs": "male_bs_body_shrink_legs.mesh",
    "feet": "male_bs_body_shrink_feet.mesh",
    "hands": "male_bs_body_shrink_hands.mesh",
}
STATES = ["base", "fat", "gaunt", "musc", "old", "dwarf"]


def read_shapes(path):
    root = pdx_data.read_meshfile(str(path))
    out = []
    for obj in root.iter("object"):
        for shape in obj:
            mesh = shape.find("mesh")
            if mesh is None:
                continue
            p = np.array(mesh.attrib["p"], dtype=np.float64).reshape(-1, 3)
            tri = np.array(mesh.attrib["tri"], dtype=np.int64).reshape(-1, 3)
            out.append((shape.tag, p, tri))
    return out


body_shape = read_shapes(BODY)[0]
P0 = body_shape[1]
BTRI = body_shape[2]


def body_delta(path):
    t = read_shapes(path)[0][1]
    return t - P0


TYPE_D = {k: body_delta(BS / v) for k, v in TYPE_FILES.items()}
SHRINK_D = {k: body_delta(BS / v) for k, v in SHRINK_FILES.items()}


def body_bvh(state, shrinks):
    pos = P0.copy()
    for s in shrinks:
        pos += SHRINK_D[s]
    if state != "base":
        pos += TYPE_D[state]
    return BVHTree.FromPolygons([Vector(v) for v in pos], [tuple(t) for t in BTRI], all_triangles=True)


def signed(bvh, pts):
    d = np.empty(len(pts))
    for i, p in enumerate(pts):
        loc, nrm, idx, dist = bvh.find_nearest(Vector(p))
        d[i] = dist if (Vector(p) - loc).dot(nrm) >= 0 else -dist
    return d


def classify(stem):
    if "_legwear_" in stem:
        return ["legs", "feet"]
    if "_headgear_" in stem:
        return None
    return ["arms", "chest", "belly"]


results = {}
out_path = Path(sys.argv[sys.argv.index("--") + 1])
meshes = sys.argv[sys.argv.index("--") + 2:]
if len(meshes) == 1 and meshes[0].endswith(".txt"):
    meshes = [l.strip().split("|", 1)[1] for l in open(meshes[0], encoding="utf-8") if "|" in l]
    labels = {l.strip().split("|", 1)[1]: l.strip().split("|", 1)[0] for l in open(sys.argv[-1], encoding="utf-8") if "|" in l}
else:
    labels = {}
cache = {}
for mp in meshes:
    mp = Path(mp)
    stem = labels.get(str(mp), mp.stem)
    mstem = mp.stem
    shr = classify(mstem)
    if shr is None:
        continue
    base = read_shapes(mp)
    res = {}
    for state in STATES:
        key = (state, tuple(shr))
        if key not in cache:
            cache[key] = body_bvh(state, shr)
        bvh = cache[key]
        if state == "base":
            shapes = base
        else:
            bsp = mp.with_name(mstem + "_bs_" + state + ".mesh")
            if not bsp.exists():
                continue
            bsh = read_shapes(bsp)
            shapes = []
            for (n0, p0, t0), (n1, p1, t1) in zip(base, bsh):
                if len(p0) != len(p1):
                    shapes.append((n0, None, t0))
                    continue
                shapes.append((n0, p1, t0))
        per = {}
        for n, p, t in shapes:
            if p is None:
                per[n] = "count-mismatch"
                continue
            d = signed(bvh, p)
            inside = -d[d < 0]
            per[n] = {
                "n": int(len(p)),
                "inside_gt0.5": int((d < -0.5).sum()),
                "inside_gt1": int((d < -1.0).sum()),
                "inside_gt2": int((d < -2.0).sum()),
                "max_depth": float(inside.max()) if len(inside) else 0.0,
            }
        res[state] = per
    results[stem] = res
    print("DONE", stem, flush=True)
out_path.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
print("WROTE", out_path)
