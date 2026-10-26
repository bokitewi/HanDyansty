"""blender -b --factory-startup --python render_sel.py -- <outdir> <sel.json> <keys comma or ALL>   env HD_VIEWS"""
import sys, os, json
from pathlib import Path
sys.path.insert(0, r"E:\documents\Paradox Interactive\Crusader Kings III\mod\tools")
from hd_tw3k_common import *  # noqa
import bpy
argv = sys.argv[sys.argv.index("--") + 1:]
outdir = Path(argv[0]); outdir.mkdir(parents=True, exist_ok=True)
sel = json.load(open(argv[1], encoding="utf-8"))
keys = list(sel) if argv[2] == "ALL" else argv[2].split(",")
def colorize(o, idx, col_sel, col_other):
    me = o.data
    a = me.color_attributes.new("c", "FLOAT_COLOR", "POINT")
    s = set(idx)
    for i in range(len(me.vertices)):
        a.data[i].color = (*(col_sel if i in s else col_other), 1.0)
    me.color_attributes.active_color = a
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sh = sc.display.shading; sh.light = "STUDIO"; sh.color_type = "VERTEX"; sh.show_object_outline = True; sh.show_backface_culling = False
sc.render.resolution_x = 420; sc.render.resolution_y = 420
sc.render.image_settings.file_format = "PNG"; sc.view_settings.view_transform = "Standard"
cd = bpy.data.cameras.new("cam"); cd.type = "ORTHO"; cd.ortho_scale = 50; cd.clip_end = 2000
cam = bpy.data.objects.new("cam", cd); bpy.context.collection.objects.link(cam); sc.camera = cam
CZ = 44.0
VIEWS = {"front": ((0.0, -300.0, CZ), (1.5707963, 0, 0)), "q34": ((212.0, -212.0, CZ), (1.5707963, 0, 0.7853982)),
         "side": ((300.0, 0.0, CZ), (1.5707963, 0, 1.5707963)), "under": ((0, -212.0, CZ - 212.0), (0.7853982, 0, 0))}
VLIST = os.environ.get("HD_VIEWS", "front,side,q34").split(",")
heads = {}
for key in keys:
    folder, sex = key.split("|")
    for o in list(bpy.data.objects):
        if o.type == "MESH" and not o.name.startswith("HEAD_"):
            bpy.data.objects.remove(o, do_unlink=True)
    if sex not in heads:
        for o in [o for o in bpy.data.objects if o.name.startswith("HEAD_")]:
            bpy.data.objects.remove(o, do_unlink=True)
        heads.clear()
        d = "female_head" if sex == "f" else "male_head"
        hm, _ = import_pdx(GAME / "gfx/models/portraits" / d / (d + ".mesh"), skel=False)
        for h in hm:
            h.name = "HEAD_" + h.name; colorize(h, [], (0, 0, 0), (0.93, 0.74, 0.6))
        heads[sex] = hm
    ms, _ = import_pdx(sel[key]["path"], skel=False)
    for o in ms:
        nm = o.name
        hit = None
        for sname, idx in sel[key]["shapes"].items():
            if sname == nm or sname in nm or nm in sname or sname.replace("Shape", "") in nm:
                hit = idx
        if hit is None:
            print("NOMATCH", nm, list(sel[key]["shapes"]))
            hit = []
        colorize(o, hit, (0.9, 0.1, 0.1), (0.55, 0.6, 0.7))
    for v in VLIST:
        cam.location, cam.rotation_euler = VIEWS[v]
        sc.render.filepath = str(outdir / f"{folder}_{sex}__{v}.png")
        bpy.ops.render.render(write_still=True)
print("DONE")
