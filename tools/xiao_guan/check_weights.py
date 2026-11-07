import bpy, sys, importlib
from collections import Counter
pdx = importlib.import_module("bl_ext.user_default.io_pdx_mesh.pdx_blender.blender_import_export")
bpy.ops.wm.read_factory_settings(use_empty=True)
pdx.import_meshfile(sys.argv[sys.argv.index("--") + 1], imp_mesh=True, imp_skel=True, imp_locs=False)
o = next(o for o in bpy.data.objects if o.type == 'MESH')
names = {g.index: g.name for g in o.vertex_groups}
BAD = ("bn_h_jaw", "bn_h_mouth", "bn_h_chin", "bn_h_neck", "bn_h_cheek", "bn_h_l_clavicle")
regions = Counter(); bones = Counter()
for v in o.data.vertices:
    gs = {names[g.group]: g.weight for g in v.groups if g.weight > 0.01}
    bad = {k: w for k, w in gs.items() if k.startswith(BAD)}
    if not bad:
        continue
    p = v.co
    if p.z > 50.0:
        reg = "hat_upper(z>50)"
    elif p.y > 3:
        reg = "back_ribbon"
    else:
        reg = "strap_front"
    regions[reg] += 1
    for k, w in bad.items():
        bones[(reg, k)] += 1
print("WCHK", dict(regions))
for k, n in sorted(bones.items()):
    print("WCHK", k, n)
