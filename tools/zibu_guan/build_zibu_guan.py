# Build the 缁布束发冠 (m_headgear_hd_huaxia_zibu_guan) in Blender 4.2 and export a PDX .mesh.
# A small gauze ring sits over the character's own topknot (no bun in the model); a tall gauze board
# rises from the ring's front and folds backward at the top; a metal filigree plaque sits on the front,
# a hairpin crosses the ring left-right.
# Usage: blender -b --factory-startup --python build_zibu_guan.py -- <jinxian.mesh> <male_head.mesh> <out_dir>
import bpy, bmesh, sys, os, math, importlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree

pdx = importlib.import_module("bl_ext.user_default.io_pdx_mesh.pdx_blender.blender_import_export")
JX, HEAD, OUT = sys.argv[sys.argv.index("--") + 1:][:3]
NAME = "m_headgear_hd_huaxia_zibu_guan"
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)

def import_new(path, skel):
    before = set(bpy.data.objects)
    pdx.import_meshfile(path, imp_mesh=True, imp_skel=skel, imp_locs=False)
    return [o for o in bpy.data.objects if o not in before]

jx_objs = import_new(JX, True)
rig = next(o for o in jx_objs if o.type == 'ARMATURE')
jx = next(o for o in jx_objs if o.type == 'MESH')
head = next(o for o in import_new(HEAD, False) if o.type == 'MESH')

def bvh_of(obj):
    me = obj.data
    me.calc_loop_triangles()
    vs = [obj.matrix_world @ v.co for v in me.vertices]
    tris = [tuple(t.vertices) for t in me.loop_triangles]
    return BVHTree.FromPolygons(vs, tris), vs, tris
head_bvh = bvh_of(head)[0]
HAIR_T = 0.35                # hair thickness over the scalp under the 'hat' tag (bs_hat flattens the hair)

# ---------------------------------------------------------------- crown frame (face is -Y)
TILT = math.radians(3)                      # ring leans back with the scalp slope under the topknot
BT = math.radians(3)                         # board world lean (it kinks forward above the ring)
O = Vector((0.0, -0.45, 59.4))                # ring base centre over the topknot
X = Vector((1, 0, 0))
U = Vector((0, math.sin(TILT), math.cos(TILT)))     # crown up
F = Vector((0, math.cos(TILT), -math.sin(TILT)))    # crown back
def L(x, f, u):
    return O + X * x + F * f + U * u

RA, RB = 3.9, 4.1            # ring outer half axes: front-back (a), left-right (b)
RT = 0.30                    # ring wall thickness
RTOP = 4.0                   # ring top (local up)
TOP_Z = 81.0                 # board top (user: longer than 进贤冠 75.5)
W0, W1 = 6.6, 10.0           # board width at the ring / at the top
CTOP = 0.55                  # board cross-section arch depth above the ring

# UV atlas regions (u0, v0, u1, v1), Blender v up
R_PANEL = (0.01, 0.01, 0.55, 0.99)
R_RING = (0.58, 0.82, 0.99, 0.99)
R_TRIM = (0.58, 0.72, 0.99, 0.79)
R_ORN = (0.58, 0.30, 0.86, 0.69)
R_METAL = (0.88, 0.30, 0.99, 0.69)
R_PIN = (0.58, 0.04, 0.99, 0.27)
def reg(r, fu, fv):
    return (r[0] + (r[2] - r[0]) * fu, r[1] + (r[3] - r[1]) * fv)

parts = {"hat": ([], [], [])}
P = parts["hat"]
V, Fc, Uv = P
def add_face(idx, uvs):
    Fc.append(tuple(idx)); Uv.append(tuple(uvs))
def nv(p):
    V.append(Vector(p)); return len(V) - 1

# ---------------------------------------------------------------- ring (束发冠圈), bottom conforms to the hair
NR = 40
def ring_xy(i, shrink=0.0):
    t = 2 * math.pi * i / NR
    return (RB - shrink) * math.sin(t), -(RA - shrink) * math.cos(t)     # i=0 at the front
def ground_u(x, f):
    # rest on the hair cap (scalp + HAIR_T), ignoring the bun that the ring encloses; sink 0.4 into the hair
    hit = head_bvh.ray_cast(L(x, f, 12.0), -U)
    if hit[0] is None:
        return 0.0
    return max(-1.6, min((hit[0] - O).dot(U) + HAIR_T - 0.15, RTOP - 3.0))
