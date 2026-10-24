"""Build the Han lacquer map-table scene at CK3 scale from the imported 3d66 source.

Blender axes: X = map east, Y = map north, Z = up (PDX exporter swaps Y/Z).
Local origin = map-table centre; table top surface at TOP_Z.
"""
import sys, os, math, json
import bpy, bmesh, mathutils

argv = sys.argv[sys.argv.index("--") + 1:]
cfg = json.loads(open(argv[0], encoding="utf-8").read())
tex_dir = cfg["tex_dir"]
K = cfg["units_per_cm"]
TOP_Z = cfg["top_z"]
MAP_W, MAP_H = cfg["map_w"], cfg["map_h"]

BLACK = ('rgb', 0.02, 0.015, 0.012)
BRONZE = ('rgb', 0.45, 0.33, 0.12)
MAP = {
    "-1-36": {0: "005", 1: "002", 2: BLACK},
    "-2-482": {"*": BLACK}, "-3-156": {"*": BLACK},
    "-4-401": {"*": "004"},
    "-5-668": {0: "007", "*": BLACK},
    "-9-590": {0: "009", "*": BLACK},     # 耳杯杯身：鱼纹内底
    "-10-117": {0: "008", "*": BLACK},    # 耳杯双耳：新月纹带
    "-11-11": {"*": "006"},
    "-12-284": {"*": "003"},
    "-13-808": {"*": BRONZE}, "-14-855": {"*": BRONZE},
}
GROUPS = {
    "table": ["-1-36", "-2-482", "-3-156"],
    "lian": ["-11-11"],            # 奁
    "plate": ["-4-401", "-5-668"],  # 红漆盘
    "dish": ["-12-284"],            # 金云纹盘
    "cup": ["-9-590", "-10-117"],   # 耳杯
    "censer": ["-13-808", "-14-855"],  # 博山炉
}

def suffix(o):
    return "-" + "-".join(o.name.split("-")[-2:])

def tex(n):
    return os.path.join(tex_dir, f"3d66Model-18349387-files-{n}.{'jpg' if n == '001' else 'png'}")

# 1. freeze world matrices, unparent, drop non-kept objects
keep_suf = {s for g in GROUPS.values() for s in g}
mats_world = {o.name: o.matrix_world.copy() for o in bpy.data.objects}
for o in list(bpy.data.objects):
    if o.type != 'MESH' or suffix(o) not in keep_suf:
        bpy.data.objects.remove(o, do_unlink=True)
for o in bpy.data.objects:
    mw = mats_world[o.name]
    o.parent = None
    o.data.transform(mw)          # bake world matrix exactly once
    o.matrix_world = mathutils.Matrix.Identity(4)
    if mw.determinant() < 0:
        o.data.flip_normals()

# 2. materials
cache = {}
def make_mat(spec):
    key = str(spec)
    if key in cache:
        return cache[key]
    m = bpy.data.materials.new("pv_" + key)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    if isinstance(spec, tuple):
        bsdf.inputs["Base Color"].default_value = (spec[1], spec[2], spec[3], 1)
        m.diffuse_color = (spec[1], spec[2], spec[3], 1)
    else:
        tn = nt.nodes.new("ShaderNodeTexImage")
        tn.image = bpy.data.images.load(tex(spec), check_existing=True)
        nt.links.new(tn.outputs["Color"], bsdf.inputs["Base Color"])
    m["src_tex"] = key
    cache[key] = m
    return m

for o in bpy.data.objects:
    spec = MAP[suffix(o)]
    orig = [p.material_index for p in o.data.polygons]
    o.data.materials.clear()
    slot = {}
    for i in sorted(set(orig)):
        o.data.materials.append(make_mat(spec.get(i, spec.get("*", BLACK))))
        slot[i] = len(o.data.materials) - 1
    for p, mi in zip(o.data.polygons, orig):
        p.material_index = slot[mi]

# 3. reference frame from the table top (object -1-36)
top = next(o for o in bpy.data.objects if suffix(o) == "-1-36")
vs = [v.co for v in top.data.vertices]
tmin = mathutils.Vector([min(v[i] for v in vs) for i in range(3)])
tmax = mathutils.Vector([max(v[i] for v in vs) for i in range(3)])
centre = mathutils.Vector(((tmin.x + tmax.x) / 2, (tmin.y + tmax.y) / 2, tmax.z))
print("TABLE_TOP_CM", tuple(round(x, 2) for x in (tmax - tmin)), "top z", round(tmax.z, 2))

def group_objs(g):
    return [o for o in bpy.data.objects if suffix(o) in GROUPS[g]]

def group_bounds(objs):
    pts = [v.co for o in objs for v in o.data.vertices]
    return (mathutils.Vector([min(p[i] for p in pts) for i in range(3)]),
            mathutils.Vector([max(p[i] for p in pts) for i in range(3)]))

