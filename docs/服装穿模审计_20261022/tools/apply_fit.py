"""Heavy_dark (hd_frontier_xiongnu_heavy_dark) fit for BOTH sexes -> staging dir.

python apply_fit.py <src_dir> <stage_dir>
Rules (user-approved 2026-10-22):
  chest_1   : front bulge pulled back to body_front - g (vanilla war_nob_01 gap), keep layer order with slope K_KEEP
  sleeves_1 : only torso-bone vertices (undertunic front panel) pulled back to body_front - g_in
  shoulder_1, collar_1 (fur cards): shell projection onto shrunk body surface, thickness FUR_LO..FUR_HI (fluffy)
  every *_bs_*.mesh gets the same per-vertex displacement as the base (body-type deltas preserved)
"""
import os
import shutil
import sys

import numpy as np

sys.path.insert(0, ".")
from pdxlib import pdx_data  # noqa: E402

GAME = r"D:\SteamLibrary\steamapps\common\Crusader Kings III\game\gfx\models\portraits"
K_KEEP = 0.10      # keep 10% of the forward excess so layered strips stay ordered (no z-fighting)
FUR_LO, FUR_HI, FUR_IN_SLOPE, FUR_MIN = 3.0, 10.0, 0.10, 1.0

SEX = {
    "m": dict(sex="m", body="male_body/male_body.mesh", bsdir="male_body/blendshapes", shrink="male_bs_body_shrink_%s.mesh",
              g=3.7, g_in=2.2, ramp=(82.0, 95.0, 135.0, 148.0)),
    "f": dict(sex="f", body="female_body/female_body.mesh", bsdir="female_body/blendshapes", shrink="female_bs_body_shrink_%s.mesh",
              g=3.4, g_in=1.6, ramp=(76.0, 88.0, 126.0, 137.0)),
}
TORSO_BONES = ("bn_sp_thoracic", "bn_sp_lumbar", "body_root")
MORPH_FILES = {
    "m": {"fat": "male_bs_body_fat_1", "gaunt": "male_bs_body_gaunt_1", "musc": "male_bs_body_muscular_1", "old": "male_bs_body_old_1", "dwarf": "male_bs_body_dwarf_1"},
    "f": {"fat": "female_bs_body_fat_1", "gaunt": "female_bs_body_gaunt_1", "musc": "female_bs_body_muscular_1", "old": "female_bs_body_old_1", "dwarf": "female_bs_body_dwarf_1",
          "pregnant": "female_bs_body_pregnant_1", "bust_max": "female_bs_body_breast_size_max", "bust_min": "female_bs_body_breast_size_min"},
}


def first_mesh(root):
    for o in root.iter("object"):
        for s in o:
            if s.find("mesh") is not None:
                return s
    raise RuntimeError("no mesh")


def positions(path):
    m = first_mesh(pdx_data.read_meshfile(path)).find("mesh")
    return np.array(m.attrib["p"], dtype=np.float64).reshape(-1, 3), np.array(m.attrib["tri"], dtype=np.int64).reshape(-1, 3)


