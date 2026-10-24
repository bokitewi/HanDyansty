"""Front-depth compression for layered chest garments (2026-10-24), staging only.

python compress_front.py <stage_root> <garment_dir> [<garment_dir> ...]      (env HD_CF_MODE=piece|linear, HD_CF_CFG=json)
Every vertex of every shape (all layers) in front of the torso is moved in z only:
    e  = H(|x|, y) - z            depth in front of the unshrunk body front (H = torso height field, slope-limited)
    e' = f(e)                     monotone, f(e) = e for e <= a, f(Emax) = T (per garment and sex)
           linear: a + k (e - a)
           piece : gap body..innermost layer (a..e_in) squeezed with KG, layers above e_in with kl
    z' = H - (e - w (e - e'))     w = w_y(y) * w_x(|x|) * armmask(x, y), all spatial
Same (x, y) => same mapping, monotone in e => stacked layers keep their order.
Normals/tangents use the deformation Jacobian (authored shading kept); every *_bs_* file gets the same
per-vertex displacement with the body-type delta re-anchored at the new position (apply_fit.process_bs).
"""
import json
import os
import sys

TOOLS = r"E:\documents\Paradox Interactive\Crusader Kings III\mod\HanDyansty\docs\服装穿模审计_20261022\tools"
sys.path.insert(0, TOOLS)
import numpy as np  # noqa: E402

import apply_fit as A  # noqa: E402
from pdxlib import pdx_data  # noqa: E402

# 输入必须是未压缩的原文件：HanJIn_Clothes 里现在已是压缩后的版本，默认读备份目录，防止二次压缩/拿错基准
BASE = r"E:\documents\Paradox Interactive\Crusader Kings III\mod\HanDyansty\docs\胸前压缩_备份_20261024"
CFG = {
    "m": dict(a=1.5, T=4.0, ry=(78.0, 90.0, 136.0, 148.0), rx=(17.0, 23.0), core_y=(92.0, 134.0)),
    "f": dict(a=1.3, T=3.6, ry=(72.0, 84.0, 126.0, 138.0), rx=(15.0, 21.0), core_y=(86.0, 124.0)),
}
if os.environ.get("HD_CF_CFG"):
    for sx, over in json.loads(os.environ["HD_CF_CFG"]).items():
        CFG[sx].update({k: tuple(v) if isinstance(v, list) else v for k, v in over.items()})
MODE = os.environ.get("HD_CF_MODE", "piece")
KG = float(os.environ.get("HD_CF_KG", "0.15"))   # piecewise: slope of the body..innermost-layer gap
MASK_BLUR = int(os.environ.get("HD_CF_MB", "1"))
KG_MIN = float(os.environ.get("HD_CF_KGMIN", "0.15"))   # local: slowest squeeze of the empty space under the stack
KL_MIN = 0.2                                             # local: never compress the layer stack below this
SLOPE = 0.8                                        # H may curve back at most this much per unit outward
SLOPE_Y = float(os.environ.get("HD_CF_SY", "0.4"))  # ... and per unit up/down
ARM = ("shoulder", "deltoid", "elbow", "forearm", "wrist", "_fi_", "sleeve")
LIMB = ("elbow", "forearm", "wrist", "_fi_", "hip", "knee", "ankle", "ftBall", "ftToe", "prop", "skirt", "cloak", "sleeve")


