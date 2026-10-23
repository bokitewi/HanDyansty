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