ring = []
for i in range(NR):
    xo, fo = ring_xy(i)
    xi, fi = ring_xy(i, RT)
    ub = ground_u(xo, fo)
    ring.append((nv(L(xo, fo, ub)), nv(L(xo, fo, RTOP)), nv(L(xi, fi, RTOP)), nv(L(xi, fi, ub))))
U0 = ground_u(0.0, -RA)          # board base = ring front base
for i in range(NR):
    a, b = ring[i], ring[(i + 1) % NR]
    f0, f1 = i / NR, (i + 1) / NR
    add_face((a[0], b[0], b[1], a[1]), (reg(R_RING, f0, 0), reg(R_RING, f1, 0), reg(R_RING, f1, 0.6), reg(R_RING, f0, 0.6)))
    add_face((a[1], b[1], b[2], a[2]), (reg(R_RING, f0, 0.62), reg(R_RING, f1, 0.62), reg(R_RING, f1, 0.7), reg(R_RING, f0, 0.7)))
    add_face((a[2], b[2], b[3], a[3]), (reg(R_RING, f0, 0.72), reg(R_RING, f1, 0.72), reg(R_RING, f1, 1.0), reg(R_RING, f0, 1.0)))

# ---------------------------------------------------------------- board centreline (turtle in the F-U plane)
# heading angle al: 0 = up, 90 = back, >90 = drooping back down. Outward normal N = U sin(al) - F cos(al).
def head_vec(al):
    return U * math.cos(al) + F * math.sin(al)
def out_vec(al):
    return U * math.sin(al) - F * math.cos(al)
base = O + F * (-RA - 0.06) + U * U0
RINGH = RTOP - U0
cl = [(base.copy(), 0.0, 0.0)]              # (point, heading rad, arc length)
p, al, s = base.copy(), 0.0, 0.0
def run(segs):
    global p, al, s
    for kind, a, deg in segs:
        if kind == "line":
            n = max(2, int(a / 0.7))
            for k in range(1, n + 1):
                cl.append((p + head_vec(al) * (a * k / n), al, s + a * k / n))
            p = p + head_vec(al) * a; s += a
        elif abs(deg) >= 0.5:
            r, d = a, math.radians(deg)
            sg = 1 if d > 0 else -1
            n = max(3, int(abs(deg) / 10))
            c = p - out_vec(al) * (r * sg)      # +turn bends back (centre behind), -turn bends forward
            for k in range(1, n + 1):
                al2 = al + d * k / n
                cl.append((c + out_vec(al2) * (r * sg), al2, s + r * abs(d) * k / n))
            p = c + out_vec(al + d) * (r * sg); al += d; s += r * abs(d)
KINK = math.degrees(TILT - BT)
run([("line", RINGH, 0), ("turn", 2.0, -KINK)])
LKINK = s
HP2 = (TOP_Z - p.z) / math.cos(BT)
run([("line", HP2, 0)])
LBOARD = s
# bend radii must exceed the cross-section arch depth CTOP, or the board edges pinch to a point
run([("turn", 1.3, 90 + KINK), ("turn", 3.0, 6), ("line", 4.8, 0), ("turn", 1.0, 70), ("line", 1.0, 0)])
LTOT = s
HP = LBOARD

def width(l):
    if l <= RINGH:
        return W0
    return W0 + (W1 - W0) * min(1.0, (l - RINGH) / (HP - RINGH))
def depth(l, x):
    ring_d = RA * (1 - math.sqrt(max(0.0, 1 - (min(abs(x), RB * 0.985) / RB) ** 2)))
    w = width(l)
    arch = CTOP * (2 * x / w) ** 2
    if l <= RINGH:
        bl = 1.0
    else:
        t = min(1.0, (l - RINGH) / 4.0)
        bl = 1 - t * t * (3 - 2 * t)
    return bl * ring_d + (1 - bl) * arch
def surf(l, x, off=0.0):
    # find centreline sample by arc length (linear interpolation)
    for k in range(1, len(cl)):
        if cl[k][2] >= l or k == len(cl) - 1:
            (p0, a0, s0), (p1, a1, s1) = cl[k - 1], cl[k]
            t = 0 if s1 == s0 else max(0.0, min(1.0, (l - s0) / (s1 - s0)))
            c = p0.lerp(p1, t); al_ = a0 + (a1 - a0) * t
            break
    n = out_vec(al_)
    return c + X * x + n * (off - depth(l, x)), n, al_