# 4. move props: target centre (cm, relative to table-top centre) and z-rotation (deg)
for g, (tx, ty, rot) in cfg["props"].items():
    objs = group_objs(g)
    if not objs:
        continue
    if tx is None:
        for o in objs:
            bpy.data.objects.remove(o, do_unlink=True)
        continue
    mn, mx = group_bounds(objs)
    c = mathutils.Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    M = (mathutils.Matrix.Translation(centre + mathutils.Vector((tx, ty, 0)))
         @ mathutils.Matrix.Rotation(math.radians(rot), 4, 'Z')
         @ mathutils.Matrix.Translation(-c))
    for o in objs:
        o.data.transform(M)
    # sit on the table top
    mn, mx = group_bounds(objs)
    dz = centre.z - mn.z
    for o in objs:
        o.data.transform(mathutils.Matrix.Translation((0, 0, dz)))

# 4b. sword (汉刀 02): hilt up-right over the map's west edge, tip just past the table's south edge
sw = cfg.get("sword")
if sw:
    ext_root = os.path.join(os.environ["APPDATA"], "Blender Foundation", "Blender", "4.2", "extensions", "user_default")
    sys.path.insert(0, ext_root)
    from io_pdx_mesh.pdx_blender import blender_import_export as bie
    before = set(bpy.data.objects)
    bie.import_meshfile(sw["mesh"], imp_mesh=True, imp_skel=False, imp_locs=False, join_materials=True)
    new = [o for o in bpy.data.objects if o not in before]
    sword = [o for o in new if o.type == 'MESH']
    for o in new:
        if o.type != 'MESH':
            bpy.data.objects.remove(o, do_unlink=True)
    for o in sword:
        o.parent = None
        o.data.transform(o.matrix_world)
        o.matrix_world = mathutils.Matrix.Identity(4)
    mn, mx = group_bounds(sword)
    length = mx.y - mn.y                      # source blade runs along Y, ring pommel at +Y
    L, ang, e = sw["length_cm"], sw["tilt_deg"], sw["overhang_cm"]
    d = mathutils.Vector((math.sin(math.radians(ang)), math.cos(math.radians(ang)), 0))
    half_map_x = MAP_W / 2 / K
    half_table_y = (tmax.y - tmin.y) / 2
    cross = sw["cross_frac"]                  # fraction of length (from the tip) where it crosses the map edge
    tip = mathutils.Vector((-half_map_x - cross * L * d.x, -half_table_y - e, 0))
    mid = tip + d * (L / 2)
    if sw.get("top_cm"):
        # explicit north end (cm from table-top centre), e.g. measured from an in-game screenshot
        top = mathutils.Vector((sw["top_cm"][0], sw["top_cm"][1], 0))
        mid = top - d * (L / 2)
        tip = top - d * L
    z_bottom = centre.z + (sw["bottom_world_y"] - TOP_Z) / K
    # lay flat: blade width (src Z) -> X, thickness (src X) -> Z, length stays Y
    flat = mathutils.Matrix(((0, 0, 1, 0), (0, 1, 0, 0), (-1, 0, 0, 0), (0, 0, 0, 1)))
    if sw.get("tip_up"):
        # blade tip toward the map, ring pommel at the south end hanging past the table
        flat = mathutils.Matrix.Rotation(math.pi, 4, 'Z') @ flat
    c = (mn + mx) / 2
    M = (mathutils.Matrix.Translation((centre.x + mid.x, centre.y + mid.y, 0))
         @ mathutils.Matrix.Rotation(-math.radians(ang), 4, 'Z')
         @ mathutils.Matrix.Scale(L / length, 4) @ flat @ mathutils.Matrix.Translation(-c))
    for o in sword:
        o.data.transform(M)
    mn, mx = group_bounds(sword)
    for o in sword:
        o.data.transform(mathutils.Matrix.Translation((0, 0, z_bottom - mn.z)))
        o["group"] = "sword"
        for m in o.data.materials:
            if m and m.use_nodes and sw.get("preview_diffuse"):
                nt = m.node_tree
                bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
                tn = nt.nodes.new("ShaderNodeTexImage")
                tn.image = bpy.data.images.load(sw["preview_diffuse"], check_existing=True)
                nt.links.new(tn.outputs["Color"], bsdf.inputs["Base Color"])
                nt.nodes.active = tn
    GROUPS["sword"] = [suffix(o) for o in sword]
    print("SWORD tip", tuple(round(v, 2) for v in tip), "dir", tuple(round(v, 3) for v in d))

# 5. table-top centre -> origin, scale to CK3 units, drop top surface to TOP_Z
G = (mathutils.Matrix.Translation((0, 0, TOP_Z)) @ mathutils.Matrix.Scale(K, 4)
     @ mathutils.Matrix.Translation(-centre))
for o in bpy.data.objects:
    o.data.transform(G)
    o.data.update()
    o["group"] = next(g for g, s in GROUPS.items() if suffix(o) in s)

print("SCENE_BUILT", len(bpy.data.objects))
if len(argv) > 1:
    bpy.ops.wm.save_as_mainfile(filepath=argv[1])
