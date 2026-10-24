"""Static poke-through check: garment vertices inside the shrunk body for every body type, orig vs staged.
python static_inside.py <orig_dir> <staged_dir> <garment_name> [m|f|mf]
Body = base + shrink(arms, chest, belly) + type delta; signed distance to nearest triangle-sample (face normal sign).
Reports, per state, count of vertices deeper than 1.0 inside (whole garment) for orig and staged.
"""
import os
import sys

sys.path.insert(0, r"E:\documents\Paradox Interactive\Crusader Kings III\mod\HanDyansty\docs\服装穿模审计_20261022\tools")
import numpy as np  # noqa: E402
from scipy.spatial import cKDTree  # noqa: E402

import apply_fit as A  # noqa: E402
from pdxlib import pdx_data  # noqa: E402

STATES = {"m": ["base", "fat", "gaunt", "musc", "old", "dwarf"],
          "f": ["base", "fat", "gaunt", "musc", "old", "dwarf", "pregnant", "bust_max", "bust_min"]}


class Body:
    def __init__(self, sex):
        self.cfg = A.SEX[sex]
        self.P0, self.tri = A.positions(os.path.join(A.GAME, self.cfg["body"]))
        sh = self.P0.copy()
        for nm in ("arms", "chest", "belly"):
            sh += A.positions(os.path.join(A.GAME, self.cfg["bsdir"], self.cfg["shrink"] % nm))[0] - self.P0
        self.shrunk = sh
        self.cache = {}

    def tree(self, state):
        if state not in self.cache:
            pos = self.shrunk.copy()
            if state != "base":
                f = A.MORPH_FILES[self.cfg["sex"]][state]
                pos += A.positions(os.path.join(A.GAME, self.cfg["bsdir"], f + ".mesh"))[0] - self.P0
            a, b, c = (pos[self.tri[:, i]] for i in range(3))
            fn = np.cross(b - a, c - a)
            fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
            pts, nrm = [], []
            n = 4
            for i in range(n + 1):
                for j in range(n + 1 - i):
                    u, v = i / n, j / n
                    pts.append(a * (1 - u - v) + b * u + c * v)
                    nrm.append(fn)
            sp, sn = np.concatenate(pts), np.concatenate(nrm)
            self.cache[state] = (cKDTree(sp), sp, sn)
        return self.cache[state]

    def inside(self, state, p):
        t, sp, sn = self.tree(state)
        _, idx = t.query(p)
        d = ((p - sp[idx]) * sn[idx]).sum(1)
        return int((d < -1.0).sum()), int((d < -2.0).sum())


def allp(path):
    root = pdx_data.read_meshfile(path)
    return np.concatenate([np.array(s.find("mesh").attrib["p"], dtype=np.float64).reshape(-1, 3)
                           for o in root.iter("object") for s in o if s.find("mesh") is not None])


def main():
    od, sd, name = sys.argv[1], sys.argv[2], sys.argv[3]
    sexes = sys.argv[4] if len(sys.argv) > 4 else "mf"
    for sex in sexes:
        stem = "%s_clothes_%s" % (sex, name)
        if not os.path.isfile(os.path.join(sd, stem + ".mesh")):
            continue
        body = Body(sex)
        row = []
        for st in STATES[sex]:
            fn = stem + (".mesh" if st == "base" else "_bs_%s.mesh" % st)
            if not os.path.isfile(os.path.join(od, fn)):
                continue
            o1, o2 = body.inside(st, allp(os.path.join(od, fn)))
            n1, n2 = body.inside(st, allp(os.path.join(sd, fn)))
            row.append("%s %d->%d (>2: %d->%d)" % (st, o1, n1, o2, n2))
        print("%s %s | %s" % (name, sex, " | ".join(row)), flush=True)


if __name__ == "__main__":
    main()
