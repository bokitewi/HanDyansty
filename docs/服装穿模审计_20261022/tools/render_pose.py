"""Flat-colour pose renders: CK3 male body (skin colour) + garments (distinct colours) driven by vanilla anims.
blender -b --factory-startup --python render_pose.py -- <outdir> --anims=a,b,c [--view=front|side|top] <mesh> [mesh ...]
"""
import sys
from pathlib import Path

sys.path.insert(0, r"E:\documents\Paradox Interactive\Crusader Kings III\mod\tools")
from hd_tw3k_common import *  # noqa: F401,F403
import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
outdir = Path(args[0])
outdir.mkdir(parents=True, exist_ok=True)
anims = []
view = "front"
meshes = []
for a in args[1:]:
    if a.startswith("--anims="):
        anims = a.split("=", 1)[1].split(",")
    elif a.startswith("--view="):
        view = a.split("=", 1)[1]
    else:
        meshes.append(a)

reset()
body, rig = import_pdx(GAME / "gfx/models/portraits/male_body/male_body.mesh")
clothes = []
for mp in meshes:
    ms, r = import_pdx(Path(mp), skel=True)
    for o in ms:
        for m in o.modifiers:
            if m.type == "ARMATURE":
                m.object = rig
        clothes.append(o)
    if r is not None and r is not rig:
        bpy.data.objects.remove(r, do_unlink=True)

PALETTE = [(0.75, 0.2, 0.2), (0.2, 0.45, 0.8), (0.25, 0.65, 0.3), (0.8, 0.7, 0.15), (0.6, 0.3, 0.75),
           (0.15, 0.7, 0.7), (0.85, 0.5, 0.15), (0.45, 0.45, 0.45), (0.7, 0.4, 0.5), (0.3, 0.3, 0.8)]
body[0].color = (0.93, 0.74, 0.6, 1.0)
for i, o in enumerate(clothes):
    c = PALETTE[i % len(PALETTE)]
    o.color = (c[0], c[1], c[2], 1.0)

sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sh = sc.display.shading
sh.light = "STUDIO"
sh.color_type = "OBJECT"
sh.show_object_outline = True
sc.render.resolution_x = 720
sc.render.resolution_y = 720
sc.render.image_settings.file_format = "PNG"
sc.view_settings.view_transform = "Standard"

cam_data = bpy.data.cameras.new("cam")
cam_data.type = "ORTHO"
cam_data.ortho_scale = 76.0
cam = bpy.data.objects.new("cam", cam_data)
bpy.context.collection.objects.link(cam)
sc.camera = cam
center = Vector((0.0, 0.0, 116.0))
if view == "front":
    cam.location = center + Vector((0, -300, 0))
    cam.rotation_euler = (1.5707963, 0, 0)
elif view == "side":
    cam.location = center + Vector((300, 0, 0))
    cam.rotation_euler = (1.5707963, 0, 1.5707963)
else:
    cam.location = center + Vector((0, -300, 0))
    cam.rotation_euler = (1.5707963, 0, 0)
cam_data.clip_end = 2000


def render(tag):
    sc.render.filepath = str(outdir / (tag + ".png"))
    bpy.ops.render.render(write_still=True)


GAMEP = GAME / "gfx/models/portraits/male_body"
render("rest_" + view)
for an in anims:
    path = GAMEP / (an + ".anim")
    if not path.is_file():
        print("MISSING", an)
        continue
    pdx.import_animfile(str(path), frame_start=1)
    frames = sorted({sc.frame_start, (sc.frame_start + sc.frame_end) // 2})
    for f in frames:
        sc.frame_set(f)
        render("%s_f%03d_%s" % (an, f, view))
    rig.animation_data_clear()
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.scale = (1, 1, 1)
print("RENDER_OK", outdir)
