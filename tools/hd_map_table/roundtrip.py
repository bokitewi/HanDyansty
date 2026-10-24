import sys, os, json, math
import bpy, mathutils

argv = sys.argv[sys.argv.index("--") + 1:]
stage, out_dir, out_json = argv[0], argv[1], argv[2]
os.makedirs(out_dir, exist_ok=True)
ext_root = os.path.join(os.environ["APPDATA"], "Blender Foundation", "Blender", "4.2", "extensions", "user_default")
sys.path.insert(0, ext_root)
from io_pdx_mesh.pdx_blender import blender_import_export as bie
from io_pdx_mesh import pdx_data

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

report = {}
for fname in ("hd_han_tabletop.mesh", "hd_han_tabletop_sword.mesh", "hd_han_tabletop_floor.mesh"):
    path = os.path.join(stage, fname)
    # raw shape/vertex counts straight from the file
    root = pdx_data.read_meshfile(path)
    raw = []
    for shape in root.find("object"):
        for i, mesh in enumerate(shape.findall("mesh")):
            p = mesh.get("p"); tri = mesh.get("tri"); u0 = mesh.get("u0")
            mat = mesh.find("material")
            raw.append({"shape": shape.tag, "index": i, "verts": len(p) // 3, "tris": len(tri) // 3,
                        "uv_sets": sum(1 for k in ("u0", "u1", "u2", "u3") if mesh.get(k)),
                        "shader": mat.get("shader")[0] if mat is not None else None,
                        "diff": (mat.get("diff") or [None])[0] if mat is not None else None})
    before = set(bpy.data.objects)
    bie.import_meshfile(path, imp_mesh=True, imp_skel=False, imp_locs=True, join_materials=True)
    new = [o for o in bpy.data.objects if o not in before]
    shapes = []
    for o in new:
        if o.type != 'MESH':
            shapes.append({"name": o.name, "type": o.type})
            continue
        me = o.data
        me.calc_loop_triangles()
        ws = [o.matrix_world @ v.co for v in me.vertices]
        uv = me.uv_layers.active.data if me.uv_layers else None
        zero_uv = degen = 0
        umin = vmin = 1e9; umax = vmax = -1e9
        for t in me.loop_triangles:
            if t.area < 1e-6:
                degen += 1
            if uv:
                a, b, c = (uv[l].uv for l in t.loops)
                ar = abs((b - a).cross(c - a)) / 2 if hasattr(b - a, "cross") else abs((b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])) / 2
                if ar < 1e-9:
                    zero_uv += 1
                for q in (a, b, c):
                    umin, umax = min(umin, q[0]), max(umax, q[0]); vmin, vmax = min(vmin, q[1]), max(vmax, q[1])
        # winding sanity: fraction of faces whose normal points away from the object's centre
        cen = sum(ws, mathutils.Vector()) / max(1, len(ws))
        outward = sum(1 for p in me.polygons if (o.matrix_world.to_3x3() @ p.normal).dot((o.matrix_world @ p.center) - cen) > 0)
        shapes.append({"name": o.name, "verts": len(me.vertices), "tris": len(me.loop_triangles),
                       "bmin": [round(min(p[i] for p in ws), 1) for i in range(3)],
                       "bmax": [round(max(p[i] for p in ws), 1) for i in range(3)],
                       "uv_range": [round(umin, 3), round(umax, 3), round(vmin, 3), round(vmax, 3)],
                       "zero_area_uv_tris": zero_uv, "degenerate_tris": degen,
                       "outward_face_frac": round(outward / max(1, len(me.polygons)), 3),
                       "materials": [m.name for m in me.materials if m]})
    report[fname] = {"raw": raw, "shapes": shapes}

json.dump(report, open(out_json, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

# --- renders with backface culling, textures from the staged DDS ----------------------------
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'TEXTURE'
sc.display.shading.show_backface_culling = True
sc.render.resolution_x, sc.render.resolution_y = 1600, 900
for o in bpy.data.objects:
    if o.type == 'MESH':
        for m in o.data.materials:
            if m and m.use_nodes:
                img = next((n for n in m.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image
                            and "diffuse" in n.image.name.lower()), None)
                if img:
                    m.node_tree.nodes.active = img
cd = bpy.data.cameras.new("c"); cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
cd.clip_start, cd.clip_end = 10, 300000
def shoot(name, loc, target, ortho=None, lens=35):
    cam.location = mathutils.Vector(loc)
    cam.rotation_euler = (mathutils.Vector(target) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cd.type = 'ORTHO' if ortho else 'PERSP'
    if ortho: cd.ortho_scale = ortho
    else: cd.lens = lens
    sc.render.filepath = os.path.join(out_dir, name + ".png")
    bpy.ops.render.render(write_still=True)
floor = bpy.data.objects.get("hd_han_floor")
shoot("rt_top", (0, 0, 40000), (0, 0, -20), ortho=24000)
shoot("rt_low", (-16000, -17000, 9000), (-6000, 0, -1500), lens=30)
shoot("rt_front_low", (0, -26000, -2500), (0, 0, -3000), lens=35)
shoot("rt_under", (6000, -9000, -5600), (0, 0, -1200), lens=24)
if floor: floor.hide_render = True
shoot("rt_censer", (-8280 - 1500, 3420 - 2500, 2200), (-8280, 3420, 600), lens=50)
shoot("rt_cup_plate", (2000, -9000, 9000), (2000, 0, 0), lens=24)
print("RT_DONE")
