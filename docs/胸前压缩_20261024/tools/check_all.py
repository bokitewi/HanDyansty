"""Per staged garment: z-ray layer flips + static poke-through per body type + new front protrusion profile.
python check_all.py <stage_dir> <out.json> <garment> [<garment> ...]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402

import compress_front as C  # noqa: E402
import static_inside as SI  # noqa: E402
import zbuf_check as Z  # noqa: E402

BASE = C.BASE


def zb(orig, new):
    a, b = Z.load(orig), Z.load(new)
    tags = list(a)
    tot = flips = deep = 0
    mx = 0.0
    for i in range(len(tags)):
        for j in range(i + 1, len(tags)):
            A0, B0, A1, B1 = a[tags[i]], a[tags[j]], b[tags[i]], b[tags[j]]
            ok = np.isfinite(A0) & np.isfinite(B0) & np.isfinite(A1) & np.isfinite(B1)
            with np.errstate(invalid="ignore"):
                d0, d1 = (A0 - B0)[ok], (A1 - B1)[ok]
            big = np.abs(d0) >= 0.2
            fl = big & (np.sign(d0) != np.sign(d1))
            tot += int(big.sum())
            flips += int(fl.sum())
            deep += int((fl & (np.abs(d1) > 0.3)).sum())
            if fl.any():
                mx = max(mx, float(np.abs(d1[fl]).max()))
    return dict(pairs=tot, flips=flips, flips_gt03=deep, max_flip=round(mx, 2))


DIRS = [np.array(v, float) / np.linalg.norm(v) for v in ((1, 0.05, 0.02), (-1, 0.05, 0.02), (0, 0.05, 1), (0, 0.05, -1), (0.7, -0.1, 0.7))]


def ray_inside(body, state, pts):
    """ray-parity (majority of 5 rays) against the shrunk, body-typed body: robust in the armpit crease."""
    P = body.shrunk.copy()
    if state != "base":
        f = SI.A.MORPH_FILES[body.cfg["sex"]][state]
        P += SI.A.positions(os.path.join(SI.A.GAME, body.cfg["bsdir"], f + ".mesh"))[0] - body.P0
    A_, B_, C_ = (P[body.tri[:, i]] for i in range(3))
    e1, e2 = B_ - A_, C_ - A_
    n = 0
    for o in pts:
        odd = 0
        for d in DIRS:
            h = np.cross(d, e2)
            a = (e1 * h).sum(1)
            ok = np.abs(a) > 1e-9
            f = np.where(ok, 1.0 / np.where(ok, a, 1.0), 0.0)
            s = o - A_
            u = f * (s * h).sum(1)
            q = np.cross(s, e1)
            v = f * (q * d).sum(1)
            t = f * (e2 * q).sum(1)
            odd += int((ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-6)).sum()) % 2
        n += odd >= 3
    return n


def emax_of(path, sex):
    cfg, F = C.CFG[sex], C.FIELDS[sex]
    from pdxlib import pdx_data
    return C.garment_emax(cfg, F, pdx_data.read_meshfile(path))


def main():
    sd, out = sys.argv[1], sys.argv[2]
    for sx in ("m", "f"):
        C.FIELDS[sx] = C.FrontField(sx)
    res = {}
    for g in sys.argv[3:]:
        for sex in ("m", "f"):
            stem = "%s_clothes_%s" % (sex, g)
            new = os.path.join(sd, g, stem + ".mesh")
            if not os.path.isfile(new):
                continue
            orig = os.path.join(BASE, g, stem + ".mesh")
            r = dict(z=zb(orig, new), emax_old=emax_of(orig, sex), emax_new=emax_of(new, sex))
            body = SI.Body(sex)
            st = {}
            for state in SI.STATES[sex]:
                fn = stem + (".mesh" if state == "base" else "_bs_%s.mesh" % state)
                if not os.path.isfile(os.path.join(BASE, g, fn)):
                    continue
                po, pn = SI.allp(os.path.join(BASE, g, fn)), SI.allp(os.path.join(sd, g, fn))
                o = body.inside(state, po)[0]
                n = body.inside(state, pn)[0]
                tr, sp, sn = body.tree(state)
                _, i0 = tr.query(po)
                _, i1 = tr.query(pn)
                d0 = ((po - sp[i0]) * sn[i0]).sum(1)
                d1 = ((pn - sp[i1]) * sn[i1]).sum(1)
                newly = np.nonzero((d1 < -1.0) & ~(d0 < -1.0))[0]
                st[state] = [o, n, len(newly), ray_inside(body, state, pn[newly]) if len(newly) else 0]
            r["inside_gt1"] = st
            res["%s|%s" % (g, sex)] = r
            worst = max((v[1] - v[0] for v in st.values()), default=0)
            ray = sum(v[3] for v in st.values())
            print("%-46s %s emax %.1f->%.1f flips %d/%d (>0.3: %d, max %.2f) inside worst +%d, newly-inside confirmed by rays: %d" % (
                g, sex, r["emax_old"], r["emax_new"], r["z"]["flips"], r["z"]["pairs"], r["z"]["flips_gt03"], r["z"]["max_flip"], worst, ray), flush=True)
    json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
