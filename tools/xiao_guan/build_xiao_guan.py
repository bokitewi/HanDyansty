# Build the low-poly 孝帽 (m_headgear_hd_huaxia_xiao_guan) in Blender 4.2 and export a PDX .mesh.
# Usage: blender -b --factory-startup --python build_xiao_guan.py -- <jinxian.mesh> <male_head.mesh> <out_dir>
import bpy, bmesh, sys, os, math, importlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

pdx = importlib.import_module("bl_ext.user_default.io_pdx_mesh.pdx_blender.blender_import_export")
JX, HEAD, OUT = sys.argv[sys.argv.index("--") + 1:][:3]
NAME = "m_headgear_hd_huaxia_xiao_guan"
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)

def import_new(path, skel):
    before = set(bpy.data.objects)
    pdx.import_meshfile(path, imp_mesh=True, imp_skel=skel, imp_locs=False)
    return [o for o in bpy.data.objects if o not in before]

jx_objs = import_new(JX, True)
rig = next(o for o in jx_objs if o.type == 'ARMATURE')
jx = next(o for o in jx_objs if o.type == 'MESH')
head_objs = import_new(HEAD, True)
head = next(o for o in head_objs if o.type == 'MESH')

def bvh_of(obj):
    me = obj.data
    me.calc_loop_triangles()
    vs = [obj.matrix_world @ v.co for v in me.vertices]
    tris = [tuple(t.vertices) for t in me.loop_triangles]
    return BVHTree.FromPolygons(vs, tris), vs, tris

head_bvh, head_vs, head_tris = bvh_of(head)

# ---------------------------------------------------------------- dimensions
CY = 0.35                     # band centre (y), -Y is the face side
RX, RY = 10.0, 11.75          # band outer half axes (matches 进贤冠 band)
THK = 0.55                    # band thickness
BH = 4.0                      # band height
def zb(y):                    # band bottom plane: front 52.5, back 50.6 (same as 进贤冠)
    return 51.57 - 0.082 * y

# UV atlas regions (u0, v0, u1, v1)
R_SHELL = (0.01, 0.01, 0.61, 0.99)
R_BAND = (0.64, 0.82, 0.98, 0.98)
R_PLAIN = (0.64, 0.56, 0.98, 0.78)
R_CAP = (0.64, 0.04, 0.98, 0.50)

def reg(r, fu, fv):
    return (r[0] + (r[2] - r[0]) * fu, r[1] + (r[3] - r[1]) * fv)

parts = {}   # name -> (verts, faces, uvs-per-face)
def new_part(name):
    parts[name] = ([], [], [])
    return parts[name]

def add_face(part, idx, uvs):
    part[1].append(tuple(idx))
    part[2].append(tuple(uvs))

# ---------------------------------------------------------------- band (颜题)
N = 32
P = new_part("hat")
V, F, U = P
ring = []
for i in range(N):
    a = 2 * math.pi * i / N
    c, s = math.cos(a), math.sin(a)
    yo = CY + RY * s
    yi = CY + (RY - THK) * s
    z0 = zb(yo)
    ob = len(V); V.append(Vector((RX * c, yo, z0)))
    ot = len(V); V.append(Vector((RX * c, yo, z0 + BH)))
    it = len(V); V.append(Vector(((RX - THK) * c, yi, z0 + BH)))
    ib = len(V); V.append(Vector(((RX - THK) * c, yi, z0)))
    ring.append((ob, ot, it, ib))
for i in range(N):
    a, b = ring[i], ring[(i + 1) % N]
    f0, f1 = i / N, (i + 1) / N
    # outer wall
    add_face(P, (a[0], b[0], b[1], a[1]), (reg(R_BAND, f0, 0), reg(R_BAND, f1, 0), reg(R_BAND, f1, 1), reg(R_BAND, f0, 1)))
    # top, inner, bottom -> plain linen strips
    add_face(P, (a[1], b[1], b[2], a[2]), (reg(R_PLAIN, f0, 0.70), reg(R_PLAIN, f1, 0.70), reg(R_PLAIN, f1, 1.0), reg(R_PLAIN, f0, 1.0)))
    add_face(P, (a[2], b[2], b[3], a[3]), (reg(R_PLAIN, f0, 0.35), reg(R_PLAIN, f1, 0.35), reg(R_PLAIN, f1, 0.65), reg(R_PLAIN, f0, 0.65)))
    add_face(P, (a[3], b[3], b[0], a[0]), (reg(R_PLAIN, f0, 0.0), reg(R_PLAIN, f1, 0.0), reg(R_PLAIN, f1, 0.30), reg(R_PLAIN, f0, 0.30)))