# ---------------------------------------------------------------- gauze board (single double-sided sheet)
NC = 16
ls = [c[2] for c in cl]
grid = []
UVSPAN = 11.0                                # u covers x in [-5.5, 5.5] so the mesh holes stay square
for l in ls:
    w = width(l)
    row = []
    for c in range(NC + 1):
        x = -w / 2 + w * c / NC
        row.append((nv(surf(l, x)[0]), reg(R_PANEL, 0.5 + x / UVSPAN, l / LTOT)))
    grid.append(row)
for r in range(len(ls) - 1):
    for c in range(NC):
        a, b = grid[r][c], grid[r][c + 1]
        d, e = grid[r + 1][c], grid[r + 1][c + 1]
        add_face((a[0], b[0], e[0], d[0]), (a[1], b[1], e[1], d[1]))

# ---------------------------------------------------------------- braided cords (opaque)
def tube(path, hints, radius, region, sides=5, closed=False):
    keep = [0] + [i for i in range(1, len(path)) if (path[i] - path[i - 1]).length > 1e-3]
    if len(keep) < len(path):
        print("STAT tube dropped", len(path) - len(keep), "duplicate points near", [round(c, 1) for c in path[-1]])
    path = [path[i] for i in keep]; hints = [hints[i] for i in keep]
    rings = []
    npt = len(path)
    for i, q in enumerate(path):
        if closed:
            t = (path[(i + 1) % npt] - path[i - 1]).normalized()
        else:
            t = (path[min(i + 1, npt - 1)] - path[max(i - 1, 0)]).normalized()
        n1 = hints[i] - t * hints[i].dot(t); n1.normalize()
        n2 = t.cross(n1)
        rings.append([nv(q + (n1 * math.cos(2 * math.pi * k / sides) + n2 * math.sin(2 * math.pi * k / sides)) * radius) for k in range(sides)])
    seglen = 0.0
    lens = [0.0]
    for i in range(1, npt):
        seglen += (path[i] - path[i - 1]).length; lens.append(seglen)
    if closed:
        seglen += (path[0] - path[-1]).length; lens.append(seglen)
    rep = max(1.0, round(seglen / 6.0))      # texture repeats every ~6 units along the cord
    cnt = npt if closed else npt - 1
    for i in range(cnt):
        j = (i + 1) % npt
        f0, f1 = lens[i] / seglen * rep, lens[i + 1] / seglen * rep
        for k in range(sides):
            k2 = (k + 1) % sides
            # u along the cord (wrapped by repeating via fractional region mapping is not possible -> stretch over region)
            add_face((rings[i][k], rings[i][k2], rings[j][k2], rings[j][k]),
                     (reg(region, f0 / rep, k / sides), reg(region, f0 / rep, (k + 1) / sides),
                      reg(region, f1 / rep, (k + 1) / sides), reg(region, f1 / rep, k / sides)))
CR = 0.2
for sx in (-1, 1):
    path, hints = [], []
    for l in ls:
        w = width(l)
        q, n, _ = surf(l, sx * w / 2)
        path.append(q + X * sx * 0.05); hints.append(n)
    tube(path, hints, CR, R_TRIM)
# fold end edge + board bottom edge
for l in (LTOT, 0.0):
    w = width(l)
    path, hints = [], []
    for c in range(NC + 1):
        q, n, _ = surf(l, -w / 2 + w * c / NC)
        path.append(q); hints.append(n)
    tube(path, hints, CR, R_TRIM)
# ring top rim
path = [L(*ring_xy(i, RT / 2), RTOP) for i in range(NR)]
tube(path, [U] * NR, CR * 0.9, R_TRIM, closed=True)

# ---------------------------------------------------------------- filigree plaque (curved card following the board) + boss
OX, OL0, OL1 = 2.95, 0.15, 7.1
ONC, ONR = 10, 12
og = []
for r in range(ONR + 1):
    l = OL0 + (OL1 - OL0) * r / ONR
    row = []
    for c in range(ONC + 1):
        x = -OX + 2 * OX * c / ONC
        row.append(nv(surf(l, x, 0.22)[0]))
    og.append(row)
for r in range(ONR):
    for c in range(ONC):
        add_face((og[r][c], og[r][c + 1], og[r + 1][c + 1], og[r + 1][c]),
                 (reg(R_ORN, c / ONC, r / ONR), reg(R_ORN, (c + 1) / ONC, r / ONR),
                  reg(R_ORN, (c + 1) / ONC, (r + 1) / ONR), reg(R_ORN, c / ONC, (r + 1) / ONR)))