class BodyModel:
    def __init__(self, cfg):
        self.cfg = cfg
        self.P0, self.tri = positions(os.path.join(GAME, cfg["body"]))
        self.shrunk = self.P0.copy()
        for nm in ("arms", "chest", "belly"):
            self.shrunk += positions(os.path.join(GAME, cfg["bsdir"], cfg["shrink"] % nm))[0] - self.P0
        a, b, c = (self.shrunk[self.tri[:, i]] for i in range(3))
        fn = np.cross(b - a, c - a)
        fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
        pts, nrm = [], []
        n = 4
        for i in range(n + 1):
            for j in range(n + 1 - i):
                u, v = i / n, j / n
                pts.append(a * (1 - u - v) + b * u + c * v)
                nrm.append(fn)
        self.sp, self.sn = np.concatenate(pts), np.concatenate(nrm)
        # samples on the UNSHRUNK base body with barycentric info, for transferring body-morph deltas
        a0, b0, c0 = (self.P0[self.tri[:, i]] for i in range(3))
        bp, bt, bw = [], [], []
        for i in range(n + 1):
            for j in range(n + 1 - i):
                u, v = i / n, j / n
                bp.append(a0 * (1 - u - v) + b0 * u + c0 * v)
                bt.append(np.arange(len(self.tri)))
                bw.append(np.tile([1 - u - v, u, v], (len(self.tri), 1)))
        self.bp, self.bt, self.bw = np.concatenate(bp), np.concatenate(bt), np.concatenate(bw)
        self.morph_sample = {}
        self.yb = np.arange(60.0, 160.0, 2.0)
        self.xb = [0, 8, 16, 24, 32]
        self.front = self._front_table()

    def _front_table(self):
        t = np.full((len(self.yb), len(self.xb) - 1), np.nan)
        for yi, y in enumerate(self.yb):
            for xi in range(len(self.xb) - 1):
                s = self.P0[(np.abs(self.P0[:, 1] - y) < 2.5) & (np.abs(self.P0[:, 0]) >= self.xb[xi]) & (np.abs(self.P0[:, 0]) < self.xb[xi + 1])]
                if len(s) > 2:
                    t[yi, xi] = s[:, 2].min()
        for xi in range(t.shape[1]):
            ok = ~np.isnan(t[:, xi])
            if ok.sum() < 3:
                t[:, xi] = t[:, xi - 1]
            else:
                t[:, xi] = np.interp(self.yb, self.yb[ok], t[ok, xi])
        return t

    def front_z(self, y, ax):
        xc = np.clip((ax - 4.0) / 8.0, 0, len(self.xb) - 2)
        x0 = np.floor(xc).astype(int)
        x1 = np.minimum(x0 + 1, len(self.xb) - 2)
        fx = xc - x0
        out = np.empty(len(y))
        for i in range(len(y)):
            r0 = np.interp(y[i], self.yb, self.front[:, x0[i]])
            r1 = np.interp(y[i], self.yb, self.front[:, x1[i]])
            out[i] = r0 * (1 - fx[i]) + r1 * fx[i]
        return out

    def morph_delta_at(self, key, pts):
        """body-morph delta transferred to points by nearest base-body sample (same idea as the original pipeline)."""
        if key not in self.morph_sample:
            d = positions(os.path.join(GAME, self.cfg["bsdir"], MORPH_FILES[self.cfg["sex"]][key] + ".mesh"))[0] - self.P0
            tri_d = d[self.tri[self.bt]]  # (nsamples, 3 verts, 3)
            self.morph_sample[key] = (tri_d * self.bw[:, :, None]).sum(1)
        out = np.empty_like(pts)
        for s in range(0, len(pts), 64):
            blk = pts[s:s + 64]
            idx = ((blk[:, None, :] - self.bp[None, :, :]) ** 2).sum(-1).argmin(1)
            out[s:s + 64] = self.morph_sample[key][idx]
        return out

    def nearest(self, pts):
        q = np.empty_like(pts)
        nn = np.empty_like(pts)
        for s in range(0, len(pts), 64):
            blk = pts[s:s + 64]
            d2 = ((blk[:, None, :] - self.sp[None, :, :]) ** 2).sum(-1)
            idx = d2.argmin(1)
            q[s:s + 64] = self.sp[idx]
            nn[s:s + 64] = self.sn[idx]
        return q, nn


def ramp_w(y, ramp):
    a, b, c, d = ramp
    return np.clip((y - a) / (b - a), 0, 1) * np.clip((d - y) / (d - c), 0, 1)


def front_pullback(body, p, g, mask=None):
    y, ax = p[:, 1], np.abs(p[:, 0])
    T = body.front_z(y, ax) - g
    w = ramp_w(y, body.cfg["ramp"])
    q = p.copy()
    sel = p[:, 2] < T
    if mask is not None:
        sel &= mask
    q[sel, 2] = p[sel, 2] + w[sel] * (1.0 - K_KEEP) * (T[sel] - p[sel, 2])
    return q


def fur_shell(body, p):
    q, n = body.nearest(p)
    d = ((p - q) * n).sum(1)
    out = np.empty_like(d)
    span = FUR_HI - FUR_LO
    up = d > FUR_LO
    out[up] = FUR_LO + span * np.tanh((d[up] - FUR_LO) / span)
    out[~up] = np.maximum(FUR_LO + FUR_IN_SLOPE * (d[~up] - FUR_LO), FUR_MIN)
    return q + n * out[:, None]


def joint_names(root):
    names = {}
    for sk in root.iter("skeleton"):
        for j in sk:
            names[int(j.attrib["ix"][0])] = j.tag.split(":")[-1]
    return names


def recompute_normals(p_old, p_new, tri, n_old, moved):
    key = np.round(p_old * 1e3).astype(np.int64)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    fn = np.cross(p_new[tri[:, 1]] - p_new[tri[:, 0]], p_new[tri[:, 2]] - p_new[tri[:, 0]])
    acc = np.zeros((inv.max() + 1, 3))
    for i in range(3):
        np.add.at(acc, inv[tri[:, i]], fn)
    nn = acc[inv]
    ln = np.linalg.norm(nn, axis=1)
    ok = ln > 1e-9
    nn[ok] /= ln[ok, None]
    dot = (nn * n_old).sum(1)
    flip = dot < 0
    nn[flip] *= -1
    dot = np.abs(dot)
    use = moved & ok & (dot > 0.2)
    out = n_old.copy()
    out[use] = nn[use]
    return out, int(use.sum())


def update_bounds(mesh_el):
    p = np.array(mesh_el.attrib["p"], dtype=np.float64).reshape(-1, 3)
    lo, hi = p.min(0), p.max(0)
    ab = mesh_el.find("aabb")
    ab.attrib["min"] = [float(x) for x in lo]
    ab.attrib["max"] = [float(x) for x in hi]
    c = (lo + hi) / 2
    mesh_el.attrib["boundingsphere"] = [float(c[0]), float(c[1]), float(c[2]), float(np.linalg.norm(p - c, axis=1).max())]