# ---------------------------------------------------------------- shell (冠身/展筩)
# centre profile from back base to front base: tall at the back, sloping down to the forehead
RXS, RYS = RX - THK / 2, RY - THK / 2      # shell sits on the band's mid-line
CTRL = [(CY + RYS, None), (11.6, 61.0), (10.6, 68.0), (8.6, 74.0), (6.0, 77.3), (3.2, 77.2),
        (0.0, 75.0), (-3.5, 71.0), (-7.0, 65.5), (-9.6, 60.0), (-10.9, 57.2), (CY - RYS, None)]
def base_z(y):
    return zb(y) + BH - 0.35
CTRL = [(y, base_z(y) if z is None else z) for y, z in CTRL]

def catmull(pts, n):
    # sample a Catmull-Rom spline through pts, then resample to n+1 points by arc length
    ext = [pts[0] + (pts[0] - pts[1])] + pts + [pts[-1] + (pts[-1] - pts[-2])]
    dense = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for k in range(20):
            t = k / 20
            dense.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    dense.append(pts[-1])
    L = [0.0]
    for i in range(1, len(dense)):
        L.append(L[-1] + (dense[i] - dense[i - 1]).length)
    out, j = [], 0
    for k in range(n + 1):
        target = L[-1] * k / n
        while j < len(L) - 2 and L[j + 1] < target:
            j += 1
        seg = L[j + 1] - L[j]
        t = 0 if seg == 0 else (target - L[j]) / seg
        out.append(dense[j].lerp(dense[j + 1], t))
    return out

NS = 18                     # rows along the profile
NC = 12                     # columns across the width (ribs every 2 columns -> 7 ribs)
W = 8.5                     # shell half width
prof = catmull([Vector(p) for p in CTRL], NS)       # (y, z) centre profile
ry0 = RYS
grid = []
for c in range(NC + 1):
    x = -W + 2 * W * c / NC
    ryx = RYS * math.sqrt(max(0.0, 1 - (x / RXS) ** 2))
    hx = 1 - 0.18 * (abs(x) / W) ** 4
    col = []
    for r, p in enumerate(prof):
        yn = (p.x - CY) / ry0
        y = CY + yn * ryx
        zc_base = base_z(p.x)
        z = base_z(y) + (p.y - zc_base) * hx
        col.append(len(V)); V.append(Vector((x, y, z)))
    grid.append(col)
for c in range(NC):
    for r in range(NS):
        a, b = grid[c][r], grid[c + 1][r]
        d, e = grid[c][r + 1], grid[c + 1][r + 1]
        add_face(P, (a, b, e, d), (reg(R_SHELL, c / NC, r / NS), reg(R_SHELL, (c + 1) / NC, r / NS),
                                   reg(R_SHELL, (c + 1) / NC, (r + 1) / NS), reg(R_SHELL, c / NC, (r + 1) / NS)))

# rolled side rims along the two free edges (triangular tubes)
def tube(part, path, radius, region, sides=3, up_hint=Vector((1, 0, 0))):
    V, F, U = part
    rings = []
    for i, p in enumerate(path):
        t = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        n1 = up_hint - t * up_hint.dot(t)
        n1.normalize()
        n2 = t.cross(n1)
        rr = []
        for k in range(sides):
            a = 2 * math.pi * k / sides
            rr.append(len(V)); V.append(p + (n1 * math.cos(a) + n2 * math.sin(a)) * radius)
        rings.append(rr)
    for i in range(len(path) - 1):
        for k in range(sides):
            k2 = (k + 1) % sides
            f0, f1 = i / (len(path) - 1), (i + 1) / (len(path) - 1)
            add_face(part, (rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]),
                     (reg(region, k / sides, f0), reg(region, (k + 1) / sides, f0),
                      reg(region, (k + 1) / sides, f1), reg(region, k / sides, f1)))
for c, hint in ((0, Vector((-1, 0, 0))), (NC, Vector((1, 0, 0)))):
    tube(P, [V[i] for i in grid[c]], 0.32, R_PLAIN, 3, hint)

