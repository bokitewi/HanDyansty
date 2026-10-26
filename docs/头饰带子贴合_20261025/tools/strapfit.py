"""Chin-strap refit for TW3K-converted headgear (2026-10-25, user-approved: gap 0.4, re-skin to head bones,
revert the 10-19 inflate for liu_shi / lu_bu).

python strapfit.py <stage_dir> [folder ...]
For every strap vertex (strapsel.select):
  main cords : cross-section moved along the head normal so its innermost point sits G above the skin,
               blended by alpha (0 where the cord touches the hat body / above the hairline of cap hats);
               skin weights -> (1-alpha)*old + alpha*head weights at the projected point (top 4, renormalised);
               fat delta    -> (1-alpha)*old + alpha*head fat delta at the projected point.
  free parts : main-cord vertices hanging off the skin copy the displacement / weights / fat of the nearest attached one.
  knots      : rigid, follow the nearest attached main-cord vertex.
Normals / tangents are rotated by the change of the geometric normal. Base + _bs_fat written to stage_dir/<folder>/.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from strapsel import *  # noqa: E402,F401,F403
from scipy.spatial import cKDTree  # noqa: E402

G, GMIN = 0.4, 0.15
R_LOC, R_SM = 1.0, 1.5
D_FREE = 3.2
A0, A1 = 0.6, 4.0
L_GEO, B_GEO = 3.5, 1.5  # along-cord ramps from where the hat body covers the cord (position / skin)
LAP_IT = 8
EAR_NEAR = 1.5  # cord within this of an ear triangle copies the ear skin
B1 = 2.1  # skin/fat blend ramps faster than the position blend, so cords near the rim already follow the jaw
CAP_Y = {"m": (45.0, 49.0), "f": (43.0, 47.0)}
EAR = ("bn_h_ear_l_main", "bn_h_ear_r_main")


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def closest_on_tri(p, a, b, c):
    """Ericson 5.1.5; returns point and barycentric (u, v, w) for a, b, c."""
    ab, ac, ap = b - a, c - a, p - a
    d1, d2 = ab @ ap, ac @ ap
    if d1 <= 0 and d2 <= 0:
        return a, (1.0, 0.0, 0.0)
    bp = p - b
    d3, d4 = ab @ bp, ac @ bp
    if d3 >= 0 and d4 <= d3:
        return b, (0.0, 1.0, 0.0)
    vc = d1 * d4 - d3 * d2
    if vc <= 0 and d1 >= 0 and d3 <= 0:
        v = d1 / (d1 - d3)
        return a + v * ab, (1 - v, v, 0.0)
    cp = p - c
    d5, d6 = ab @ cp, ac @ cp
    if d6 >= 0 and d5 <= d6:
        return c, (0.0, 0.0, 1.0)
    vb = d5 * d2 - d1 * d6
    if vb <= 0 and d2 >= 0 and d6 <= 0:
        w = d2 / (d2 - d6)
        return a + w * ac, (1 - w, 0.0, w)
    va = d3 * d6 - d5 * d4
    if va <= 0 and (d4 - d3) >= 0 and (d5 - d6) >= 0:
        w = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        return b + w * (c - b), (0.0, 1 - w, w)
    den = 1.0 / (va + vb + vc)
    v, w = vb * den, vc * den
    return a + ab * v + ac * w, (1 - v - w, v, w)


def vertex_normals(P, T):
    a, b, c = (P[T[:, i]] for i in range(3))
    fn = np.cross(b - a, c - a)
    vn = np.zeros_like(P)
    for i in range(3):
        np.add.at(vn, T[:, i], fn)
    return vn / np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)


def welded_normals(P, T, tol=1e-3):
    key = np.round(P / tol).astype(np.int64)
    _, weld = np.unique(key, axis=0, return_inverse=True)
    weld = weld.ravel()
    Pw = np.zeros((weld.max() + 1, 3))
    Pw[weld] = P
    return vertex_normals(Pw, weld[T])[weld]


def rotate_min(a, b, v):
    """rotate v (N,3) by the minimal rotation taking unit a to unit b (row-wise)."""
    k = np.cross(a, b)
    s = np.linalg.norm(k, axis=1, keepdims=True)
    c = np.einsum("ij,ij->i", a, b)[:, None]
    kk = np.divide(k, s, out=np.zeros_like(k), where=s > 1e-9)
    out = v * c + np.cross(kk, v) * s + kk * np.einsum("ij,ij->i", kk, v)[:, None] * (1 - c)
    return np.where(s > 1e-9, out, v)


class HeadModel:
    def __init__(self, sex):
        d = "female_head" if sex == "f" else "male_head"
        root, sh = shapes(os.path.join(GAME, d, d + ".mesh"))
        h = sh[0]
        self.sex = sex
        self.P, self.T = h["P"], h["T"]
        self.vn = vertex_normals(self.P, self.T)
        self.ix, self.w, self.bones = h["ix"], h["w"], h["bones"]
        sk = next(c for c in h["node"] if c.tag == "skeleton")
        self.tx = {j.tag.split(":")[-1]: np.array(j.attrib["tx"], dtype=np.float64) for j in sk}
        ear = np.zeros(len(self.P))
        for k in range(self.ix.shape[1]):
            nm = np.array([self.bones.get(int(b), "") for b in self.ix[:, k]])
            ear += np.where(np.isin(nm, EAR), self.w[:, k], 0.0)
        self.ear_tri = (ear[self.T] > 0.25).any(1)
        _, fsh = shapes(os.path.join(GAME, d, "blendshapes", d.split("_")[0] + "_bs_fat_1_head.mesh"))
        self.fat = fsh[0]["P"] - self.P
        self.kd = {}
        for key, tris in (("noear", np.where(~self.ear_tri)[0]), ("all", np.arange(len(self.T)))):
            pts, tid = [], []
            a, b, c = (self.P[self.T[tris, i]] for i in range(3))
            n = 4
            for i in range(n + 1):
                for j in range(n + 1 - i):
                    u, v = i / n, j / n
                    pts.append(a * (1 - u - v) + b * u + c * v)
                    tid.append(tris)
            self.kd[key] = (cKDTree(np.concatenate(pts)), np.concatenate(tid))

    def project(self, Q, key="noear"):
        kd, tid = self.kd[key]
        _, ii = kd.query(Q, k=12)
        q = np.zeros_like(Q); n = np.zeros_like(Q); d = np.zeros(len(Q))
        tri = np.zeros(len(Q), np.int64); bary = np.zeros((len(Q), 3))
        for r, p in enumerate(Q):
            best = None
            for t in np.unique(tid[ii[r]]):
                a, b, c = self.P[self.T[t]]
                x, bc = closest_on_tri(p, a, b, c)
                dd = np.linalg.norm(p - x)
                if best is None or dd < best[0]:
                    best = (dd, x, t, bc)
            _, x, t, bc = best
            nn = (np.array(bc)[:, None] * self.vn[self.T[t]]).sum(0)
            nn /= np.linalg.norm(nn)
            q[r], n[r], tri[r], bary[r] = x, nn, t, bc
            d[r] = (p - x) @ nn
        return q, n, d, tri, bary

    def weights_at(self, tri, bary):
        out = {}
        for tv, tb in zip(self.T[tri], bary):
            for vi, bw in zip(tv, tb):
                for k in range(self.ix.shape[1]):
                    b = int(self.ix[vi, k])
                    if b < 0 or self.w[vi, k] <= 0:
                        continue
                    nm = self.bones[b]
                    out[nm] = out.get(nm, 0.0) + float(bw) * float(self.w[vi, k])
        return out

    def fat_at(self, tri, bary):
        """single point: tri (1,), bary (1, 3) -> (3,)"""
        return (np.asarray(bary)[0][:, None] * self.fat[self.T[int(tri[0])]]).sum(0)


def fat_head_model(sex):
    h = HeadModel(sex)
    h.P = h.P + h.fat
    h.vn = vertex_normals(h.P, h.T)
    for key, tris in (("noear", np.where(~h.ear_tri)[0]), ("all", np.arange(len(h.T)))):
        pts, tid = [], []
        a, b, c = (h.P[h.T[tris, i]] for i in range(3))
        for i in range(5):
            for j in range(5 - i):
                u, v = i / 4, j / 4
                pts.append(a * (1 - u - v) + b * u + c * v)
                tid.append(tris)
        h.kd[key] = (cKDTree(np.concatenate(pts)), np.concatenate(tid))
    return h


PUSH_MAX = 1.0


def floor_push(model, pts, cluster_of, gmin):
    """push points out of the (ear-less) head surface to gmin: knot clusters rigidly, cords per vertex."""
    q, n, d, _, _ = model.project(pts, "noear")
    push = np.minimum(np.maximum(gmin - d, 0.0), PUSH_MAX)[:, None] * n
    for c in np.unique(cluster_of[cluster_of >= 0]):
        sel = cluster_of == c
        j = np.argmin(np.where(sel, d, np.inf))
        push[sel] = n[j] * min(max(gmin - d[j], 0.0), PUSH_MAX)
    return pts + push


def chord_push(model, Pn, T, verts, kind_of_vert, gmin, iters=3):
    """make the strap surface (triangle interiors, not only vertices) clear the head by gmin.
    T: strap triangles (main cords only); pushes their vertices along the head normal."""
    if len(T) == 0:
        return Pn
    bc = np.array([(1 - i / 4 - j / 4, i / 4, j / 4) for i in range(5) for j in range(5 - i)])
    for _ in range(iters):
        sp = np.einsum("kb,tbx->tkx", bc, Pn[T]).reshape(-1, 3)
        d = model.project(sp, "noear")[2].reshape(len(T), len(bc))
        deficit = np.minimum(np.maximum(gmin - d.min(1), 0.0), PUSH_MAX)
        if deficit.max() < 1e-3:
            break
        need = np.zeros(len(Pn))
        for t, df in zip(T, deficit):
            if df > 0:
                need[t] = np.maximum(need[t], df)
        vs = np.where(need > 0)[0]
        n = model.project(Pn[vs], "noear")[1]
        Pn[vs] += n * need[vs, None]
    return Pn


def seg_hits(o, e, tris, eps=0.02):
    """does segment o->e (excluding its ends) cross any triangle in tris (N,3,3)?"""
    if len(tris) == 0:
        return False
    d = e - o
    v0, v1, v2 = tris[:, 0], tris[:, 1], tris[:, 2]
    e1, e2 = v1 - v0, v2 - v0
    pv = np.cross(d, e2)
    det = np.einsum("ij,ij->i", e1, pv)
    ok = np.abs(det) > 1e-12
    inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
    tv = o - v0
    u = np.einsum("ij,ij->i", tv, pv) * inv
    qv = np.cross(tv, e1)
    v = (qv @ d) * inv
    t = np.einsum("ij,ij->i", e2, qv) * inv
    return bool(np.any(ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > eps) & (t < 1 - eps)))


def seg_first_hit(o, e, tris, eps=1e-4):
    """smallest t in (eps, 1] where segment o->e enters a triangle of tris, else None."""
    if len(tris) == 0:
        return None
    d = e - o
    v0, v1, v2 = tris[:, 0], tris[:, 1], tris[:, 2]
    e1, e2 = v1 - v0, v2 - v0
    pv = np.cross(d, e2)
    det = np.einsum("ij,ij->i", e1, pv)
    ok = np.abs(det) > 1e-12
    inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
    tv = o - v0
    u = np.einsum("ij,ij->i", tv, pv) * inv
    qv = np.cross(tv, e1)
    v = (qv @ d) * inv
    t = np.einsum("ij,ij->i", e2, qv) * inv
    hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > eps) & (t <= 1)
    return float(t[hit].min()) if hit.any() else None


def strap_graph(P, T, ids):
    """sparse graph over vertex ids (global) using triangle edges + zero-length welds; returns (csr, local index map)."""
    from scipy.sparse import coo_matrix
    loc = {g: k for k, g in enumerate(ids)}
    rows, cols, ws = [], [], []
    idset = set(ids.tolist())
    for t in T:
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            if a in idset and b in idset:
                w = float(np.linalg.norm(P[a] - P[b])) + 1e-6
                rows += [loc[a], loc[b]]; cols += [loc[b], loc[a]]; ws += [w, w]
    key = np.round(P[ids] / 1e-3).astype(np.int64)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.ravel()
    for grp in np.unique(inv):
        mem = np.where(inv == grp)[0]
        for a in mem[1:]:
            rows += [mem[0], a]; cols += [a, mem[0]]; ws += [1e-6, 1e-6]
    n = len(ids)
    return coo_matrix((ws, (rows, cols)), shape=(n, n)).tocsr(), loc


def hat_bone_maps(s, head):
    sk = next(c for c in s["node"] if c.tag == "skeleton")
    name2ix, ok = {}, set()
    for j in sk:
        nm = j.tag.split(":")[-1]
        name2ix[nm] = int(j.attrib["ix"][0])
        if nm in head.tx and np.abs(np.array(j.attrib["tx"], dtype=np.float64) - head.tx[nm]).max() < 1e-3:
            ok.add(nm)
    return name2ix, ok


def top4(wd, ok):
    items = sorted(((v, k) for k, v in wd.items() if k in ok and v > 1e-4), reverse=True)[:4]
    tot = sum(v for v, _ in items)
    return [(k, v / tot) for v, k in items]


def neighbours(P, idx_sets, r):
    """list of neighbour index arrays (global idx) for each idx within radius r, restricted to the same set."""
    out = {}
    for ids in idx_sets:
        if len(ids) == 0:
            continue
        kd = cKDTree(P[ids])
        for loc, nb in zip(ids, kd.query_ball_point(P[ids], r)):
            out[loc] = ids[nb]
    return out


def fit_file(folder, sex, fn, stage, head, report, fhead=None):
    src = src_path(folder, fn)
    fat_fn = fn[:-5] + "_bs_fat.mesh"
    fat_src = os.path.join(os.path.dirname(src), fat_fn)
    root = pdx_data.read_meshfile(src)
    froot = pdx_data.read_meshfile(fat_src) if os.path.exists(fat_src) else None
    _, sh = shapes(src)
    # shapes() re-reads; bind to the nodes of *our* root so edits land in what we write
    nodes = [s for o in root for s in o if s.find("mesh") is not None]
    fnodes = {s.tag: s for o in froot for s in o if s.find("mesh") is not None} if froot is not None else {}
    assert [n.tag for n in nodes] == [s["name"] for s in sh]
    sel = select(folder, sex, sh)
    cap = HATS[folder].get("cap", False)
    # anchor geometry: everything that is not strap
    anc = []
    for s, r in zip(sh, sel):
        keep = ~r["mask"]
        if keep.sum() == 0:
            continue
        T = s["T"][keep[s["T"]].all(1)]
        a, b, c = (s["P"][T[:, i]] for i in range(3))
        for i in range(4):
            for j in range(4 - i):
                u, v = i / 3, j / 3
                anc.append(a * (1 - u - v) + b * u + c * v)
        anc.append(s["P"][keep])
    akd = cKDTree(np.concatenate(anc)) if anc else None
    body = []
    for s_, r_ in zip(sh, sel):
        if "plume" in s_["name"].lower():
            continue
        keep = ~r_["mask"]
        T_ = s_["T"][keep[s_["T"]].all(1)]
        if len(T_):
            body.append(s_["P"][T_])
    body = np.concatenate(body) if body else np.zeros((0, 3, 3))
    stats = []
    main_ref = []  # (pos, disp, weights(list), fatdelta) for knot lookup
    per_shape = []
    for si, (s, r, node) in enumerate(zip(sh, sel, nodes)):
        P = s["P"]
        comp, kind = r["comp"], r["kind"]
        main = np.array([kind[c] == "main" for c in comp])
        if not r["mask"].any():
            per_shape.append(None)
            continue
        name2ix, ok = hat_bone_maps(s, head)
        ix2name = {v: k for k, v in name2ix.items()}
        fnode = fnodes.get(s["name"])
        Pf = np.array(fnode.find("mesh").attrib["p"], dtype=np.float64).reshape(-1, 3) if fnode is not None else None
        disp = np.zeros_like(P)
        alpha = np.zeros(len(P))
        neww = {}
        newfat = {}
        mi = np.where(main)[0]
        if len(mi):
            q, n, d, tri, bary = head.project(P[mi])
            # skin source: where the cord lies on the ear, take the ear's weights (it moves with head width)
            qa_, na_, da_, tria, barya = head.project(P[mi], "all")
            on_ear = head.ear_tri[tria] & (da_ < EAR_NEAR)
            wtri = np.where(on_ear, tria, tri); wbary = np.where(on_ear[:, None], barya, bary)
            att = np.ones(len(mi), bool)  # every main-cord vertex is fitted; covered rings are held by alpha = 0
            ad = akd.query(P[mi])[0] if akd is not None else np.full(len(mi), 99.0)
            al = smoothstep(A0, A1, ad)
            be = smoothstep(A0, B1, ad)
            pos = {g: k for k, g in enumerate(mi)}
            sets = [mi[att & (comp[mi] == c)] for c in np.unique(comp[mi])]
            nb_loc = neighbours(P, sets, R_LOC)
            covered = np.array([seg_hits(P[g], q[k], body) for k, g in enumerate(mi)])
            # ring consistency: a cross-section is covered if any of its vertices is
            cov_ring = covered.copy()
            for k, g in enumerate(mi):
                if att[k] and not covered[k] and any(covered[pos[j]] for j in nb_loc[g]):
                    cov_ring[k] = True
            graphs = {}
            for c in np.unique(comp[mi]):
                ids = mi[comp[mi] == c]
                gr, loc = strap_graph(P, s["T"], ids)
                graphs[c] = (gr, loc, ids)
                srcs = [loc[g] for g in ids if cov_ring[pos[g]]]
                if not srcs:
                    continue
                from scipy.sparse.csgraph import dijkstra
                geo = dijkstra(gr, indices=srcs, min_only=True)
                for g in ids:
                    k = pos[g]
                    al[k] = smoothstep(0.0, L_GEO, geo[loc[g]])
                    be[k] = smoothstep(0.0, B_GEO, geo[loc[g]])
            if cap:
                hf = 1 - smoothstep(CAP_Y[sex][0], CAP_Y[sex][1], q[:, 1])
                al, be = al * hf, be * hf
            raw = np.zeros((len(mi), 3))
            for k, g in enumerate(mi):
                if not att[k]:
                    continue
                m_loc = min(d[pos[j]] for j in nb_loc[g])
                raw[k] = al[k] * (HATS[folder].get("gap", G) - m_loc) * n[k]
            # rigid cross-sections: average over the ring neighbourhood
            sm = np.zeros_like(raw)
            for k, g in enumerate(mi):
                if att[k]:
                    sm[k] = raw[[pos[j] for j in nb_loc[g]]].mean(0)
            # smooth along the cord graph (never across separate cord parts); covered rings stay put
            for c, (gr, loc, ids) in graphs.items():
                ks = np.array([pos[g] for g in ids])
                fixed = cov_ring[ks] | ~att[ks]
                D = sm[ks].copy()
                A = (gr > 0).astype(np.float64)
                deg = np.asarray(A.sum(1)).ravel()
                for _ in range(LAP_IT):
                    avg = (A @ D) / np.maximum(deg, 1)[:, None]
                    D = np.where(fixed[:, None] | (deg[:, None] == 0), D, 0.5 * D + 0.5 * avg)
                sm[ks] = D
            fac = np.ones(len(mi))
            for k, g in enumerate(mi):
                L = np.linalg.norm(sm[k])
                if L < 1e-4:
                    continue
                t = seg_first_hit(P[g], P[g] + sm[k], body)
                if t is not None:
                    fac[k] = max(0.0, t - 0.15 / L)
            fac_r = np.array([min(fac[pos[j]] for j in nb_loc[g]) for g in mi])
            sm *= fac_r[:, None]
            # weights + fat for attached
            for k, g in enumerate(mi):
                if not att[k]:
                    continue
                old = {ix2name[int(b)]: float(ww) for b, ww in zip(s["ix"][g], s["w"][g]) if ww > 0}
                hw = head.weights_at(np.array([wtri[k]]), np.array([wbary[k]]))
                mix = {}
                for nm, ww in old.items():
                    mix[nm] = mix.get(nm, 0.0) + (1 - be[k]) * ww
                for nm, ww in hw.items():
                    mix[nm] = mix.get(nm, 0.0) + be[k] * ww
                neww[g] = top4(mix, ok | set(old))
                if Pf is not None:
                    newfat[g] = (1 - be[k]) * (Pf[g] - P[g]) + be[k] * head.fat_at(np.array([tri[k]]), np.array([bary[k]]))
                disp[g] = sm[k]
                alpha[g] = al[k]
            # free (hanging) main vertices: copy nearest attached of the same component
            for c in np.unique(comp[mi]):
                ids = mi[comp[mi] == c]
                a_ids = ids[att[[pos[g] for g in ids]]]
                f_ids = ids[~att[[pos[g] for g in ids]]]
                if len(f_ids) == 0:
                    continue
                if len(a_ids) == 0:
                    continue
                kd = cKDTree(P[a_ids])
                _, nn_ = kd.query(P[f_ids])
                for g, j in zip(f_ids, a_ids[nn_]):
                    disp[g] = disp[j]; alpha[g] = alpha[j]; neww[g] = neww[j]
                    if Pf is not None:
                        newfat[g] = newfat[j]
            for g in mi:
                if g in neww:
                    main_ref.append((P[g], disp[g], neww[g], newfat.get(g), alpha[g]))
        per_shape.append(dict(P=P, comp=comp, kind=kind, disp=disp, alpha=alpha, neww=neww, newfat=newfat,
                              name2ix=name2ix, ok=ok, Pf=Pf, fnode=fnode))
    # knots: cluster neighbouring knot/tassel components (across shapes), move each cluster as one rigid piece and
    # skin it to the head at its attachment point (chin centre) so the loops do not pull apart
    kitems = []
    for si, (ps, s_) in enumerate(zip(per_shape, sh)):
        if ps is None:
            continue
        ps["kcl"] = -np.ones(len(ps["P"]), np.int64)
        for c, k in enumerate(ps["kind"]):
            if k == "knot":
                kitems.append((si, c, np.where(ps["comp"] == c)[0]))
    par = list(range(len(kitems)))

    def kfind(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a
    for a in range(len(kitems)):
        for b in range(a + 1, len(kitems)):
            pa = sh[kitems[a][0]]["P"][kitems[a][2]]
            pb = sh[kitems[b][0]]["P"][kitems[b][2]]
            if cKDTree(pa).query(pb)[0].min() < 1.5:
                par[kfind(b)] = kfind(a)
    clusters = {}
    for i_, it in enumerate(kitems):
        clusters.setdefault(kfind(i_), []).append(it)
    mkd = cKDTree(np.array([m[0] for m in main_ref])) if main_ref else None
    for cid, items in enumerate(clusters.values()):
        if mkd is None:
            break
        Kp = np.concatenate([sh[si]["P"][ids] for si, _, ids in items])
        near = sorted(set(j for lst in mkd.query_ball_point(Kp, 2.5) for j in lst))
        if not near:
            dd_, jj_ = mkd.query(Kp)
            near = [int(jj_[dd_.argmin()])]
        kdisp = np.mean([main_ref[j][1] for j in near], axis=0)
        kal = float(np.mean([main_ref[j][4] for j in near]))
        top = Kp[Kp[:, 1] >= np.percentile(Kp[:, 1], 70)].mean(0)
        _, _, _, ktri, kbary = head.project(top[None, :])
        hw = head.weights_at(ktri, kbary)
        kfat = head.fat_at(ktri, kbary)
        for si, c, ids in items:
            ps = per_shape[si]
            wl = top4(hw, ps["ok"])
            for g in ids:
                ps["disp"][g] = kdisp
                ps["neww"][g] = wl
                ps["alpha"][g] = kal
                ps["kcl"][g] = cid
                if ps["Pf"] is not None:
                    ps["newfat"][g] = kal * kfat + (1 - kal) * (ps["Pf"][g] - ps["P"][g])
    # collision floor against the full head (ears included) + write
    for ps, s, node in zip(per_shape, sh, nodes):
        if ps is None:
            continue
        P = ps["P"]
        moved = np.array(sorted(ps["neww"].keys()), dtype=np.int64)
        if len(moved) == 0:
            continue
        Pn = P.copy()
        Pn[moved] += ps["disp"][moved]
        kcl = ps.get("kcl", -np.ones(len(P), np.int64))
        Pn[moved] = floor_push(head, Pn[moved], kcl[moved], GMIN)
        main_v = np.array([ps["kind"][c] == "main" for c in ps["comp"]])
        movedset = np.zeros(len(P), bool); movedset[moved] = True
        Ts = s["T"][(main_v & movedset)[s["T"]].all(1)]
        Pn = chord_push(head, Pn, Ts, moved, None, HATS[folder].get("gap", G))
        d_before = head.project(P[moved], "all")[2]
        d_after = head.project(Pn[moved], "all")[2]
        # normals / tangents
        m = node.find("mesh")
        n_old = np.array(m.attrib["n"], dtype=np.float64).reshape(-1, 3)
        ta = np.array(m.attrib["ta"], dtype=np.float64).reshape(-1, 4)
        g0 = welded_normals(P, s["T"])
        g1 = welded_normals(Pn, s["T"])
        n_new = n_old.copy(); ta_new = ta.copy()
        n_new[moved] = rotate_min(g0[moved], g1[moved], n_old[moved])
        ta_new[moved, :3] = rotate_min(g0[moved], g1[moved], ta[moved, :3])
        m.attrib["p"] = [float(v) for v in Pn.reshape(-1)]
        m.attrib["n"] = [float(v) for v in n_new.reshape(-1)]
        m.attrib["ta"] = [float(v) for v in ta_new.reshape(-1)]
        # skin
        skin = m.find("skin")
        nb = skin.attrib["bones"][0]
        ix = np.array(skin.attrib["ix"], dtype=np.int64).reshape(-1, nb)
        w = np.array(skin.attrib["w"], dtype=np.float64).reshape(-1, nb)
        jaw = 0.0
        for g in moved:
            lst = ps["neww"][g]
            ix[g] = -1; w[g] = 0.0
            for k2, (nm, ww) in enumerate(lst[:nb]):
                ix[g, k2] = ps["name2ix"][nm]; w[g, k2] = ww
                if nm in JAWSET:
                    jaw += ww
            if (ix[g] < 0).all():
                raise RuntimeError("empty skin %s %d" % (s["name"], g))
        skin.attrib["ix"] = [int(v) for v in ix.reshape(-1)]
        skin.attrib["w"] = [float(v) for v in w.reshape(-1)]
        A_update_bounds(m)
        # fat blendshape
        if ps["fnode"] is not None:
            fm = ps["fnode"].find("mesh")
            Pf = ps["Pf"].copy()
            for g in moved:
                if g in ps["newfat"]:
                    Pf[g] = Pn[g] + ps["newfat"][g]
                else:
                    Pf[g] = Pf[g] + (Pn[g] - P[g])
            if fhead is not None:
                Pf[moved] = floor_push(fhead, Pf[moved], kcl[moved], GMIN)
                Pf = chord_push(fhead, Pf, Ts, moved, None, GMIN)
            fm.attrib["p"] = [float(v) for v in Pf.reshape(-1)]
            if "n" in fm.attrib:
                fn_ = np.array(fm.attrib["n"], dtype=np.float64).reshape(-1, 3)
                fn_[moved] = rotate_min(g0[moved], g1[moved], fn_[moved])
                fm.attrib["n"] = [float(v) for v in fn_.reshape(-1)]
            if "ta" in fm.attrib:
                ft = np.array(fm.attrib["ta"], dtype=np.float64).reshape(-1, 4)
                ft[moved, :3] = rotate_min(g0[moved], g1[moved], ft[moved, :3])
                fm.attrib["ta"] = [float(v) for v in ft.reshape(-1)]
            A_update_bounds(fm)
        dd = np.linalg.norm(Pn[moved] - P[moved], axis=1)
        att_mask = d_before < D_FREE
        stats.append(dict(shape=s["name"], moved=int(len(moved)), nv=int(len(P)),
                          disp_mean=round(float(dd.mean()), 3), disp_max=round(float(dd.max()), 3),
                          gap_before_med=round(float(np.median(d_before[att_mask])), 3) if att_mask.any() else None,
                          gap_after_med=round(float(np.median(d_after[att_mask])), 3) if att_mask.any() else None,
                          gap_after_min=round(float(d_after.min()), 3),
                          jaw_frac=round(jaw / len(moved), 3)))
    out_dir = os.path.join(stage, folder)
    os.makedirs(out_dir, exist_ok=True)
    pdx_data.write_meshfile(os.path.join(out_dir, fn), root)
    if froot is not None:
        pdx_data.write_meshfile(os.path.join(out_dir, fat_fn), froot)
    report[f"{folder}|{sex}"] = dict(src=src, stats=stats)
    for st in stats:
        print("  %-3s %-34s moved %4d/%5d disp mean %.2f max %.2f gap med %s -> %s min %.2f jaw %.2f" % (
            sex, st["shape"][-34:], st["moved"], st["nv"], st["disp_mean"], st["disp_max"], st["gap_before_med"],
            st["gap_after_med"], st["gap_after_min"], st["jaw_frac"]))


def A_update_bounds(mesh_el):
    p = np.array(mesh_el.attrib["p"], dtype=np.float64).reshape(-1, 3)
    lo, hi = p.min(0), p.max(0)
    ab = mesh_el.find("aabb")
    if ab is not None:
        ab.attrib["min"] = [float(x) for x in lo]
        ab.attrib["max"] = [float(x) for x in hi]
    c = (lo + hi) / 2
    if "boundingsphere" in mesh_el.attrib:
        mesh_el.attrib["boundingsphere"] = [float(c[0]), float(c[1]), float(c[2]), float(np.linalg.norm(p - c, axis=1).max())]


def main():
    stage = sys.argv[1]
    only = sys.argv[2:]
    heads = {"m": HeadModel("m"), "f": HeadModel("f")}
    fheads = {"m": fat_head_model("m"), "f": fat_head_model("f")}
    report = {}
    for folder in HATS:
        if only and folder not in only:
            continue
        for sex, fn in files_for(folder):
            print("==", folder, sex, "<-", "backup" if "备份" in src_path(folder, fn) else "current")
            fit_file(folder, sex, fn, stage, heads[sex], report, fheads[sex])
            # untouched sibling files of a reverted hat (e.g. other shapes) come with the backup copy
    json.dump(report, open(os.path.join(stage, "report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("STAGED", stage)


if __name__ == "__main__":
    main()
