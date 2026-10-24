import sys, os, math, json
import bpy, mathutils

argv = sys.argv[sys.argv.index("--") + 1:]
cfg = json.loads(open(argv[0], encoding="utf-8").read())
out_dir = argv[1]
os.makedirs(out_dir, exist_ok=True)
MAP_W, MAP_H, TOP_Z = cfg["map_w"], cfg["map_h"], cfg["top_z"]

# map placeholder (colormap) centred on origin
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, TOP_Z + 3))
mp = bpy.context.active_object
mp.scale = (MAP_W, MAP_H, 1)
m = bpy.data.materials.new("map")
m.use_nodes = True
tn = m.node_tree.nodes.new("ShaderNodeTexImage")
try:
    tn.image = bpy.data.images.load(cfg["map_image"])
except Exception as e:
    print("MAP_IMAGE_FAIL", e)
m.node_tree.links.new(tn.outputs["Color"], m.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
mp.data.materials.append(m)

if cfg.get("floor_image"):
    fz = TOP_Z - cfg["table_height_units"]
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, fz))
    fl = bpy.context.active_object
    fl.scale = (60000, 60000, 1)
    fm = bpy.data.materials.new("floor")
    fm.use_nodes = True
    nt = fm.node_tree
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(cfg["floor_image"])
    mapn = nt.nodes.new("ShaderNodeMapping")
    mapn.inputs["Scale"].default_value = (cfg["floor_tiles"], cfg["floor_tiles"], 1)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tc.outputs["UV"], mapn.inputs["Vector"])
    nt.links.new(mapn.outputs["Vector"], t.inputs["Vector"])
    nt.links.new(t.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    fl.data.materials.append(fm)

sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'TEXTURE'
sc.display.shading.show_shadows = True
sc.render.resolution_x, sc.render.resolution_y = 1600, 900

cd = bpy.data.cameras.new("c")
cam = bpy.data.objects.new("c", cd)
sc.collection.objects.link(cam)
sc.camera = cam
cd.clip_start, cd.clip_end = 10, 200000

def shoot(name, loc, target, ortho=None, lens=35):
    cam.location = mathutils.Vector(loc)
    cam.rotation_euler = (mathutils.Vector(target) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    if ortho:
        cd.type = 'ORTHO'; cd.ortho_scale = ortho
    else:
        cd.type = 'PERSP'; cd.lens = lens
    sc.render.filepath = os.path.join(out_dir, name + ".png")
    bpy.ops.render.render(write_still=True)

shoot("mock_top", (0, 0, 30000), (0, 0, TOP_Z), ortho=24000)
tilt = math.radians(70)
for nm, cx, dist in (("mock_tilt_whole", 0, 30000), ("mock_tilt_west_edge", -MAP_W / 2, 9000)):
    shoot(nm, (cx, -dist * math.cos(tilt), TOP_Z + dist * math.sin(tilt)), (cx, 0, TOP_Z))
shoot("mock_low_angle", (-16000, -17000, 9000), (-6000, 0, TOP_Z - 1500), lens=30)
print("MOCK_DONE")