# ---------------------------------------------------------------- inner black cap (内帻) covering the topknot
NR, NA = 5, 16
cap_rings = []
for j in range(NR):
    phi = (j / NR) * (math.pi / 2)
    sc = math.cos(phi)
    rr = []
    for i in range(NA):
        a = 2 * math.pi * i / NA
        rx_, ry_ = (RX - THK - 0.25) * sc, (RY - THK - 0.25) * sc
        cyj = CY + 2.5 * (1 - sc)               # top drifts toward the back (发髻在后上)
        y = cyj + ry_ * math.sin(a)
        z = zb(CY + (RY - THK) * math.sin(a)) + 0.6 + 10.5 * math.sin(phi)
        rr.append(len(V)); V.append(Vector((rx_ * math.cos(a), y, z)))
    cap_rings.append(rr)
top = len(V); V.append(Vector((0, CY + 2.5, zb(CY) + 0.6 + 11.2)))
for j in range(NR - 1):
    for i in range(NA):
        i2 = (i + 1) % NA
        add_face(P, (cap_rings[j][i], cap_rings[j][i2], cap_rings[j + 1][i2], cap_rings[j + 1][i]),
                 (reg(R_CAP, i / NA, j / NR), reg(R_CAP, (i + 1) / NA, j / NR),
                  reg(R_CAP, (i + 1) / NA, (j + 1) / NR), reg(R_CAP, i / NA, (j + 1) / NR)))
for i in range(NA):
    i2 = (i + 1) % NA
    add_face(P, (cap_rings[-1][i], cap_rings[-1][i2], top),
             (reg(R_CAP, i / NA, (NR - 1) / NR), reg(R_CAP, (i + 1) / NA, (NR - 1) / NR), reg(R_CAP, (i + 0.5) / NA, 1.0)))

# ---------------------------------------------------------------- strips helper
def strip(part, path, normals, width, region):
    V, F, U = part
    pairs = []
    for i, p in enumerate(path):
        t = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        side = t.cross(normals[i]).normalized() * (width / 2)
        a = len(V); V.append(p - side)
        b = len(V); V.append(p + side)
        pairs.append((a, b))
    for i in range(len(path) - 1):
        f0, f1 = i / (len(path) - 1), (i + 1) / (len(path) - 1)
        a, b = pairs[i]; c, d = pairs[i + 1]
        add_face(part, (a, b, d, c), (reg(region, 0, f0), reg(region, 1, f0), reg(region, 1, f1), reg(region, 0, f1)))

def push_out(p, clearance):
    loc, nrm, idx, dist = head_bvh.find_nearest(p)
    if loc is None:
        return p, Vector((0, 0, 1))
    tri = head_tris[idx]
    n = (head_vs[tri[1]] - head_vs[tri[0]]).cross(head_vs[tri[2]] - head_vs[tri[0]]).normalized()
    if (p - loc).dot(n) < 0:
        n = -n if (loc - Vector((0, 0, 44))).dot(n) < 0 else n
    return loc + n * clearance, n

# back ribbons (后垂白带): hang from the back of the band, kept clear of the nape
for sx in (-1, 1):
    path, nrms = [], []
    x0 = sx * 1.7
    for j in range(8):
        z = zb(CY + RY) - 0.2 - j * 1.8
        x = x0 + sx * 0.18 * j
        hit = head_bvh.ray_cast(Vector((x, 40.0, z)), Vector((0, -1, 0)))
        ysurf = hit[0].y if hit[0] is not None else 8.0
        y = max(ysurf + 1.3, CY + RY - 0.15 - 0.55 * j) if j else CY + RY + 0.05
        path.append(Vector((x, y, z))); nrms.append(Vector((0, 1, 0.15)).normalized())
    strip(P, path, nrms, 2.0, R_PLAIN)

# ---------------------------------------------------------------- chin straps (白冠缨), skinned from the head
S = new_part("strap")
rough = [(9.75, -2.1, None), (8.6, -2.6, 48.0), (8.2, -3.2, 44.0), (7.6, -4.2, 40.0), (6.6, -5.6, 36.0),
         (5.0, -7.2, 32.5), (3.0, -8.6, 29.5), (1.2, -9.2, 28.2)]
chin_pts = []
for sx in (-1, 1):
    path, nrms = [], []
    for k, (x, y, z) in enumerate(rough):
        if z is None:
            p = Vector((sx * x, y, zb(y) + 0.3)); n = Vector((sx, 0, 0))
        else:
            p, n = push_out(Vector((sx * x, y, z)), 0.35)
        path.append(p); nrms.append(n)
    chin_pts.append(path[-1])
    strip(S, path, nrms, 0.55, R_PLAIN)
