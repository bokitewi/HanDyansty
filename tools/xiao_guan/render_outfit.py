import bpy, sys, importlib
from mathutils import Vector
pdx = importlib.import_module("bl_ext.user_default.io_pdx_mesh.pdx_blender.blender_import_export")
args = sys.argv[sys.argv.index("--") + 1:]
out = args[0]
bpy.ops.wm.read_factory_settings(use_empty=True)
mats = {}
def mat(name, col):
    m = bpy.data.materials.new(name); m.diffuse_color = col; return m
mats["skin"] = mat("skin", (0.78, 0.62, 0.52, 1))
mats["hair"] = mat("hair", (0.05, 0.04, 0.035, 1))
mats["white"] = mat("white", (0.93, 0.92, 0.90, 1))
for spec in args[1:]:
    path, mode = spec.rsplit("|", 1)
    b = set(bpy.data.objects)
    pdx.import_meshfile(path, imp_mesh=True, imp_skel=False, imp_locs=False)
    for o in bpy.data.objects:
        if o in b or o.type != 'MESH':
            continue
        o.modifiers.clear()
        if mode != "tex":
            o.data.materials.clear(); o.data.materials.append(mats[mode])
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.color_type = 'TEXTURE'
sc.display.shading.light = 'STUDIO'
sc.display.shading.show_cavity = True
sc.render.resolution_x = 500; sc.render.resolution_y = 900
cd = bpy.data.cameras.new("c"); cd.type = 'ORTHO'; cd.ortho_scale = 200
cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
tgt = Vector((0, 0, 95))
for n, d in {"front": (0.25, -1, 0.1), "side": (-1, -0.3, 0.1)}.items():
    dv = Vector(d).normalized()
    cam.location = tgt + dv * 300
    cam.rotation_euler = (-dv).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f"{out}_{n}.png"
    bpy.ops.render.render(write_still=True)
