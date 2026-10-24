"""Write the CK3 text files for the Han-Jin lacquer map table into the staging tree.

python -P write_text.py <stage_root> <roundtrip.json> <vanilla_game_dir>
"""
import json, os, shutil, sys

stage, rt_path, game = sys.argv[1:4]
rt = json.load(open(rt_path, encoding="utf-8"))

MAP_CX, MAP_CZ = 11136 / 2, 6848 / 2
STYLE = "map_table_style_hd_han"
LAYER = "map_table_layer_hd_han"


def write(rel, text, bom=True):
    path = os.path.join(stage, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = text.replace("\r\n", "\n").replace("\n", "\r\n")
    with open(path, "w", encoding="utf-8-sig" if bom else "utf-8", newline="") as f:
        f.write(data)
    print("WROTE", rel)


def shapes(fname):
    return [(r["shape"], r["index"]) for r in rt[fname]["raw"]]


# ---------------------------------------------------------------- .asset
DIFF = {
    "hd_han_table_top": "hd_han_table_top_diffuse.dds",
    "hd_han_table_side": "hd_han_table_side_diffuse.dds",
    "hd_han_plate_top": "hd_han_plate_top_diffuse.dds",
    "hd_han_plate_rim": "hd_han_plate_rim_diffuse.dds",
    "hd_han_cup": "hd_han_cup_diffuse.dds",
    "hd_han_cup_ears": "hd_han_cup_ears_diffuse.dds",
    "hd_han_censer": "hd_han_censer_diffuse.dds",
}
SHADER = {"hd_han_table_top": "standard_map_decoration", "hd_han_table_side": "standard_map_decoration"}

blocks = []
ms = []
order = ["hd_han_table_top", "hd_han_table_side", "hd_han_plate_top", "hd_han_plate_rim",
         "hd_han_cup", "hd_han_cup_ears", "hd_han_censer"]
found = dict(shapes("hd_han_tabletop.mesh"))
assert set(found) == set(order), (sorted(found), order)
for name in order:
    ms.append(f"""	meshsettings = {{
		name = "{name}"
		index = {found[name]}
		texture_diffuse = "{DIFF[name]}"
		texture_normal = "null_normal.dds"
		texture_specular = "null_gloss.dds"
		shader = "{SHADER.get(name, 'tabletop_standard')}"
		shader_file = "gfx/FX/pdxmesh.shader"
	}}
""")
blocks.append("""# 汉晋漆案地图桌：漆案、红漆盘、耳杯、博山炉（素材 3d66 #18349387）
pdxmesh = {
	name = "hd_han_tabletop_mesh"
	file = "hd_han_tabletop.mesh"

	cull_distance = 50000.0

""" + "\n".join(ms) + """}

entity = {
	name = "hd_han_tabletop_entity"
	pdxmesh = "hd_han_tabletop_mesh"
}
""")

(sw_name, sw_idx), = shapes("hd_han_tabletop_sword.mesh")
assert sw_name == "hd_han_sword"
blocks.append(f"""# 桌上汉刀：取自 hd_weapon_handao_02，单独物件走 Map 通道，才能压在地图西缘之上
# 压在纸面地图上的物件按 _table_styles.info 用 standard 系着色器
pdxmesh = {{
	name = "hd_han_tabletop_sword_mesh"
	file = "hd_han_tabletop_sword.mesh"

	cull_distance = 50000.0

	meshsettings = {{
		name = "{sw_name}"
		index = {sw_idx}
		texture_diffuse = "hd_han_sword_diffuse.dds"
		texture_normal = "hd_han_sword_normal.dds"
		texture_specular = "hd_han_sword_properties.dds"
		shader = "standard"
		shader_file = "gfx/FX/pdxmesh.shader"
	}}
}}

entity = {{
	name = "hd_han_tabletop_sword_entity"
	pdxmesh = "hd_han_tabletop_sword_mesh"
}}
""")

(fl_name, fl_idx), = shapes("hd_han_tabletop_floor.mesh")
assert fl_name == "hd_han_floor"
blocks.append(f"""# 地面：原版天下风格深色地砖 + 按本桌轮廓重烘的光照贴图
pdxmesh = {{
	name = "hd_han_tabletop_floor_mesh"
	file = "hd_han_tabletop_floor.mesh"

	cull_distance = 50000.0

	meshsettings = {{
		name = "{fl_name}"
		index = {fl_idx}
		texture_diffuse = "hd_han_floor_diffuse.dds"
		texture_normal = "hd_han_floor_normal.dds"
		texture_specular = "hd_han_floor_properties.dds"
		shader = "map_floor"
		shader_file = "gfx/FX/pdxmesh.shader"

		texture = {{ file = "hd_han_floor_lighting.dds" index = 7 }}
		additional_shader_defines = {{
			"BAKED_LIGHTING"
			"LIGHTING_DECAL"
			"TILING float4 (2.72, 2.72, 1, 1)"
		}}
	}}
}}

entity = {{
	name = "hd_han_tabletop_floor_entity"
	pdxmesh = "hd_han_tabletop_floor_mesh"
}}
""")
write("gfx/models/tabletop/hd_han/hd_han_tabletop.asset", "\n".join(blocks), bom=False)

# ---------------------------------------------------------------- map objects
def obj(name, render_pass, entity):
    return f"""object={{
	name="{name}"
	render_pass={render_pass}
	clamp_to_water_level=yes
	generated_content=no
	layer="{LAYER}"
	entity="{entity}"
	count=1
	transform="{MAP_CX:.6f} 0.000000 {MAP_CZ:.6f} 0.000000 0.000000 0.000000 1.000000 1.000000 1.000000 1.000000
"}}
"""
write("gfx/map/map_object_data/hd_han_map_table.txt",
      obj("hd_han_tabletop", "MapUnderTerrain", "hd_han_tabletop_entity")
      + obj("hd_han_tabletop_floor", "MapUnderTerrain", "hd_han_tabletop_floor_entity")
      + obj("hd_han_tabletop_sword", "Map", "hd_han_tabletop_sword_entity"))

write("gfx/map/map_object_data/hd_han_map_table_layers.txt", f"""layer={{
	name="{LAYER}"
	fade_in=21
	fade_out=80
	category=""
	masks=""
	visibility_tags="{STYLE}"
}}
""")

# ---------------------------------------------------------------- style + environment
write("gfx/map/table_styles/hd_han_table_styles.txt", f"""# 汉晋漆案：不依赖 DLC，优先级高于原版各风格，「动态」设置下任何角色都用它
{STYLE} = {{
	environment = "gfx/map/environment/environment_hd_han_table.txt"
	audio_parameter = asian
	priority = 10
	is_shown = {{
		always = yes
	}}
}}
""")
env = open(os.path.join(game, "gfx/map/environment/environment_tgp_table.txt"), encoding="utf-8").read()
write("gfx/map/environment/environment_hd_han_table.txt", env, bom=False)

# ---------------------------------------------------------------- localization
write("localization/simp_chinese/hd_map_table_style_l_simp_chinese.yml",
      f'l_simp_chinese:\n {STYLE}:0 "汉晋漆案"\n')
write("localization/english/hd_map_table_style_l_english.yml",
      f'l_english:\n {STYLE}:0 "Han-Jin Lacquer Table"\n')
print("TEXT_DONE")
