"""Turn the placed scene (scene_v2.blend) into the three CK3 meshes of the Han-Jin map table.

argv: <tex_report.json> <stage_model_dir> <censer_target_tris> <out_blend>
"""
import sys, os, json, math
import bpy, bmesh, mathutils

argv = sys.argv[sys.argv.index("--") + 1:]
tex_report = json.load(open(argv[0], encoding="utf-8"))
stage = argv[1]
censer_target = int(argv[2])
out_blend = argv[3]

ext_root = os.path.join(os.environ["APPDATA"], "Blender Foundation", "Blender", "4.2", "extensions", "user_default")
sys.path.insert(0, ext_root)
from io_pdx_mesh.pdx_blender import blender_import_export as bie

patches = tex_report["black_patches"]
TOP_BLACK = patches["table_top_centre_0.4_0.6"]
PLATE_BLACK = patches["plate_top"]
EARS_BLACK = patches["cup_ears"]

def suffix(o):
    return "-" + "-".join(o.name.split("-")[-2:])

def by_suffix(s):
    return next(o for o in bpy.data.objects if o.type == 'MESH' and suffix(o) == s)

def slot_key(o, idx):
    m = o.data.materials[idx] if idx < len(o.data.materials) else None
    return m.get("src_tex") if m else None

def new_obj_from_faces(src, face_pred, name):
    """Copy src into a new object holding only faces where face_pred(poly) is True."""
    me = src.data.copy()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    keep_flags = [face_pred(p) for p in src.data.polygons]
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f, k in zip(bm.faces, keep_flags) if not k], context='FACES')
    bm.to_mesh(me)
    bm.free()
    return ob

def remap_faces_into(ob, face_pred, patch):
    """Squeeze the UVs of selected faces into a black patch, keeping non-zero area."""
    me = ob.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uv = me.uv_layers.active.data
    u0, u1 = patch["u"]; v0, v1 = patch["v"]
    # inset 15% so bilinear/mip footprints stay inside the dark area
    du, dv = (u1 - u0) * 0.15, (v1 - v0) * 0.15
    u0, u1, v0, v1 = u0 + du, u1 - du, v0 + dv, v1 - dv
    sel = [p for p in me.polygons if face_pred(p)]
    for p in sel:
        n = p.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        a, b = [i for i in range(3) if i != ax]
        cs = [me.vertices[me.loops[li].vertex_index].co for li in p.loop_indices]
        amin, amax = min(c[a] for c in cs), max(c[a] for c in cs)
        bmin, bmax = min(c[b] for c in cs), max(c[b] for c in cs)
        sa, sb = max(amax - amin, 1e-6), max(bmax - bmin, 1e-6)
        for li, c in zip(p.loop_indices, cs):
            uv[li].uv = (u0 + (c[a] - amin) / sa * (u1 - u0), v0 + (c[b] - bmin) / sb * (v1 - v0))
    return len(sel)

def join(objs, name):
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    ob.data.name = name
    return ob

def ensure_uv_name(ob):
    # the exporter takes UV sets in order; keep exactly one named UVMap
    me = ob.data
    while len(me.uv_layers) > 1:
        me.uv_layers.remove(me.uv_layers[-1])
    me.uv_layers[0].name = "UVMap"

