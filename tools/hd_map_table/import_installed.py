import sys, os, bpy
argv = sys.argv[sys.argv.index("--") + 1:]
d, out_blend = argv
ext_root = os.path.join(os.environ["APPDATA"], "Blender Foundation", "Blender", "4.2", "extensions", "user_default")
sys.path.insert(0, ext_root)
from io_pdx_mesh.pdx_blender import blender_import_export as bie
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for f in ("hd_han_tabletop.mesh", "hd_han_tabletop_sword.mesh", "hd_han_tabletop_floor.mesh"):
    bie.import_meshfile(os.path.join(d, f), imp_mesh=True, imp_skel=False, imp_locs=False, join_materials=True)
for o in bpy.data.objects:
    if o.type == 'MESH':
        for m in o.data.materials:
            if m and m.use_nodes:
                img = next((n for n in m.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image and "diffuse" in n.image.name.lower()), None)
                if img: m.node_tree.nodes.active = img
bpy.context.scene.display.shading.show_backface_culling = True
bpy.ops.wm.save_as_mainfile(filepath=out_blend)
print("IMPORTED", len(bpy.data.objects))
