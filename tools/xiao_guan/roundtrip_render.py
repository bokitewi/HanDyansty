import bpy, sys, importlib, math
from mathutils import Vector
pdx = importlib.import_module("bl_ext.user_default.io_pdx_mesh.pdx_blender.blender_import_export")
args = sys.argv[sys.argv.index("--") + 1:]
hat_path, head_path, out = args[:3]
bpy.ops.wm.read_factory_settings(use_empty=True)

def imp(p, skel):
    b = set(bpy.data.objects)
    pdx.import_meshfile(p, imp_mesh=True, imp_skel=skel, imp_locs=True)
    return [o for o in bpy.data.objects if o not in b]

hat_objs = imp(hat_path, True)
for o in hat_objs:
    if o.type == 'MESH':
        me = o.data
        me.calc_loop_triangles()
        print("RT obj", o.name, "data", me.name, "tris", len(me.loop_triangles), "verts", len(me.vertices),
              "uv", [u.name for u in me.uv_layers])
        ws = [v.co for v in me.vertices]
        print("RT bbox", [round(min(getattr(v, a) for v in ws), 2) for a in "xyz"], [round(max(getattr(v, a) for v in ws), 2) for a in "xyz"])
        print("RT infl", max(len(v.groups) for v in me.vertices), "unweighted", sum(1 for v in me.vertices if not v.groups),
              "wsum_dev", round(max(abs(sum(g.weight for g in v.groups) - 1) for v in me.vertices), 4))
        for m in me.materials:
            print("RT mat", m.name, m.get("shader"), [n.image.filepath for n in m.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image])
        uv = me.uv_layers[0]
        bad = sum(1 for t in me.loop_triangles if abs((uv.data[t.loops[1]].uv - uv.data[t.loops[0]].uv).cross(uv.data[t.loops[2]].uv - uv.data[t.loops[0]].uv)) < 1e-8)
        print("RT zero_uv", bad)
    elif o.type == 'ARMATURE':
        print("RT rig bones", len(o.data.bones))

head_objs = imp(head_path, False)
skin = bpy.data.materials.new("skin"); skin.diffuse_color = (0.78, 0.62, 0.52, 1)
for o in head_objs:
    if o.type == 'MESH':
        o.data.materials.clear(); o.data.materials.append(skin)
        o.modifiers.clear()
hairm = bpy.data.materials.new("hair"); hairm.diffuse_color = (0.05, 0.04, 0.035, 1)
for extra in args[3:]:
    for o in imp(extra, False):
        if o.type == 'MESH':
            o.data.materials.clear(); o.data.materials.append(hairm); o.modifiers.clear()
            zs = [v.co.z for v in o.data.vertices]
            print("RT hair", o.name, "zmax", round(max(zs), 2))
for o in hat_objs:
    if o.type == 'MESH':
        o.modifiers.clear()

sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.color_type = 'TEXTURE'
sc.display.shading.light = 'STUDIO'
sc.display.shading.show_cavity = True
sc.display.shading.show_backface_culling = False
sc.render.resolution_x = 560; sc.render.resolution_y = 700
cd = bpy.data.cameras.new("c"); cd.type = 'ORTHO'; cd.ortho_scale = 66
cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
tgt = Vector((0, 0, 54))
views = {"front": (0, -1, 0.05), "side": (-1, 0, 0.05), "three": (-0.65, -0.75, 0.3),
         "backleft": (-0.75, 0.6, 0.35), "frontright": (0.35, -1, 0.2), "back": (0, 1, 0.1)}
for n, d in views.items():
    dv = Vector(d).normalized()
    cam.location = tgt + dv * 200
    cam.rotation_euler = (-dv).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f"{out}_{n}.png"
    bpy.ops.render.render(write_still=True)
