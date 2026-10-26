"""blender -b --factory-startup --python render_head.py -- <outdir> <list.txt>   list: label|mesh1;mesh2   env HD_SEX=f, HD_COLOR=object|texture"""
import sys, os
from pathlib import Path
sys.path.insert(0, r"E:\documents\Paradox Interactive\Crusader Kings III\mod\tools")
from hd_tw3k_common import *  # noqa
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
outdir = Path(argv[0]); outdir.mkdir(parents=True, exist_ok=True)
items = [l.strip().split("|", 1) for l in open(argv[1], encoding="utf-8") if "|" in l]
SEX = os.environ.get("HD_SEX", "m")
HEADDIR = "female_head" if SEX == "f" else "male_head"
COLOR = os.environ.get("HD_COLOR", "object")
reset()
head, rig = import_pdx(GAME / "gfx/models/portraits" / HEADDIR / (HEADDIR + ".mesh"))
for h in head:
    h.color = (0.93, 0.74, 0.6, 1.0)
PALETTE = [(0.75, 0.2, 0.2), (0.2, 0.45, 0.8), (0.25, 0.65, 0.3), (0.8, 0.7, 0.15), (0.6, 0.3, 0.75), (0.15, 0.7, 0.7)]
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sh = sc.display.shading
sh.light = "STUDIO"
sh.color_type = "OBJECT" if COLOR == "object" else "TEXTURE"
sh.show_object_outline = True
sh.show_backface_culling = False
sc.render.resolution_x = 520
sc.render.resolution_y = 520
sc.render.image_settings.file_format = "PNG"
sc.view_settings.view_transform = "Standard"
cd = bpy.data.cameras.new("cam"); cd.type = "ORTHO"; cd.ortho_scale = float(os.environ.get("HD_SCALE", "52")); cd.clip_end = 2000
cam = bpy.data.objects.new("cam", cd); bpy.context.collection.objects.link(cam); sc.camera = cam
CZ = float(os.environ.get("HD_CZ", "46"))
VIEWS = {"front": ((0.0, -300.0, CZ), (1.5707963, 0, 0)),
         "side": ((300.0, 0.0, CZ), (1.5707963, 0, 1.5707963)),
         "q34": ((212.0, -212.0, CZ), (1.5707963, 0, 0.7853982)),
         "back": ((0.0, 300.0, CZ), (1.5707963, 0, 3.14159265)),
         "top": ((0.0, 0.0, 300.0), (0, 0, 0))}
VLIST = os.environ.get("HD_VIEWS", "front,side,q34").split(",")
for label, paths in items:
    new = []
    for i, p in enumerate(paths.split(";")):
        ms, r = import_pdx(p, skel=False)
        for k, m in enumerate(ms):
            m.color = (*PALETTE[(i * 3 + k) % len(PALETTE)], 1.0)
        new += ms
    for v in VLIST:
        loc, rot = VIEWS[v]
        cam.location = loc; cam.rotation_euler = rot
        sc.render.filepath = str(outdir / f"{label}__{v}.png")
        bpy.ops.render.render(write_still=True)
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
print("DONE")