BL = OL0 + (OL1 - OL0) * 0.42               # boss sits on the rosette at 42% plaque height
bc, bn, _ = surf(BL, 0.0, 0.22)
BX = X; BY = bn.cross(X).normalized()
bring = []
for j, (rad, h) in enumerate(((0.62, 0.0), (0.52, 0.22), (0.3, 0.42))):
    bring.append([nv(bc + bn * h + (BX * math.cos(2 * math.pi * k / 10) + BY * math.sin(2 * math.pi * k / 10)) * rad) for k in range(10)])
btop = nv(bc + bn * 0.5)
for j in range(2):
    for k in range(10):
        k2 = (k + 1) % 10
        add_face((bring[j][k], bring[j][k2], bring[j + 1][k2], bring[j + 1][k]),
                 (reg(R_METAL, k / 10, j / 3), reg(R_METAL, (k + 1) / 10, j / 3), reg(R_METAL, (k + 1) / 10, (j + 1) / 3), reg(R_METAL, k / 10, (j + 1) / 3)))
for k in range(10):
    add_face((bring[2][k], bring[2][(k + 1) % 10], btop), (reg(R_METAL, k / 10, 0.7), reg(R_METAL, (k + 1) / 10, 0.7), reg(R_METAL, 0.5, 1.0)))

# ---------------------------------------------------------------- hairpin (簪): point at -X, ornamental head at +X
PF, PU = 0.3, 2.0
pin_path, pin_r = [], []
for k in range(13):
    x = -8.2 + (15.2 * k / 12)
    pin_path.append(L(x, PF, PU))
    t = k / 12
    pin_r.append(0.03 + 0.19 * min(1.0, t / 0.35))
rings = []
for q, r in zip(pin_path, pin_r):
    rings.append([nv(q + (U * math.cos(2 * math.pi * k / 6) + F * math.sin(2 * math.pi * k / 6)) * r) for k in range(6)])
tip = nv(L(-8.6, PF, PU))
pu = lambda i: 0.03 + i / 12 * 0.67
for i in range(len(rings) - 1):
    for k in range(6):
        k2 = (k + 1) % 6
        add_face((rings[i][k], rings[i + 1][k], rings[i + 1][k2], rings[i][k2]),
                 (reg(R_PIN, pu(i), k / 6), reg(R_PIN, pu(i + 1), k / 6), reg(R_PIN, pu(i + 1), (k + 1) / 6), reg(R_PIN, pu(i), (k + 1) / 6)))
for k in range(6):
    add_face((rings[0][(k + 1) % 6], tip, rings[0][k]), (reg(R_PIN, 0.03, (k + 1) / 6), reg(R_PIN, 0, (k + 0.5) / 6), reg(R_PIN, 0.03, k / 6)))
# head: collar + flat cloud-leaf (thin along F, broad in X-U)
hc = L(7.95, PF, PU + 0.15)
LEAF = [(-0.95, 0.0), (-0.55, 0.45), (-0.1, 0.62), (0.25, 0.85), (0.65, 0.7), (0.95, 0.3), (0.9, -0.15), (0.55, -0.45), (0.1, -0.5), (-0.45, -0.3)]
front = [nv(hc + X * lx + U * lu - F * 0.17) for lx, lu in LEAF]
back = [nv(hc + X * lx + U * lu + F * 0.17) for lx, lu in LEAF]
cf, cb = nv(hc - F * 0.3), nv(hc + F * 0.3)
nl = len(LEAF)
for k in range(nl):
    k2 = (k + 1) % nl
    uu = lambda lx, lu: reg(R_PIN, 0.75 + 0.24 * (lx + 1) / 2, 0.05 + 0.9 * (lu + 0.6) / 1.5)
    add_face((front[k2], front[k], cf), (uu(*LEAF[k2]), uu(*LEAF[k]), uu(0, 0.1)))
    add_face((back[k], back[k2], cb), (uu(*LEAF[k]), uu(*LEAF[k2]), uu(0, 0.1)))
    add_face((front[k], front[k2], back[k2], back[k]),
             (reg(R_PIN, 0.03 + 0.67 * k / nl, 0.9), reg(R_PIN, 0.03 + 0.67 * (k + 1) / nl, 0.9),
              reg(R_PIN, 0.03 + 0.67 * (k + 1) / nl, 0.99), reg(R_PIN, 0.03 + 0.67 * k / nl, 0.99)))

# ---------------------------------------------------------------- build object + weights
def build(name, part):
    Vv, Ff, UU = part
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in Vv], [], Ff)
    me.update()
    for ln in ("map1",):
        uv = me.uv_layers.new(name=ln)
        for poly, uvs in zip(me.polygons, UU):
            for k, l in enumerate(poly.loop_indices):
                uv.data[l].uv = uvs[k]
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob

