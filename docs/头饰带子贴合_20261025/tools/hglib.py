import sys, os
sys.path.insert(0, r"E:\documents\Paradox Interactive\Crusader Kings III\mod\HanDyansty\docs\服装穿模审计_20261022\tools")
import numpy as np
from pdxlib import pdx_data
from scipy.spatial import cKDTree
GAME = r"D:\SteamLibrary\steamapps\common\Crusader Kings III\game\gfx\models\portraits"

def shapes(path):
    root = pdx_data.read_meshfile(path)
    out = []
    for o in root:
        for s in o:
            m = s.find("mesh")
            if m is None: continue
            bones = None
            sk = next((c for c in s if c.tag == "skeleton"), None)
            if sk is not None:
                bones = {int(j.attrib["ix"][0]): j.tag.split(":")[-1] for j in sk}
            P = np.array(m.attrib["p"], dtype=np.float64).reshape(-1, 3)
            T = np.array(m.attrib["tri"], dtype=np.int64).reshape(-1, 3)
            sk_ = m.find("skin")
            ix = w = None
            if sk_ is not None:
                nb = sk_.attrib["bones"][0]
                ix = np.array(sk_.attrib["ix"]).reshape(-1, nb)
                w = np.array(sk_.attrib["w"], dtype=np.float64).reshape(-1, nb)
            out.append(dict(name=s.tag, P=P, T=T, ix=ix, w=w, bones=bones, node=s))
    return root, out

class Head:
    def __init__(self, sex="m", n=6):
        d = "female_head" if sex == "f" else "male_head"
        root, sh = shapes(os.path.join(GAME, d, d + ".mesh"))
        h = sh[0]
        self.sh = sh
        self.P, self.T = h["P"], h["T"]
        a, b, c = (self.P[self.T[:, i]] for i in range(3))
        fn = np.cross(b - a, c - a); fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
        pts, nrm, tid, bw = [], [], [], []
        for i in range(n + 1):
            for j in range(n + 1 - i):
                u, v = i / n, j / n
                pts.append(a * (1 - u - v) + b * u + c * v); nrm.append(fn)
                tid.append(np.arange(len(self.T))); bw.append(np.tile([1 - u - v, u, v], (len(self.T), 1)))
        self.sp, self.sn = np.concatenate(pts), np.concatenate(nrm)
        self.st, self.sb = np.concatenate(tid), np.concatenate(bw)
        self.kd = cKDTree(self.sp)
    def signed(self, Q):
        d, i = self.kd.query(Q)
        s = np.sign(np.einsum("ij,ij->i", Q - self.sp[i], self.sn[i]))
        return d * s, i

def components(P, T, tol=1e-3):
    key = np.round(P / tol).astype(np.int64)
    _, weld = np.unique(key, axis=0, return_inverse=True)
    weld = weld.ravel()
    parent = np.arange(weld.max() + 1)
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    for t in T:
        a, b, c = (find(weld[i]) for i in t)
        parent[b] = a; parent[find(c)] = a
    roots = np.array([find(w) for w in weld])
    _, comp = np.unique(roots, return_inverse=True)
    return comp.ravel()

JAWSET = {"bn_h_jaw","bn_h_jaw_low","bn_h_jaw_l_side","bn_h_jaw_r_side","bn_h_chin_l_side","bn_h_chin_r_side","bn_h_cheek_l_side","bn_h_cheek_r_side","bn_h_face_lower","bn_h_mouth_lowerLip","bn_h_mouth_l_lowerLip","bn_h_mouth_r_lowerLip"}
def jawfrac(s, mask):
    if s["ix"] is None: return 0.0
    tot = jw = 0.0
    for row_i, row_w in zip(s["ix"][mask], s["w"][mask]):
        for b, ww in zip(row_i, row_w):
            tot += ww
            if s["bones"].get(int(b), "") in JAWSET: jw += ww
    return jw / max(tot, 1e-9)
