import sys, os, json
import bpy, mathutils

argv = sys.argv[sys.argv.index("--") + 1:]
ext_dir, max_path, out_blend, out_json = argv

sys.path.insert(0, ext_dir)
from io_scene_max import import_max

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

import_max.parent_dict.clear()
import_max.matrix_dict.clear()
mscale = mathutils.Matrix.Scale(1.0, 4)
import_max.read(bpy.context, max_path, mscale,
                obtypes={'MATERIAL', 'UV', 'PRIMITIVE', 'EMPTY'},
                search=True, transform=True)

dg = bpy.context.evaluated_depsgraph_get()
rep = []
for o in bpy.data.objects:
    d = {"name": o.name, "type": o.type,
         "parent": o.parent.name if o.parent else None,
         "loc": list(o.matrix_world.translation),
         "scale": list(o.matrix_world.to_scale()),
         "det": o.matrix_world.determinant()}
    if o.type == 'MESH':
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        ws = [o.matrix_world @ v.co for v in me.vertices]
        if ws:
            mn = [min(p[i] for p in ws) for i in range(3)]
            mx = [max(p[i] for p in ws) for i in range(3)]
        else:
            mn = mx = [0, 0, 0]
        me.calc_loop_triangles()
        d.update({"verts": len(me.vertices), "tris": len(me.loop_triangles),
                  "polys": len(me.polygons),
                  "bmin": mn, "bmax": mx,
                  "uv": [u.name for u in me.uv_layers],
                  "mats": [m.name if m else None for m in o.data.materials],
                  "modifiers": [m.type for m in o.modifiers]})
        ev.to_mesh_clear()
    rep.append(d)

mats = {}
for m in bpy.data.materials:
    imgs = []
    if m.use_nodes:
        for n in m.node_tree.nodes:
            if n.type == 'TEX_IMAGE' and n.image:
                imgs.append(os.path.basename(n.image.filepath))
    mats[m.name] = {"diffuse": list(m.diffuse_color), "images": imgs}

json.dump({"objects": rep, "materials": mats}, open(out_json, "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
bpy.ops.wm.save_as_mainfile(filepath=out_blend)
print("AUDIT_DONE", len(rep))