def smooth(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def bilinear(G, fx, fy):
    i, j = np.floor(fy).astype(int), np.floor(fx).astype(int)
    ty, tx = fy - i, fx - j
    return G[i, j] * (1 - tx) * (1 - ty) + G[i, j + 1] * tx * (1 - ty) + G[i + 1, j] * (1 - tx) * ty + G[i + 1, j + 1] * tx * ty


def blur3(G):
    ny, nx = G.shape
    P = np.pad(G, 1, mode="edge")
    return sum(P[1 + dy:1 + dy + ny, 1 + dx:1 + dx + nx] for dy in (-1, 0, 1) for dx in (-1, 0, 1)) / 9.0


class FrontField:
    """H(|x|, y): min z of the unshrunk, front-facing, non-limb body surface; 1-unit cells, holes filled."""

    def __init__(self, sex):
        cfg = A.SEX[sex]
        root = pdx_data.read_meshfile(os.path.join(A.GAME, cfg["body"]))
        jn = A.joint_names(root)
        m = A.first_mesh(root).find("mesh")
        p = np.array(m.attrib["p"], dtype=np.float64).reshape(-1, 3)
        tri = np.array(m.attrib["tri"], dtype=np.int64).reshape(-1, 3)
        sk = m.find("skin")
        ix = np.array(sk.attrib["ix"], dtype=np.int64).reshape(-1, 4)
        w = np.array(sk.attrib["w"], dtype=np.float64).reshape(-1, 4)
        dom = ix[np.arange(len(ix)), w.argmax(1)]
        torso_v = np.array([not any(t in jn.get(int(b), "") for t in LIMB) for b in dom])
        tri = tri[torso_v[tri].all(1)]
        a, b, c = (p[tri[:, i]] for i in range(3))
        fn = np.cross(b - a, c - a)
        fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
        keep = fn[:, 2] < -0.3          # outward normal faces the viewer (-z); checked: chest centre nz ~ -0.95
        self.y0 = 50.0
        self.nx, self.ny = 31, 125

        def raster(a, b, c):
            pts = []
            n = 6
            for i in range(n + 1):
                for j in range(n + 1 - i):
                    u, v = i / n, j / n
                    pts.append(a * (1 - u - v) + b * u + c * v)
            s = np.concatenate(pts)
            G = np.full((self.ny, self.nx), np.inf)
            xi = np.clip(np.round(np.abs(s[:, 0])).astype(int), 0, self.nx - 1)
            yi = np.round(s[:, 1] - self.y0).astype(int)
            ok = (yi >= 0) & (yi < self.ny)
            np.minimum.at(G, (yi[ok], xi[ok]), s[ok, 2])
            return G

        H = raster(a[keep], b[keep], c[keep])
        H[np.isinf(H)] = np.nan
        ALL = raster(a, b, c)   # every non-limb sample: the side-facing deltoid / armpit fronts the filter drops
        for r in range(self.ny):
            good = ~np.isnan(H[r])
            if good.sum() >= 2:
                H[r] = np.interp(np.arange(self.nx), np.nonzero(good)[0], H[r, good])
        for col in range(self.nx):
            good = ~np.isnan(H[:, col])
            if good.sum() >= 2:
                H[:, col] = np.interp(np.arange(self.ny), np.nonzero(good)[0], H[good, col])
        H = np.minimum(H, ALL)                 # never behind any real body sample of the cell
        for col in range(1, self.nx):
            H[:, col] = np.minimum(H[:, col], H[:, col - 1] + SLOPE)
        for r in range(self.ny - 2, -1, -1):   # downward from the chest: cloth drapes, front may recede <= SLOPE_Y per unit
            H[r] = np.minimum(H[r], H[r + 1] + SLOPE_Y)
        for r in range(1, self.ny):            # upward toward the collar, same limit
            H[r] = np.minimum(H[r], H[r - 1] + SLOPE_Y)
        for _ in range(2):
            H = blur3(H)
        self.H = H

    def __call__(self, x, y):
        return bilinear(self.H, np.clip(np.abs(x), 0, self.nx - 1.001), np.clip(y - self.y0, 0, self.ny - 1.001))


class ArmMask:
    """Spatial mask from skin weights: mean arm-bone weight of ALL garment vertices per 2x2 (x, y) cell,
    3x3 box-summed, then 1 - smoothstep((armfrac - 0.3) / 0.4). Same (x, y) => same mask for every layer."""

    def __init__(self, root):
        jn = A.joint_names(root)
        arm_ids = [i for i, nm in jn.items() if any(t in nm for t in ARM)]
        xs, ys, aw = [], [], []
        for s in shapes(root):
            m = s.find("mesh")
            p = np.array(m.attrib["p"], dtype=np.float64).reshape(-1, 3)
            sk = m.find("skin")
            if sk is None:
                a = np.zeros(len(p))
            else:
                ix = np.array(sk.attrib["ix"], dtype=np.int64).reshape(-1, 4)
                w = np.array(sk.attrib["w"], dtype=np.float64).reshape(-1, 4)
                a = (w * np.isin(ix, arm_ids)).sum(1)
            xs.append(p[:, 0])
            ys.append(p[:, 1])
            aw.append(a)
        x, y, a = np.concatenate(xs), np.concatenate(ys), np.concatenate(aw)
        self.x0, self.y0, self.c = -40.0, 50.0, 2.0
        self.nx, self.ny = 41, 60
        S = np.zeros((self.ny, self.nx))
        N = np.zeros((self.ny, self.nx))
        i = np.clip(np.round((y - self.y0) / self.c).astype(int), 0, self.ny - 1)
        j = np.clip(np.round((x - self.x0) / self.c).astype(int), 0, self.nx - 1)
        np.add.at(S, (i, j), a)
        np.add.at(N, (i, j), 1.0)
        for _ in range(MASK_BLUR):
            S, N = blur3(S) * 9.0, blur3(N) * 9.0
        frac = np.where(N > 0, S / np.maximum(N, 1e-9), 0.0)
        self.M = 1.0 - smooth((frac - 0.3) / 0.4)

    def __call__(self, x, y):
        return bilinear(self.M, np.clip((x - self.x0) / self.c, 0, self.nx - 1.001), np.clip((y - self.y0) / self.c, 0, self.ny - 1.001))


def weight(cfg, x, y):
    y0, y1, y2, y3 = cfg["ry"]
    wy = smooth((y - y0) / (y1 - y0)) * smooth((y3 - y) / (y3 - y2))
    x0, x1 = cfg["rx"]
    wx = 1.0 - smooth((np.abs(x) - x0) / (x1 - x0))
    return wy * wx


class LocalCurve:
    """Stack-aware local curve. Per 2x2 (x, y) cell: e_lo = front of the innermost layer (min over shapes of the
    shape's front-most depth, shapes above a + 0.5 only), e_hi = outermost front. The empty space a..e_lo is
    squeezed first (slope kg >= KG_MIN); the layer stack e_lo..e_hi keeps slope 1 unless that is not enough to
    bring e_hi down to T, then slope kl < 1. Cells already at or under T stay unchanged. Parameter grids are
    hole-filled and blurred, so the map stays smooth; slopes > 0 keep it monotone along every z ray."""

    def __init__(self, root, cfg, F):
        self.a, self.T = cfg["a"], cfg["T"]
        self.x0, self.y0, self.c = -32.0, 50.0, 2.0
        self.nx, self.ny = 33, 61
        lo = np.full((self.ny, self.nx), np.inf)
        hi = np.full((self.ny, self.nx), -np.inf)
        for s in shapes(root):
            m = s.find("mesh")
            p = np.array(m.attrib["p"], dtype=np.float64).reshape(-1, 3)
            t = np.array(m.attrib["tri"], dtype=np.int64).reshape(-1, 3)
            if not len(t):
                continue
            a_, b_, c_ = (p[t[:, i]] for i in range(3))
            q = np.concatenate([a_ * (1 - u - v) + b_ * u + c_ * v for u, v in
                                ((0, 0), (1, 0), (0, 1), (1 / 3, 1 / 3), (0.5, 0), (0, 0.5), (0.5, 0.5))])
            e = F(q[:, 0], q[:, 1]) - q[:, 2]
            i = np.round((q[:, 1] - self.y0) / self.c).astype(int)
            j = np.round((q[:, 0] - self.x0) / self.c).astype(int)
            ok = (i >= 0) & (i < self.ny) & (j >= 0) & (j < self.nx)
            front = np.full((self.ny, self.nx), -np.inf)
            np.maximum.at(front, (i[ok], j[ok]), e[ok])
            hi = np.maximum(hi, front)
            sel = front > self.a + 0.5
            lo[sel] = np.minimum(lo[sel], front[sel])
        valid = np.isfinite(lo) & np.isfinite(hi)
        lo = np.where(valid, lo, np.nan)
        hi = np.where(valid, np.maximum(hi, lo), np.nan)
        lo, hi = self._fill(lo), self._fill(hi)
        P = np.pad(hi, 1, mode="edge")   # local max first, so blurred e_hi does not undercut local peaks
        hi = np.max(np.stack([P[1 + dy:1 + dy + self.ny, 1 + dx:1 + dx + self.nx] for dy in (-1, 0, 1) for dx in (-1, 0, 1)]), 0)
        for _ in range(2):
            lo, hi = blur3(lo), blur3(hi)
        hi = np.maximum(hi, lo)
        a, T = self.a, self.T
        need = hi > T
        stack = np.maximum(hi - lo, 0.0)
        span = np.maximum(lo - a, 1e-6)
        kg = np.clip((T - a - stack) / span, KG_MIN, 1.0)
        kl = np.clip((T - a - kg * (lo - a)) / np.maximum(stack, 0.5), KL_MIN, 1.0)
        self.kg = np.where(need, kg, 1.0)
        self.kl = np.where(need, kl, 1.0)
        self.lo = np.maximum(lo, a)
        for _ in range(2):
            self.kg, self.kl = blur3(self.kg), blur3(self.kl)
        self.stats = dict(lo=lo, hi=hi)

    @staticmethod
    def _fill(G):
        G = G.copy()
        for _ in range(40):
            bad = np.isnan(G)
            if not bad.any():
                break
            P = np.pad(G, 1, mode="edge")
            nb = np.stack([P[1 + dy:1 + dy + G.shape[0], 1 + dx:1 + dx + G.shape[1]] for dy in (-1, 0, 1) for dx in (-1, 0, 1)])
            with np.errstate(all="ignore"):
                mean = np.nanmean(nb, 0)
            G[bad] = mean[bad]
        G[np.isnan(G)] = np.nanmedian(G) if np.isfinite(G).any() else 0.0
        return G

    def __call__(self, e, x, y):
        fx = np.clip((x - self.x0) / self.c, 0, self.nx - 1.001)
        fy = np.clip((y - self.y0) / self.c, 0, self.ny - 1.001)
        lo, kg, kl = bilinear(self.lo, fx, fy), bilinear(self.kg, fx, fy), bilinear(self.kl, fx, fy)
        a = self.a
        f_lo = a + kg * (e - a)
        f_hi = a + kg * (lo - a) + kl * (e - lo)
        return np.where(e <= a, e, np.where(e <= lo, f_lo, f_hi))


def curve(k, e, a, x=None, y=None):
    """k = ("linear", k) | ("piece", e_in, kg, kl) | LocalCurve: monotone f(e) with f(e) = e below a."""
    if isinstance(k, LocalCurve):
        return k(e, x, y)
    if k[0] == "linear":
        return np.where(e > a, a + k[1] * (e - a), e)
    _, e_in, kg, kl = k
    lo = a + kg * (e - a)
    hi = a + kg * (e_in - a) + kl * (e - e_in)
    return np.where(e <= a, e, np.where(e <= e_in, lo, hi))


def deform(cfg, F, k, p, mask=None):
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    H = F(x, y)
    e = H - z
    w = weight(cfg, x, y)
    if mask is not None:
        w = w * mask(x, y)
    e_new = e - w * (e - curve(k, e, cfg["a"], x, y))
    out = p.copy()
    out[:, 2] = H - e_new
    return out


def jac_normals(cfg, F, k, p, n, ta, mask=None):
    """Transform normals by J^-T and tangents by J for the map (x, y, z) -> (x, y, g(x, y, z))."""
    h = 0.05
    g = lambda q: deform(cfg, F, k, q, mask)[:, 2]  # noqa: E731
    d = []
    for ax in range(3):
        qp, qm = p.copy(), p.copy()
        qp[:, ax] += h
        qm[:, ax] -= h
        d.append((g(qp) - g(qm)) / (2 * h))
    gx, gy, gz = d
    gz = np.maximum(gz, 1e-3)
    nn = np.stack([n[:, 0] - gx / gz * n[:, 2], n[:, 1] - gy / gz * n[:, 2], n[:, 2] / gz], 1)
    nn /= np.maximum(np.linalg.norm(nn, axis=1, keepdims=True), 1e-12)
    t = ta[:, :3]
    tt = np.stack([t[:, 0], t[:, 1], gx * t[:, 0] + gy * t[:, 1] + gz * t[:, 2]], 1)
    tt -= nn * (nn * tt).sum(1, keepdims=True)
    ln = np.linalg.norm(tt, axis=1, keepdims=True)
    bad = ln[:, 0] < 1e-6
    tt[~bad] /= ln[~bad]
    tt[bad] = t[bad]
    out_ta = ta.copy()
    out_ta[:, :3] = tt
    return nn, out_ta


def shapes(root):
    for o in root.iter("object"):
        for s in o:
            if s.find("mesh") is not None:
                yield s


def core_cells(cfg, F, p):
    c = p[(np.abs(p[:, 0]) < 12) & (p[:, 1] > cfg["core_y"][0]) & (p[:, 1] < cfg["core_y"][1])]
    mx = {}
    if not len(c):
        return mx
    e = F(c[:, 0], c[:, 1]) - c[:, 2]
    cell = np.round(c[:, 0] / 2).astype(int) * 1000 + np.round(c[:, 1] / 2).astype(int)
    for cc, ee in zip(cell.tolist(), e.tolist()):
        if ee > mx.get(cc, -1e9):
            mx[cc] = ee
    return mx


def garment_emax(cfg, F, root):
    """p90 over core 2x2 cells of the outermost front depth."""
    ps = np.concatenate([np.array(s.find("mesh").attrib["p"], dtype=np.float64).reshape(-1, 3) for s in shapes(root)])
    mx = core_cells(cfg, F, ps)
    return float(np.percentile(list(mx.values()), 90)) if len(mx) >= 5 else None


def garment_ein(cfg, F, root):
    """median over core 2x2 cells of the innermost layer's front depth (front-most e per shape, min over shapes)."""
    per = {}
    for s in shapes(root):
        mx = core_cells(cfg, F, np.array(s.find("mesh").attrib["p"], dtype=np.float64).reshape(-1, 3))
        for cc, ee in mx.items():
            if ee > 0:
                per.setdefault(cc, []).append(ee)
    vals = [min(v) for v in per.values()]
    return float(np.median(vals)) if vals else None


def choose_curve(cfg, emax, e_in):
    a, T = cfg["a"], cfg["T"]
    if MODE == "piece" and e_in is not None and a + 0.5 < e_in < emax - 0.5:
        kl = (T - a - KG * (e_in - a)) / (emax - e_in)
        if KG < kl <= 1.0:
            return ("piece", e_in, KG, kl)
    return ("linear", (T - a) / (emax - a))


def process_base(src, dst, cfg, F, k):
    root = pdx_data.read_meshfile(src)
    mk = ArmMask(root)
    disp, dn, dt, oldp, newpos, stats = {}, {}, {}, {}, {}, []
    for s in shapes(root):
        m = s.find("mesh")
        p = np.array(m.attrib["p"], dtype=np.float64).reshape(-1, 3)
        n_old = np.array(m.attrib["n"], dtype=np.float64).reshape(-1, 3)
        ta_old = np.array(m.attrib["ta"], dtype=np.float64).reshape(-1, 4)
        newp = deform(cfg, F, k, p, mk)
        d = newp - p
        moved = np.abs(d[:, 2]) > 1e-6
        disp[s.tag], oldp[s.tag], newpos[s.tag] = d, p, newp
        if moved.any():
            n_new, ta_new = jac_normals(cfg, F, k, p, n_old, ta_old, mk)
            n_new[~moved], ta_new[~moved] = n_old[~moved], ta_old[~moved]
            dn[s.tag] = n_new - n_old
            dt[s.tag] = ta_new[:, :3] - ta_old[:, :3]
            m.attrib["p"] = [float(v) for v in newp.reshape(-1)]
            m.attrib["n"] = [float(v) for v in n_new.reshape(-1)]
            m.attrib["ta"] = [float(v) for v in ta_new.reshape(-1)]
            A.update_bounds(m)
        else:
            dn[s.tag] = np.zeros_like(n_old)
            dt[s.tag] = np.zeros((len(p), 3))
        stats.append((s.tag, int(moved.sum()), len(p), float(np.abs(d[:, 2]).max()) if len(p) else 0.0))
    pdx_data.write_meshfile(dst, root)
    return disp, dn, dt, oldp, newpos, stats


def run(stage_root, name):
    src_dir = os.path.join(BASE, name)
    stage = os.path.join(stage_root, name)
    os.makedirs(stage, exist_ok=True)
    report = {}
    for sex in ("m", "f"):
        base_name = "%s_clothes_%s.mesh" % (sex, name)
        src = os.path.join(src_dir, base_name)
        if not os.path.isfile(src):
            continue
        cfg = CFG[sex]
        F = FIELDS[sex]
        root0 = pdx_data.read_meshfile(src)
        emax = garment_emax(cfg, F, root0)
        if emax is None or emax <= cfg["T"]:
            report[sex] = dict(emax=emax, skipped=True)
            print("== %s %s Emax=%s -> skip" % (name, sex, emax))
            continue
        e_in = garment_ein(cfg, F, root0)
        if MODE == "local":
            k = LocalCurve(root0, cfg, F)
            ci = slice(int((cfg["core_y"][0] - k.y0) / k.c), int((cfg["core_y"][1] - k.y0) / k.c))
            cj = slice(int((-12 - k.x0) / k.c), int((12 - k.x0) / k.c) + 1)
            desc = "local lo~%.1f hi~%.1f kg~%.2f kl~%.2f" % (np.median(k.stats["lo"][ci, cj]), np.median(k.stats["hi"][ci, cj]),
                                                           np.median(k.kg[ci, cj]), np.median(k.kl[ci, cj]))
        else:
            k = choose_curve(cfg, emax, e_in)
            desc = str(tuple(round(v, 3) if isinstance(v, float) else v for v in k))
        print("== %s %s Emax=%.2f e_in=%s curve=%s" % (name, sex, emax, None if e_in is None else round(e_in, 2), desc))
        disp, dn, dt, oldp, newpos, stats = process_base(src, os.path.join(stage, base_name), cfg, F, k)
        for tag, mv, nv, mx in stats:
            print("   %-55s moved %5d/%5d  max dz %.2f" % (tag[-55:], mv, nv, mx))
        for fn in sorted(os.listdir(src_dir)):
            if fn.startswith("%s_clothes_%s_bs_" % (sex, name)) and fn.endswith(".mesh"):
                key = fn.split("_bs_")[1][:-5]
                A.process_bs(os.path.join(src_dir, fn), os.path.join(stage, fn), disp, dn, dt, oldp, newpos, BODIES[sex], key)
        report[sex] = dict(emax=emax, e_in=e_in, curve=desc, shapes=stats)
    return report


FIELDS, BODIES = {}, {}
if __name__ == "__main__":
    stage_root = sys.argv[1]
    for sx in ("m", "f"):
        FIELDS[sx] = FrontField(sx)
        BODIES[sx] = A.BodyModel(A.SEX[sx])
    rep = {}
    for nm in sys.argv[2:]:
        rep[nm] = run(stage_root, nm)
    os.makedirs(stage_root, exist_ok=True)
    json.dump(rep, open(os.path.join(stage_root, "compress_report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("STAGED", stage_root)