def triangulate(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
    bmesh.ops.dissolve_degenerate(bm, dist=1e-4, edges=bm.edges[:])
    bm.to_mesh(ob.data)
    bm.free()

def fix_zero_uv(ob, size=0.004):
    """Faces whose UVs collapse to a line (planar-projected walls) get a tiny local unwrap
    around their own UV centroid, so the colour stays the same but tangents stay valid."""
    me = ob.data
    uv = me.uv_layers.active.data
    fixed = 0
    for p in me.polygons:
        ls = list(p.loop_indices)
        a, b, c = (uv[l].uv.copy() for l in ls[:3])
        if abs((b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)) / 2 > 1e-9:
            continue
        cu = sum(uv[l].uv.x for l in ls) / len(ls)
        cv = sum(uv[l].uv.y for l in ls) / len(ls)
        ax = max(range(3), key=lambda i: abs(p.normal[i]))
        i, j = [k for k in range(3) if k != ax]
        cs = [me.vertices[me.loops[l].vertex_index].co for l in ls]
        ai, aj = min(q[i] for q in cs), min(q[j] for q in cs)
        si = max(max(q[i] for q in cs) - ai, 1e-6)
        sj = max(max(q[j] for q in cs) - aj, 1e-6)
        s = max(si, sj)
        for l, q in zip(ls, cs):
            uv[l].uv = (cu + ((q[i] - ai) / s - 0.5) * size, cv + ((q[j] - aj) / s - 0.5) * size)
        fixed += 1
    return fixed

def set_shading(ob, smooth, angle=40):
    me = ob.data
    if smooth:
        me.shade_smooth()
        me.set_sharp_from_angle(angle=math.radians(angle))
    else:
        me.shade_flat()

def pdx_material(ob, shader, diffuse_file):
    m = bpy.data.materials.new("PDXmat_" + ob.name)
    m["shader"] = shader
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tn = nt.nodes.new("ShaderNodeTexImage")
    img = bpy.data.images.load(os.path.join(stage, diffuse_file), check_existing=True)
    tn.image = img
    nt.links.new(tn.outputs["Color"], bsdf.inputs["Base Color"])
    nt.nodes.active = tn
    m.use_backface_culling = True
    ob.data.materials.clear()
    ob.data.materials.append(m)
    for p in ob.data.polygons:
        p.material_index = 0

# ------------------------------------------------------------------ table
top = by_suffix("-1-36")
legs = [by_suffix("-2-482"), by_suffix("-3-156")]
side_slot = {i for i in range(len(top.data.materials)) if slot_key(top, i) == "002"}
top_slot = {i for i in range(len(top.data.materials)) if slot_key(top, i) == "005"}
sides = new_obj_from_faces(top, lambda p: p.material_index in side_slot, "hd_han_table_side")
tabletop = new_obj_from_faces(top, lambda p: p.material_index not in side_slot, "hd_han_table_top_part")
n_bottom = remap_faces_into(tabletop, lambda p: p.material_index not in top_slot, TOP_BLACK)
for lg in legs:
    lg.data.uv_layers.new(name="UVMap") if not lg.data.uv_layers else None
    remap_faces_into(lg, lambda p: True, TOP_BLACK)
bpy.data.objects.remove(top, do_unlink=True)
table = join([tabletop] + legs, "hd_han_table_top")
sides.name = sides.data.name = "hd_han_table_side"
print("TABLE bottom faces remapped", n_bottom)

# ------------------------------------------------------------------ plate
plate_body = by_suffix("-5-668")
p_tex = {i for i in range(len(plate_body.data.materials)) if slot_key(plate_body, i) == "007"}
n = remap_faces_into(plate_body, lambda p: p.material_index not in p_tex, PLATE_BLACK)
plate_body.name = plate_body.data.name = "hd_han_plate_top"
rim = by_suffix("-4-401")
rim.name = rim.data.name = "hd_han_plate_rim"
print("PLATE black faces remapped", n)

# ------------------------------------------------------------------ cup
cup = by_suffix("-9-590")
cup.name = cup.data.name = "hd_han_cup"
ears = by_suffix("-10-117")
e_tex = {i for i in range(len(ears.data.materials)) if slot_key(ears, i) == "008"}
n = remap_faces_into(ears, lambda p: p.material_index not in e_tex, EARS_BLACK)
ears.name = ears.data.name = "hd_han_cup_ears"
print("EARS black faces remapped", n)

# ------------------------------------------------------------------ censer (博山炉)
cens = join([by_suffix("-13-808"), by_suffix("-14-855")], "hd_han_censer")
src_tris = sum(len(p.vertices) - 2 for p in cens.data.polygons)
ratio = min(1.0, censer_target / src_tris)
mod = cens.modifiers.new("dec", 'DECIMATE')
mod.decimate_type = 'COLLAPSE'
mod.ratio = ratio
mod.use_collapse_triangulate = True
bpy.context.view_layer.objects.active = cens
bpy.ops.object.modifier_apply(modifier=mod.name)
print("CENSER", src_tris, "->", sum(len(p.vertices) - 2 for p in cens.data.polygons), "ratio", round(ratio, 4))

# ------------------------------------------------------------------ sword
sword_objs = [o for o in bpy.data.objects if o.type == 'MESH' and o.get("group") == "sword"]
sword = join(sword_objs, "hd_han_sword")

# ------------------------------------------------------------------ floor
z_floor = min((table.matrix_world @ v.co).z for v in table.data.vertices)
me = bpy.data.meshes.new("hd_han_floor")
H = 30000.0
me.from_pydata([(-H, -H, z_floor), (H, -H, z_floor), (H, H, z_floor), (-H, H, z_floor)], [], [(0, 1, 2, 3)])
uvl = me.uv_layers.new(name="UVMap")
for li, uvc in zip(range(4), [(0, 0), (1, 0), (1, 1), (0, 1)]):
    uvl.data[li].uv = uvc
floor = bpy.data.objects.new("hd_han_floor", me)
bpy.context.scene.collection.objects.link(floor)
print("FLOOR z", round(z_floor, 2))

# ------------------------------------------------------------------ finalize
SPEC = {
    "hd_han_table_top":  ("standard_map_decoration", "hd_han_table_top_diffuse.dds", False, "table"),
    "hd_han_table_side": ("standard_map_decoration", "hd_han_table_side_diffuse.dds", False, "table"),
    "hd_han_plate_top":  ("tabletop_standard", "hd_han_plate_top_diffuse.dds", True, "table"),
    "hd_han_plate_rim":  ("tabletop_standard", "hd_han_plate_rim_diffuse.dds", True, "table"),
    "hd_han_cup":        ("tabletop_standard", "hd_han_cup_diffuse.dds", True, "table"),
    "hd_han_cup_ears":   ("tabletop_standard", "hd_han_cup_ears_diffuse.dds", True, "table"),
    "hd_han_censer":     ("tabletop_standard", "hd_han_censer_diffuse.dds", True, "table"),
    "hd_han_sword":      ("standard", "hd_han_sword_diffuse.dds", None, "sword"),
    "hd_han_floor":      ("map_floor", "hd_han_floor_diffuse.dds", False, "floor"),
}
for o in list(bpy.data.objects):
    if o.type != 'MESH' or o.name not in SPEC:
        bpy.data.objects.remove(o, do_unlink=True)
for name, (shader, diff, smooth, target) in SPEC.items():
    o = bpy.data.objects[name]
    o.data.name = name
    o.parent = None
    if o.matrix_world != mathutils.Matrix.Identity(4):
        o.data.transform(o.matrix_world)
        o.matrix_world = mathutils.Matrix.Identity(4)
    o.modifiers.clear()
    ensure_uv_name(o)
    triangulate(o)
    nfix = fix_zero_uv(o)
    if nfix:
        print("ZERO_UV_FIXED", name, nfix)
    if smooth is not None:          # keep the sword's authored normals
        set_shading(o, smooth)
    pdx_material(o, shader, diff)
    o["export_target"] = target
    tris = len(o.data.polygons)
    print("SHAPE", name, "tris", tris, "verts", len(o.data.vertices), "target", target)

bpy.ops.wm.save_as_mainfile(filepath=out_blend)

# ------------------------------------------------------------------ export
outputs = {"table": "hd_han_tabletop.mesh", "sword": "hd_han_tabletop_sword.mesh", "floor": "hd_han_tabletop_floor.mesh"}
for target, fname in outputs.items():
    for o in bpy.context.scene.objects:
        o.select_set(o.get("export_target") == target)
    bie.export_meshfile(os.path.join(stage, fname), exp_mesh=True, exp_skel=False, exp_locs=False, exp_selected=True)
    print("EXPORTED", fname, os.path.getsize(os.path.join(stage, fname)))
print("PROD_DONE")
