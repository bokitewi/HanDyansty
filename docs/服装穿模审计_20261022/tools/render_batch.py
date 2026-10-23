"""Batch pose renders in ONE Blender process: body+rig+anim loaded once, garments swapped.
blender -b --factory-startup --python render_batch.py -- <outdir> <anims comma> <list.txt>
list.txt: one 'label|path.mesh' per line. Output: <outdir>/<label>__<anim>.png (front view, mid frame of anim)
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, r"E:\documents\Paradox Interactive\Crusader Kings III\mod\tools")
from hd_tw3k_common import *  # noqa: F401,F403
import bpy
from mathutils import Vector

outdir = Path(sys.argv[sys.argv.index("--") + 1])
anims = sys.argv[sys.argv.index("--") + 2].split(",")
items = [l.strip().split("|", 1) for l in open(sys.argv[sys.argv.index("--") + 3], encoding="utf-8") if "|" in l]
outdir.mkdir(parents=True, exist_ok=True)

reset()
import os
SEXDIR = "female_body" if os.environ.get("HD_SEX") == "f" else "male_body"
body, rig = import_pdx(GAME / "gfx/models/portraits" / SEXDIR / (SEXDIR + ".mesh"))
body[0].color = (0.93, 0.74, 0.6, 1.0)
PALETTE = [(0.75, 0.2, 0.2), (0.2, 0.45, 0.8), (0.25, 0.65, 0.3), (0.8, 0.7, 0.15), (0.6, 0.3, 0.75),
           (0.15, 0.7, 0.7), (0.85, 0.5, 0.15), (0.45, 0.45, 0.45), (0.7, 0.4, 0.5), (0.3, 0.3, 0.8)]

sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sh = sc.display.shading
sh.light = "STUDIO"
sh.color_type = "OBJECT"
sh.show_object_outline = True
sc.render.resolution_x = 600
sc.render.resolution_y = 600
sc.render.image_settings.file_format = "PNG"
sc.view_settings.view_transform = "Standard"
cam_data = bpy.data.cameras.new("cam")
cam_data.type = "ORTHO"
cam_data.ortho_scale = 76.0
cam_data.clip_end = 2000
cam = bpy.data.objects.new("cam", cam_data)
bpy.context.collection.objects.link(cam)
sc.camera = cam
cam.location = Vector((0.0, -300.0, 108.0 if SEXDIR == "female_body" else 116.0))
cam.rotation_euler = (1.5707963, 0, 0)

# one-time: load each anim into its own action and keep it
actions = {}
for an in anims:
    pdx.import_animfile(str(GAME / "gfx/models/portraits" / SEXDIR / (an + ".anim")), frame_start=1)
    act = rig.animation_data.action
    act.name = "A_" + an
    act.use_fake_user = True
    actions[an] = act
    rig.animation_data_clear()
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.scale = (1, 1, 1)
print("ANIMS_LOADED", list(actions))

for label, path in items:
    t0 = time.time()
    try:
        ms, r = import_pdx(Path(path), skel=True)
    except Exception as exc:  # noqa: BLE001
        print("IMPORT_FAIL", label, exc)
        continue
    for i, o in enumerate(ms):
        for m in o.modifiers:
            if m.type == "ARMATURE":
                m.object = rig
        c = PALETTE[i % len(PALETTE)]
        o.color = (c[0], c[1], c[2], 1.0)
    if r is not None and r is not rig:
        bpy.data.objects.remove(r, do_unlink=True)
    for an, act in actions.items():
        rig.animation_data_create()
        rig.animation_data.action = act
        f = (int(act.frame_range[0]) + int(act.frame_range[1])) // 2
        sc.frame_set(1)
        sc.frame_set(max(1, f) if an != "rest" else 1)
        sc.render.filepath = str(outdir / ("%s__%s.png" % (label, an)))
        bpy.ops.render.render(write_still=True)
    rig.animation_data_clear()
    for o in ms:
        bpy.data.objects.remove(o, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    print("ITEM_DONE", label, "%.1fs" % (time.time() - t0), flush=True)
print("BATCH_OK")