def transfer_weights(dst, src):
    bvh, svs, stris = bvh_of(src)
    sgroups = {g.index: g.name for g in src.vertex_groups}
    sw = [{sgroups[g.group]: g.weight for g in v.groups if g.weight > 0} for v in src.data.vertices]
    for bone in rig.data.bones:
        if bone.name not in dst.vertex_groups:
            dst.vertex_groups.new(name=bone.name)
    for v in dst.data.vertices:
        p = dst.matrix_world @ v.co
        loc, nrm, idx, dist = bvh.find_nearest(p)
        t = stris[idx]
        a, b, c = (svs[i] for i in t)
        v0, v1, v2 = b - a, c - a, loc - a
        d00, d01, d11 = v0.dot(v0), v0.dot(v1), v1.dot(v1)
        d20, d21 = v2.dot(v0), v2.dot(v1)
        den = d00 * d11 - d01 * d01 or 1e-9
        wb = (d11 * d20 - d01 * d21) / den
        wc = (d00 * d21 - d01 * d20) / den
        wa = 1 - wb - wc
        acc = {}
        for w, vi in ((wa, t[0]), (wb, t[1]), (wc, t[2])):
            w = max(0.0, w)
            for g, gw in sw[vi].items():
                acc[g] = acc.get(g, 0) + w * gw
        top4 = sorted(acc.items(), key=lambda kv: -kv[1])[:4]
        tot = sum(w for _, w in top4) or 1
        for g, w in top4:
            if w / tot > 1e-4:
                dst.vertex_groups[g].add([v.index], w / tot, 'REPLACE')

hat = build(NAME, parts["hat"])
me = hat.data
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='BEAUTY')
bm.to_mesh(me); bm.free()
transfer_weights(hat, jx)
me.shade_smooth()
me.set_sharp_from_angle(angle=math.radians(45))
me.name = NAME + "Shape"
hat.name = NAME

mat = bpy.data.materials.new("PDXmat_" + NAME + "Shape")
mat["shader"] = "portrait_attachment_alpha_to_coverage"
mat.use_nodes = True
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
def teximg(slot):
    n = nt.nodes.new('ShaderNodeTexImage')
    img = bpy.data.images.new(f"{NAME}_{slot}", 4, 4)
    img.source = 'FILE'
    img.filepath = os.path.join(OUT, f"{NAME}_{slot}.dds")
    n.image = img
    return n
nt.links.new(teximg("black_diffuse").outputs["Color"], bsdf.inputs["Base Color"])
sep = nt.nodes.new('ShaderNodeSeparateColor')
nt.links.new(teximg("properties").outputs["Color"], sep.inputs["Color"])
nt.links.new(sep.outputs["Red"], bsdf.inputs["Roughness"])
nm = nt.nodes.new('ShaderNodeNormalMap')
nt.links.new(teximg("normal").outputs["Color"], nm.inputs["Color"])
nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
me.materials.clear(); me.materials.append(mat)
mod = hat.modifiers.new("skin", 'ARMATURE'); mod.object = rig

for o in list(bpy.data.objects):
    if o not in (hat, rig):
        bpy.data.objects.remove(o, do_unlink=True)

me.calc_loop_triangles()
print("STAT tris", len(me.loop_triangles), "verts", len(me.vertices),
      "bbox", [round(min(getattr(v.co, a) for v in me.vertices), 2) for a in "xyz"],
      [round(max(getattr(v.co, a) for v in me.vertices), 2) for a in "xyz"])
print("STAT U0", round(U0, 2), "RINGH", round(RINGH, 2), "HP", round(HP, 2), "LTOT", round(LTOT, 2))
import json
json.dump({"RINGH": RINGH, "LTOT": LTOT}, open(os.path.join(OUT, "zibu_params.json"), "w"))
print("STAT unweighted", sum(1 for v in me.vertices if not v.groups), "max_infl", max(len(v.groups) for v in me.vertices))
uv = me.uv_layers["map1"]
print("STAT zero_area_uv_tris", sum(1 for t in me.loop_triangles if abs((uv.data[t.loops[1]].uv - uv.data[t.loops[0]].uv).cross(uv.data[t.loops[2]].uv - uv.data[t.loops[0]].uv)) < 1e-9))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, NAME + ".blend"))
pdx.export_meshfile(os.path.join(OUT, NAME + ".mesh"), exp_mesh=True, exp_skel=True, exp_locs=False)
print("EXPORTED")
