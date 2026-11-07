# Textured EEVEE preview of the 缁布束发冠 on the male head + topknot hair.
# Usage: blender -b --factory-startup --python preview_zibu.py -- <hat.mesh> <head.mesh> <hair.mesh> <png_dir> <variant> <out_prefix>
import bpy, sys, importlib, os
from mathutils import Vector
pdx = importlib.import_module("bl_ext.user_default.io_pdx_mesh.pdx_blender.blender_import_export")
hat_p, head_p, hair_p, png, var, out = sys.argv[sys.argv.index("--") + 1:][:6]
NAME = "m_headgear_hd_huaxia_zibu_guan"
bpy.ops.wm.read_factory_settings(use_empty=True)
def imp(p):
    b = set(bpy.data.objects)
    pdx.import_meshfile(p, imp_mesh=True, imp_skel=False, imp_locs=False)
    return [o for o in bpy.data.objects if o not in b and o.type == 'MESH']
def flat(name, col, rough=0.6):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = col; b.inputs["Roughness"].default_value = rough
    return m
for o in imp(head_p):
    o.modifiers.clear(); o.data.materials.clear(); o.data.materials.append(flat("skin", (0.62, 0.45, 0.36, 1)))
for o in imp(hair_p):
    o.modifiers.clear(); o.data.materials.clear(); o.data.materials.append(flat("hair", (0.02, 0.018, 0.016, 1), 0.45))
hat = imp(hat_p)
m = bpy.data.materials.new("hat"); m.use_nodes = True
nt = m.node_tree; b = nt.nodes["Principled BSDF"]
def img(nm, noncolor=False):
    n = nt.nodes.new("ShaderNodeTexImage"); n.image = bpy.data.images.load(os.path.join(png, f"{NAME}_{nm}.png"))
    n.interpolation = 'Closest' if False else 'Linear'
    if noncolor: n.image.colorspace_settings.name = 'Non-Color'
    return n
d = img(f"{var}_diffuse"); pr = img("properties", True)
nt.links.new(d.outputs["Color"], b.inputs["Base Color"])
nt.links.new(d.outputs["Alpha"], b.inputs["Alpha"])
sep = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(pr.outputs["Color"], sep.inputs["Color"])
nt.links.new(sep.outputs["Blue"], b.inputs["Metallic"])
nt.links.new(pr.outputs["Alpha"], b.inputs["Roughness"])
m.surface_render_method = 'DITHERED'
m.use_backface_culling = False
for o in hat:
    o.modifiers.clear(); o.data.materials.clear(); o.data.materials.append(m)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE_NEXT'
sc.eevee.taa_render_samples = 32
sc.render.film_transparent = False
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.55, 0.58, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.9
for loc, e in (((-60, -80, 120), 3.0), ((80, -40, 90), 1.5), ((0, 90, 110), 1.2)):
    ld = bpy.data.lights.new("l", 'SUN'); ld.energy = e
    lo = bpy.data.objects.new("l", ld); sc.collection.objects.link(lo)
    lo.rotation_euler = (-Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
sc.render.resolution_x = 600; sc.render.resolution_y = 700
cd = bpy.data.cameras.new("c"); cd.type = 'ORTHO'; cd.ortho_scale = 48
cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
tgt = Vector((0, 0, 65))
for n, dv in {"front": (0, -1, 0.08), "three": (-0.7, -0.75, 0.25), "side": (-1, 0, 0.08), "back": (0.5, 0.9, 0.3)}.items():
    dv = Vector(dv).normalized()
    cam.location = tgt + dv * 200
    cam.rotation_euler = (-dv).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f"{out}_{var}_{n}.png"
    bpy.ops.render.render(write_still=True)