# knot under the chin + two short tails
kc = (chin_pts[0] + chin_pts[1]) / 2
kc, kn = push_out(kc, 0.55)
Vs, Fs, Us = S
oct_ = [kc + Vector(d) * 0.6 for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]
base = len(Vs); Vs.extend(oct_)
for a, b, c in ((0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)):
    add_face(S, (base + a, base + b, base + c), (reg(R_PLAIN, 0.1, 0.1), reg(R_PLAIN, 0.3, 0.1), reg(R_PLAIN, 0.2, 0.3)))
for sx in (-1, 1):
    path = [kc + Vector((sx * 0.3 * j, -0.35 * j, -1.2 * j)) for j in range(4)]
    strip(S, path, [Vector((0, -1, 0))] * 4, 0.5, R_PLAIN)

# ---------------------------------------------------------------- build objects + manual weight transfer
def build(name, part):
    V, F, U = part
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in V], [], F)
    me.update()
    for ln in ("map1", "map2"):
        uv = me.uv_layers.new(name=ln)
        li = 0
        for poly, uvs in zip(me.polygons, U):
            for k, l in enumerate(poly.loop_indices):
                uv.data[l].uv = uvs[k]
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob

def transfer_weights(dst, src, exclude=(), fallback=None):
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
        # barycentric coordinates of loc in triangle abc
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
        acc = {g: w for g, w in acc.items() if not g.startswith(exclude)} if exclude else acc
        if fallback and sum(acc.values()) < 1e-4:
            acc = {fallback: 1.0}
        top4 = sorted(acc.items(), key=lambda kv: -kv[1])[:4]
        tot = sum(w for _, w in top4) or 1
        for g, w in top4:
            if w / tot > 1e-4:
                dst.vertex_groups[g].add([v.index], w / tot, 'REPLACE')

hat = build(NAME, parts["hat"])
strap = build(NAME + "_strap", parts["strap"])
transfer_weights(hat, jx)
transfer_weights(strap, head, exclude=("bn_h_neck", "bn_h_l_clavicle", "head_root"), fallback="bn_h_jaw_low")

# join strap into hat
bpy.ops.object.select_all(action='DESELECT')
hat.select_set(True); strap.select_set(True)
bpy.context.view_layer.objects.active = hat
bpy.ops.object.join()

me = hat.data
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='BEAUTY')
bm.to_mesh(me); bm.free()
me.shade_smooth()
me.set_sharp_from_angle(angle=math.radians(50))
me.name = NAME + "Shape"
hat.name = NAME

# material: reuse the 进贤冠 PDX material node layout, retarget textures
mat = bpy.data.materials.new("PDXmat_" + NAME + "Shape")
mat["shader"] = "portrait_attachment"
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
nt.links.new(teximg("diffuse").outputs["Color"], bsdf.inputs["Base Color"])
sep = nt.nodes.new('ShaderNodeSeparateColor')
nt.links.new(teximg("properties").outputs["Color"], sep.inputs["Color"])
nt.links.new(sep.outputs["Red"], bsdf.inputs["Roughness"])
nm = nt.nodes.new('ShaderNodeNormalMap')
nt.links.new(teximg("normal").outputs["Color"], nm.inputs["Color"])
nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
me.materials.clear(); me.materials.append(mat)

mod = hat.modifiers.new("skin", 'ARMATURE'); mod.object = rig
hat.parent = None

# remove reference objects
for o in list(bpy.data.objects):
    if o not in (hat, rig):
        bpy.data.objects.remove(o, do_unlink=True)

# stats
me.calc_loop_triangles()
zs = [v.co.z for v in me.vertices]
print("STAT tris", len(me.loop_triangles), "verts", len(me.vertices),
      "bbox", [round(min(getattr(v.co, a) for v in me.vertices), 2) for a in "xyz"],
      [round(max(getattr(v.co, a) for v in me.vertices), 2) for a in "xyz"])
unweighted = sum(1 for v in me.vertices if not v.groups)
print("STAT unweighted", unweighted, "max_infl", max(len(v.groups) for v in me.vertices))
# zero-area UV check
uv = me.uv_layers["map1"]
bad = 0
for t in me.loop_triangles:
    a, b, c = (uv.data[l].uv for l in t.loops)
    if abs((b - a).cross(c - a)) < 1e-7:
        bad += 1
print("STAT zero_area_uv_tris", bad)
# head clearance of cap / band inner
inside = 0
for v in me.vertices:
    loc, nrm, idx, dist = head_bvh.find_nearest(v.co) if False else (None, None, None, None)
print("STAT done")

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, NAME + ".blend"))
pdx.export_meshfile(os.path.join(OUT, NAME + ".mesh"), exp_mesh=True, exp_skel=True, exp_locs=False)
print("EXPORTED")
