"""Round-2 fit (user-approved 2026-10-22): xiongnu_noble, nanman_shoulder, sabre_infantry_01 -> staging dir.

python apply_fit2.py <garment_dir_name> <stage_root>
Rules:
  hd_frontier_xiongnu_noble     : shoulder_1, shoulder_2 -> fur shell 3..10
  hd_frontier_nanman_shoulder   : robe_2 -> fur shell 3..10 ; robe_1 -> front pull-back to body_front - g (m 4.5 / f 4.1)
  hd_historic_sabre_infantry_01 : whole shape -> vertices inside (d < 1.0 above shrunk body) pushed out to 1.0..1.1 (monotone), depth cap PUSH_CAP
Every *_bs_*.mesh gets the same per-vertex displacement, body-type delta re-anchored at the new position (as round 1).
"""
import os
import sys

import numpy as np

sys.path.insert(0, ".")
import apply_fit as A  # noqa: E402
from pdxlib import pdx_data  # noqa: E402

BASE = r"E:\documents\Paradox Interactive\Crusader Kings III\mod\HanJIn_Clothes\gfx\models\portraits\m_clothes"
PUSH_LO = 1.0
PUSH_CAP = 8.0     # vertices deeper than this inside the body are left alone (likely hidden/back-side), reported

RULES = {
    "hd_frontier_xiongnu_noble": [("shoulder_1", "fur", None), ("shoulder_2", "fur", None)],
    "hd_frontier_nanman_shoulder": [("robe_2", "fur", None), ("robe_1", "front", {"m": 4.5, "f": 4.1})],
    "hd_historic_sabre_infantry_01": [("sabre_infantry_01Shape", "push", None)],
}


def push_out(body, p):
    q, n = body.nearest(p)
    d = ((p - q) * n).sum(1)
    sel = (d < PUSH_LO) & (d > -PUSH_CAP)
    out = p.copy()
    nd = PUSH_LO + 0.1 * np.clip((d[sel] + PUSH_CAP) / (PUSH_LO + PUSH_CAP), 0, 1)
    out[sel] = q[sel] + n[sel] * nd[:, None]
    deep = int((d <= -PUSH_CAP).sum())
    return out, deep


def process_base(src, dst, body, cfg, rules):
    root = pdx_data.read_meshfile(src)
    disp, dn, dt, oldp, newpos = {}, {}, {}, {}, {}
    for o in root.iter("object"):
        for shape in o:
            m = shape.find("mesh")
            if m is None:
                continue
            p = np.array(m.attrib["p"], dtype=np.float64).reshape(-1, 3)
            tri = np.array(m.attrib["tri"], dtype=np.int64).reshape(-1, 3)
            n_old = np.array(m.attrib["n"], dtype=np.float64).reshape(-1, 3)
            ta_old = np.array(m.attrib["ta"], dtype=np.float64).reshape(-1, 4)
            newp, renorm, note = p, False, ""
            for key, op, arg in rules:
                if key not in shape.tag:
                    continue
                if op == "fur":
                    newp = A.fur_shell(body, p)
                elif op == "front":
                    newp = A.front_pullback(body, p, arg[cfg["sex"]])
                    renorm = True
                elif op == "push":
                    newp, deep = push_out(body, p)
                    renorm = True
                    note = " (deeper than cap, untouched: %d)" % deep
                break
            d = newp - p
            moved = np.linalg.norm(d, axis=1) > 1e-6
            disp[shape.tag] = d
            oldp[shape.tag] = p
            newpos[shape.tag] = newp
            if renorm and moved.any():
                n_new, used = A.recompute_normals(p, newp, tri, n_old, moved)
                ta_new = ta_old.copy()
                t = ta_old[:, :3]
                t2 = t - n_new * (n_new * t).sum(1, keepdims=True)
                ln = np.linalg.norm(t2, axis=1)
                good = moved & (ln > 1e-6)
                ta_new[good, :3] = t2[good] / ln[good, None]
                dn[shape.tag] = n_new - n_old
                dt[shape.tag] = ta_new[:, :3] - ta_old[:, :3]
                m.attrib["n"] = [float(x) for x in n_new.reshape(-1)]
                m.attrib["ta"] = [float(x) for x in ta_new.reshape(-1)]
            else:
                dn[shape.tag] = np.zeros_like(n_old)
                dt[shape.tag] = np.zeros((len(p), 3))
            if moved.any():
                m.attrib["p"] = [float(x) for x in newp.reshape(-1)]
                A.update_bounds(m)
            print("  %-3s %-52s moved=%4d/%4d mean=%.2f max=%.2f%s" % (os.path.basename(dst)[:2], shape.tag[-52:], int(moved.sum()), len(p), np.linalg.norm(d, axis=1).mean(), np.linalg.norm(d, axis=1).max(), note))
    pdx_data.write_meshfile(dst, root)
    return disp, dn, dt, oldp, newpos


VARIANTS = {
    "noble_B": ("hd_frontier_xiongnu_noble", [("shoulder_1", "fur", None), ("shoulder_2", "fur", None)], 16.0),
    "noble_C": ("hd_frontier_xiongnu_noble", [("shoulder_1", "fur", None), ("shoulder_2", "fur", None)], 13.0),
    "noble_P": ("hd_frontier_xiongnu_noble", [("shoulder_1", "push", None), ("shoulder_2", "push", None)], None),
    "nanman_P": ("hd_frontier_nanman_shoulder", [("robe_2", "push", None)], None),
    "nanman_B": ("hd_frontier_nanman_shoulder", [("robe_1", "front", {"m": 4.5, "f": 4.1})], None),
}


def main():
    name, stage_root = sys.argv[1], sys.argv[2]
    if len(sys.argv) > 3:
        name, rules_override, hi = VARIANTS[sys.argv[3]]
        RULES[name] = rules_override
        if hi is not None:
            A.FUR_HI = hi
    src_dir = os.path.join(BASE, name)
    stage = os.path.join(stage_root, name)
    os.makedirs(stage, exist_ok=True)
    rules = RULES[name]
    for sex, cfg in A.SEX.items():
        body = A.BodyModel(cfg)
        base_name = "%s_clothes_%s.mesh" % (sex, name)
        print("== %s sex %s" % (name, sex))
        disp, dn, dt, oldp, newpos = process_base(os.path.join(src_dir, base_name), os.path.join(stage, base_name), body, cfg, rules)
        for fn in sorted(os.listdir(src_dir)):
            if fn.startswith("%s_clothes_%s_bs_" % (sex, name)) and fn.endswith(".mesh"):
                key = fn.split("_bs_")[1][:-5]
                A.process_bs(os.path.join(src_dir, fn), os.path.join(stage, fn), disp, dn, dt, oldp, newpos, body, key)
    print("STAGED", stage)


if __name__ == "__main__":
    main()
