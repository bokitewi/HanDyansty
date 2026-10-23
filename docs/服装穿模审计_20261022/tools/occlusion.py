"""Arm-through-garment metric: body forearm/wrist/finger vertices occluded (from the front camera) by non-arm garment shapes.
blender -b --factory-startup --python occlusion.py -- <out.json> <anims comma> <list.txt>
list.txt: label|path.mesh
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, r"E:\documents\Paradox Interactive\Crusader Kings III\mod\tools")
from hd_tw3k_common import *  # noqa: F401,F403
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

out_path = Path(sys.argv[sys.argv.index("--") + 1])
anims = sys.argv[sys.argv.index("--") + 2].split(",")
items = [l.strip().split("|", 1) for l in open(sys.argv[sys.argv.index("--") + 3], encoding="utf-8") if "|" in l]

reset()
body, rig = import_pdx(GAME / "gfx/models/portraits/male_body/male_body.mesh")
bo = body[0]
ARM_KEYS = ("forearm", "wrist", "fi_")
gnames = [g.name for g in bo.vertex_groups]
arm_idx = []
for v in bo.data.vertices:
    if not len(v.groups):
        continue
    g = max(v.groups, key=lambda x: x.weight).group
    if any(k in gnames[g] for k in ARM_KEYS):
        arm_idx.append(v.index)
print("ARM_VERTS", len(arm_idx))

actions = {}
for an in anims:
    pdx.import_animfile(str(GAME / "gfx/models/portraits/male_body" / (an + ".anim")), frame_start=1)
    act = rig.animation_data.action
    act.name = "A_" + an
    act.use_fake_user = True
    actions[an] = act
    rig.animation_data_clear()
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.scale = (1, 1, 1)
print("ANIMS_LOADED", list(actions), flush=True)

SKIP_NAMES = ("sleeve", "bracer", "vambrace", "cuff", "glove", "gauntlet", "armband")
ARMBONES = ("forearm", "wrist", "elbow", "fi_", "sleeve", "bn_l_prop", "bn_r_prop")


def is_arm_shape(o):
    nm = o.name.lower()
    if any(k in nm for k in SKIP_NAMES):
        return True
    gn = [g.name for g in o.vertex_groups]
    if not gn:
        return False
    cnt = 0
    for v in o.data.vertices:
        if len(v.groups):
            g = max(v.groups, key=lambda x: x.weight).group
            if any(k in gn[g] for k in ARMBONES):
                cnt += 1
    return cnt > 0.4 * len(o.data.vertices)


res = {}
for label, path in items:
    t0 = time.time()
    try:
        ms, r = import_pdx(Path(path), skel=True)
    except Exception as exc:  # noqa: BLE001
        print("IMPORT_FAIL", label, exc)
        continue
    for o in ms:
        for m in o.modifiers:
            if m.type == "ARMATURE":
                m.object = rig
    if r is not None and r is not rig:
        bpy.data.objects.remove(r, do_unlink=True)
    solid = [o for o in ms if not is_arm_shape(o)]
    res[label] = {"solid": [o.name[-30:] for o in solid]}
    for an, act in actions.items():
        rig.animation_data_create()
        rig.animation_data.action = act
        sc = bpy.context.scene
        f = (int(act.frame_range[0]) + int(act.frame_range[1])) // 2
        sc.frame_set(1)
        sc.frame_set(max(1, f))
        dg = bpy.context.evaluated_depsgraph_get()
        eb = bo.evaluated_get(dg)
        me = eb.to_mesh()
        pts = [eb.matrix_world @ me.vertices[i].co for i in arm_idx]
        eb.to_mesh_clear()
        hidden = 0
        per_shape = {}
        for o in solid:
            bvh = BVHTree.FromObject(o, dg)
            c = 0
            for p in pts:
                if bvh.ray_cast(p + Vector((0, -0.05, 0)), Vector((0, -1, 0)), 300.0)[0] is not None:
                    c += 1
            per_shape[o.name[-24:]] = c
        # union count
        bvhs = [BVHTree.FromObject(o, dg) for o in solid]
        for p in pts:
            org = p + Vector((0, -0.05, 0))
            if any(b.ray_cast(org, Vector((0, -1, 0)), 300.0)[0] is not None for b in bvhs):
                hidden += 1
        res[label][an] = {"hidden": hidden, "per_shape": per_shape}
    rig.animation_data_clear()
    for o in ms:
        bpy.data.objects.remove(o, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    print("ITEM_DONE", label, {a: res[label][a]["hidden"] for a in anims}, "%.1fs" % (time.time() - t0), flush=True)
out_path.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print("OCC_OK")