def process_base(src, dst, body, cfg):
    root = pdx_data.read_meshfile(src)
    jn = joint_names(root)
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
            newp = p
            renorm = False
            if "chest_1" in shape.tag:
                newp = front_pullback(body, p, cfg["g"])
                renorm = True
            elif "sleeves_1" in shape.tag:
                skin = m.find("skin")
                ix = np.array(skin.attrib["ix"], dtype=np.int64).reshape(-1, 4)
                w = np.array(skin.attrib["w"], dtype=np.float64).reshape(-1, 4)
                dom = ix[np.arange(len(ix)), w.argmax(1)]
                torso = np.array([jn.get(int(b), "") in TORSO_BONES for b in dom]) & (np.abs(p[:, 0]) < 24.0)
                newp = front_pullback(body, p, cfg["g_in"], mask=torso)
                renorm = True
            elif "shoulder_1" in shape.tag or "collar_1" in shape.tag:
                newp = fur_shell(body, p)
            d = newp - p
            moved = np.linalg.norm(d, axis=1) > 1e-6
            disp[shape.tag] = d
            oldp[shape.tag] = p
            newpos[shape.tag] = newp
            if renorm and moved.any():
                n_new, used = recompute_normals(p, newp, tri, n_old, moved)
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
                update_bounds(m)
            print("  %-3s %-52s moved=%4d/%4d mean=%.2f max=%.2f" % (os.path.basename(dst)[:2], shape.tag[-52:], int(moved.sum()), len(p), np.linalg.norm(d, axis=1).mean(), np.linalg.norm(d, axis=1).max()))
    pdx_data.write_meshfile(dst, root)
    return disp, dn, dt, oldp, newpos


def process_bs(src, dst, disp, dn, dt, oldp, newpos, body, key):
    root = pdx_data.read_meshfile(src)
    for o in root.iter("object"):
        for shape in o:
            m = shape.find("mesh")
            if m is None:
                continue
            p = np.array(m.attrib["p"], dtype=np.float64).reshape(-1, 3)
            if shape.tag not in disp or len(disp[shape.tag]) != len(p):
                raise RuntimeError("bs shape mismatch %s %s" % (src, shape.tag))
            dd = disp[shape.tag].copy()
            moved = np.linalg.norm(dd, axis=1) > 1e-6
            if moved.any() and key in MORPH_FILES[body.cfg["sex"]]:
                bs_old = p - oldp[shape.tag]
                t_old = body.morph_delta_at(key, oldp[shape.tag][moved])
                err = np.abs(bs_old[moved] - t_old).mean()
                if err < 1.0:
                    t_new = body.morph_delta_at(key, newpos[shape.tag][moved])
                    dd[moved] += t_new - t_old
                    print("    %-9s %-40s reanchor ok (old-delta vs transfer err=%.2f)" % (key, shape.tag[-40:], err))
                else:
                    print("    %-9s %-40s WARN transfer mismatch err=%.2f -> delta preserved" % (key, shape.tag[-40:], err))
            m.attrib["p"] = [float(x) for x in (p + dd).reshape(-1)]
            if np.abs(dn[shape.tag]).max() > 0 and "n" in m.attrib:
                n = np.array(m.attrib["n"], dtype=np.float64).reshape(-1, 3) + dn[shape.tag]
                ln = np.linalg.norm(n, axis=1, keepdims=True)
                n = n / np.maximum(ln, 1e-9)
                m.attrib["n"] = [float(x) for x in n.reshape(-1)]
                ta = np.array(m.attrib["ta"], dtype=np.float64).reshape(-1, 4)
                t = ta[:, :3] + dt[shape.tag]
                lt = np.linalg.norm(t, axis=1, keepdims=True)
                ta[:, :3] = t / np.maximum(lt, 1e-9)
                m.attrib["ta"] = [float(x) for x in ta.reshape(-1)]
            update_bounds(m)
    pdx_data.write_meshfile(dst, root)


def main():
    src_dir, stage = sys.argv[1], sys.argv[2]
    os.makedirs(stage, exist_ok=True)
    for sex, cfg in SEX.items():
        body = BodyModel(cfg)
        base_name = "%s_clothes_hd_frontier_xiongnu_heavy_dark.mesh" % sex
        print("== sex", sex, "front table y=100/120 central:", round(float(np.interp(100, body.yb, body.front[:, 0])), 1), round(float(np.interp(120, body.yb, body.front[:, 0])), 1))
        disp, dn, dt, oldp, newpos = process_base(os.path.join(src_dir, base_name), os.path.join(stage, base_name), body, cfg)
        for fn in sorted(os.listdir(src_dir)):
            if fn.startswith("%s_clothes_hd_frontier_xiongnu_heavy_dark_bs_" % sex) and fn.endswith(".mesh"):
                key = fn.split("_bs_")[1][:-5]
                process_bs(os.path.join(src_dir, fn), os.path.join(stage, fn), disp, dn, dt, oldp, newpos, body, key)
                print("  bs ok", fn)
    print("STAGED", stage)


if __name__ == "__main__":
    main()
