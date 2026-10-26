"""blender -b --factory-startup --python render_genes.py -- <outdir> <list.txt> <genes comma>   env HD_SEX"""
import sys, os
from pathlib import Path
sys.path.insert(0, r"E:\documents\Paradox Interactive\Crusader Kings III\mod\tools")
from hd_tw3k_common import *  # noqa
import bpy
argv = sys.argv[sys.argv.index("--") + 1:]
outdir = Path(argv[0]); outdir.mkdir(parents=True, exist_ok=True)
items = [l.strip().split("|", 1) for l in open(argv[1], encoding="utf-8") if "|" in l]
genes = argv[2].split(",")
SEX = os.environ.get("HD_SEX", "m")
HEADDIR = "female_head" if SEX == "f" else "male_head"
reset()
head, rig = import_pdx(GAME / "gfx/models/portraits" / HEADDIR / (HEADDIR + ".mesh"), skel=True)
for h in head: h.color = (0.93, 0.74, 0.6, 1.0)
actions = {}
from mathutils import Vector, Quaternion
def sample_pose(act, f):
    rig.animation_data.action = act
    bpy.context.scene.frame_set(f)
    return {pb.name: (pb.location.copy(), pb.rotation_quaternion.copy(), pb.scale.copy()) for pb in rig.pose.bones}
deltas = {}
for g in genes:
    pdx.import_animfile(str(GAME / "gfx/models/portraits" / HEADDIR / (HEADDIR + "_" + g + ".anim")), frame_start=1)
    act = rig.animation_data.action
    act.name = "G_" + g; act.use_fake_user = True
    actions[g] = (act, int(act.frame_range[0]), int(act.frame_range[1]))
    f0, f1 = actions[g][1], actions[g][2]; fm = (f0 + f1) // 2
    mid = sample_pose(act, fm)
    for tag, f in (("min", f0), ("max", f1)):
        P = sample_pose(act, f); D = {}
        for n, (l, q, sc_) in P.items():
            lm, qm, sm = mid[n]
            D[n] = (l - lm, q @ qm.inverted(), Vector((sc_[0] / sm[0], sc_[1] / sm[1], sc_[2] / sm[2])))
        deltas[f"{g}_{tag}"] = D
    rig.animation_data_clear()
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
rig.animation_data_create()
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sh = sc.display.shading; sh.light = "STUDIO"; sh.color_type = "OBJECT"; sh.show_object_outline = True; sh.show_backface_culling = False
sc.render.resolution_x = 420; sc.render.resolution_y = 420
sc.render.image_settings.file_format = "PNG"; sc.view_settings.view_transform = "Standard"
cd = bpy.data.cameras.new("cam"); cd.type = "ORTHO"; cd.ortho_scale = float(os.environ.get("HD_SCALE", "46")); cd.clip_end = 2000
cam = bpy.data.objects.new("cam", cd); bpy.context.collection.objects.link(cam); sc.camera = cam
CZ = float(os.environ.get("HD_CZ", "42"))
VIEWS = {"front": ((0.0, -300.0, CZ), (1.5707963, 0, 0)), "q34": ((212.0, -212.0, CZ), (1.5707963, 0, 0.7853982)),
         "side": ((300.0, 0.0, CZ), (1.5707963, 0, 1.5707963)), "lside": ((-300.0, 0.0, CZ), (1.5707963, 0, -1.5707963)),
         "q34l": ((-212.0, -212.0, CZ), (1.5707963, 0, -0.7853982)), "back": ((0.0, 300.0, CZ), (1.5707963, 0, 3.14159265))}
VLIST = os.environ.get("HD_VIEWS", "front,q34").split(",")
PAL = [(0.75, 0.2, 0.2), (0.2, 0.45, 0.8), (0.25, 0.65, 0.3), (0.8, 0.7, 0.15)]
for label, path in items:
    before = set(bpy.data.objects)
    ms, hrig = import_pdx(path, skel=True)
    for k, m in enumerate(ms): m.color = (*PAL[k % 4], 1.0)
    if hrig:
        for pb in hrig.pose.bones:
            if pb.name in rig.pose.bones:
                c = pb.constraints.new("COPY_TRANSFORMS"); c.target = rig; c.subtarget = pb.name
    rig.animation_data.action = None
    POSES = os.environ.get("HD_POSES")
    tags = ["rest"] + list(deltas.keys())
    if POSES:
        tags = [t for t in tags if t in POSES.split(",")]
    if label.endswith("_old"):
        tags = ["rest"]
    for tag in tags:
        if True:
            for pb in rig.pose.bones:
                if tag == "rest":
                    pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
                else:
                    l, q, s3 = deltas[tag][pb.name]
                    pb.location = l; pb.rotation_quaternion = q; pb.scale = s3
            sc.frame_set(1)
            bpy.context.view_layer.update()
            for v in (VLIST if tag == "rest" else [x for x in VLIST if x != "side"]):
                cam.location, cam.rotation_euler = VIEWS[v]
                sc.render.filepath = str(outdir / f"{label}__{tag}__{v}.png")
                bpy.ops.render.render(write_still=True)
    for o in list(bpy.data.objects):
        if o not in before: bpy.data.objects.remove(o, do_unlink=True)
print("FRAMES", {g: (a[1], a[2]) for g, a in actions.items()})
print("DONE")
