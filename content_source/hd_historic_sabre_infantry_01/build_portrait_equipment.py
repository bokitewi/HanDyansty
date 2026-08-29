"""Build the historic sabre infantry portrait meshes in Blender 4.2 LTS.

The script consumes the short-path, hash-verified RMV2 staging directory and
exports one CK3 PDX mesh per portrait slot plus the approved adult male body
blend shapes.  It intentionally does not register assets in CK3; registration
is kept in the ordinary mod text files.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from types import SimpleNamespace

import bpy
from mathutils import Vector, geometry
from mathutils.bvhtree import BVHTree


GAME_ROOT = Path(r"D:\SteamLibrary\steamapps\common\Crusader Kings III\game")
RMV2_ADDON_ROOT = Path(
    r"E:\documents\Paradox Interactive\Crusader Kings III\mod\tools\third_party"
    r"\io_scene_rmv2\1.8.0\app"
)
PDX_ADDON_ROOT = Path(
    r"E:\documents\Paradox Interactive\Crusader Kings III\mod\tools\third_party"
    r"\io_pdx_mesh\0.91\official_release"
)

REFERENCES = {
    "clothes": GAME_ROOT
    / "gfx/models/portraits/m_clothes/tgp_chinese/war_nob_01"
    / "m_clothes_sec_tgp_chinese_war_nob_01.mesh",
    "headgear": GAME_ROOT
    / "gfx/models/portraits/m_headgear/tgp_chinese/war_nob_01"
    / "m_headgear_sec_tgp_chinese_war_nob_01_hi.mesh",
    "legwear": GAME_ROOT
    / "gfx/models/portraits/m_legwear/tgp_chinese/war_nob_01"
    / "m_legwear_sec_tgp_chinese_war_nob_01.mesh",
}

REFERENCE_MORPHS = {
    "clothes": {
        "fat": "m_clothes_sec_tgp_chinese_war_nob_01_bs_fat.mesh",
        "gaunt": "m_clothes_sec_tgp_chinese_war_nob_01_bs_gaunt.mesh",
        "musc": "m_clothes_sec_tgp_chinese_war_nob_01_bs_musc.mesh",
        "old": "m_clothes_sec_tgp_chinese_war_nob_01_bs_old.mesh",
        "dwarf": "m_clothes_sec_tgp_chinese_war_nob_01_bs_dwarf.mesh",
    },
    "headgear": {
        "fat": "m_headgear_sec_tgp_chinese_war_nob_01_hi_bs_fat.mesh",
    },
    "legwear": {
        "fat": "m_legwear_sec_tgp_chinese_war_nob_01_bs_fat.mesh",
        "gaunt": "m_legwear_sec_tgp_chinese_war_nob_01_bs_gaunt.mesh",
        "musc": "m_legwear_sec_tgp_chinese_war_nob_01_bs_musc.mesh",
        "old": "m_legwear_sec_tgp_chinese_war_nob_01_bs_old.mesh",
        "dwarf": "m_legwear_sec_tgp_chinese_war_nob_01_bs_dwarf.mesh",
        "clothed": "m_legwear_sec_tgp_chinese_war_nob_01_bs_clothed.mesh",
    },
}

COMPONENTS = {
    "headgear": [
        ("helmet", True, "portrait_attachment_alpha_to_coverage"),
        ("feather", True, "portrait_attachment_alpha_to_coverage"),
    ],
    "clothes": [
        ("neck_collar", True, "portrait_attachment"),
        ("chest", True, "portrait_attachment"),
        ("skirt", False, "portrait_attachment"),
        ("collar_armour", True, "portrait_attachment"),
        ("shoulders", True, "portrait_attachment"),
        ("armour_belt", True, "portrait_attachment"),
        ("tunic_top", False, "portrait_attachment"),
        ("vambraces", True, "portrait_attachment"),
        ("tunic_bottom", False, "portrait_attachment"),
        ("scabbard", True, "portrait_attachment"),
        ("scabbard_hanger", True, "portrait_attachment"),
        ("outer_belt", True, "portrait_attachment"),
        ("yiling", False, "portrait_attachment"),
    ],
    "legwear": [
        ("trousers", False, "portrait_attachment"),
        ("greaves", True, "portrait_attachment"),
    ],
}

RESOURCE_NAMES = {
    "headgear": "m_headgear_hd_historic_sabre_infantry_01",
    "clothes": "m_clothes_hd_historic_sabre_infantry_01",
    "legwear": "m_legwear_hd_historic_sabre_infantry_01",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--inspect-only", action="store_true")
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])


def enable_addons() -> None:
    sys.path.insert(0, str(RMV2_ADDON_ROOT))
    sys.path.insert(0, str(PDX_ADDON_ROOT))
    import io_pdx_mesh
    import io_scene_rmv2

    io_pdx_mesh.register()
    io_scene_rmv2.register()


def reset_scene() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for collection in list(bpy.data.collections):
        if collection != bpy.context.scene.collection:
            bpy.data.collections.remove(collection)


def new_collection(name: str) -> bpy.types.Collection:
    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    return collection


def move_to_collection(obj: bpy.types.Object, collection: bpy.types.Collection) -> None:
    for current in list(obj.users_collection):
        current.objects.unlink(obj)
    collection.objects.link(obj)


def import_pdx(path: Path, *, skeleton: bool) -> tuple[list[bpy.types.Object], list[bpy.types.Object]]:
    before = set(bpy.data.objects)
    result = bpy.ops.io_pdx_mesh.import_mesh(
        filepath=str(path),
        chk_mesh=True,
        chk_skel=skeleton,
        chk_locs=False,
        chk_joinmats=True,
        chk_bonespace=False,
    )
    if result != {"FINISHED"}:
        raise RuntimeError(f"PDX import failed: {path}: {result}")
    added = set(bpy.data.objects) - before
    meshes = [obj for obj in added if obj.type == "MESH"]
    rigs = [obj for obj in added if obj.type == "ARMATURE"]
    if len(meshes) != 1 or len(rigs) > 1:
        raise RuntimeError(
            f"Unexpected PDX import objects for {path}: meshes={len(meshes)} rigs={len(rigs)}"
        )
    return meshes, rigs


def import_rmv2(path: Path) -> bpy.types.Object:
    from io_scene_rmv2 import import_rmv2 as importer

    before = set(bpy.data.objects)
    _, stats = importer.import_file(
        bpy.context,
        str(path),
        {
            "import_lods": "FIRST",
            "build_materials": False,
            "texture_root": str(path.parent),
            "create_attach_empties": False,
            "attach_armature": False,
            "global_scale": 100.0,
        },
    )
    added = [obj for obj in set(bpy.data.objects) - before if obj.type == "MESH"]
    if len(added) != 1 or stats["meshes"] != 1:
        raise RuntimeError(f"Unexpected RMV2 import for {path}: {stats}")
    return added[0]


def bounds(obj: bpy.types.Object) -> tuple[Vector, Vector]:
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    return (
        Vector(tuple(min(point[axis] for point in points) for axis in range(3))),
        Vector(tuple(max(point[axis] for point in points) for axis in range(3))),
    )


def apply_transform(obj: bpy.types.Object) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def clear_vertex_groups(obj: bpy.types.Object) -> None:
    for group in list(obj.vertex_groups):
        obj.vertex_groups.remove(group)


def transfer_weights(source: bpy.types.Object, reference: bpy.types.Object) -> None:
    clear_vertex_groups(source)
    modifier = source.modifiers.new("ck3_weight_transfer", "DATA_TRANSFER")
    modifier.object = reference
    modifier.use_vert_data = True
    modifier.data_types_verts = {"VGROUP_WEIGHTS"}
    modifier.vert_mapping = "POLYINTERP_NEAREST"
    modifier.mix_mode = "REPLACE"
    modifier.mix_factor = 1.0
    bpy.context.view_layer.objects.active = source
    source.select_set(True)
    bpy.ops.object.datalayout_transfer(
        modifier=modifier.name,
        data_type="VGROUP_WEIGHTS",
        use_delete=False,
        layers_select_src="ALL",
        layers_select_dst="NAME",
    )
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.ops.object.vertex_group_limit_total(group_select_mode="ALL", limit=4)
    bpy.ops.object.vertex_group_normalize_all(group_select_mode="ALL", lock_active=False)
    source.select_set(False)


def make_rigid_weights(obj: bpy.types.Object) -> None:
    for vertex in obj.data.vertices:
        assignments = [(item.group, item.weight) for item in vertex.groups if item.weight > 1e-8]
        if not assignments:
            continue
        keep = max(assignments, key=lambda item: item[1])[0]
        for group_index, _ in assignments:
            obj.vertex_groups[group_index].remove([vertex.index])
        obj.vertex_groups[keep].add([vertex.index], 1.0, "REPLACE")


def rigid_head_weights(obj: bpy.types.Object) -> None:
    clear_vertex_groups(obj)
    group = obj.vertex_groups.new(name="bn_h_head")
    group.add(range(len(obj.data.vertices)), 1.0, "REPLACE")


def bind_to_rig(obj: bpy.types.Object, rig: bpy.types.Object) -> None:
    modifier = obj.modifiers.new("io_pdx_rig_skin", "ARMATURE")
    modifier.object = rig


def create_pdx_material(
    name: str,
    shader: str,
    texture_dir: Path,
    component: str,
) -> bpy.types.Material:
    from io_pdx_mesh.pdx_blender.blender_import_export import create_shader

    material = create_shader(
        SimpleNamespace(
            shader=[shader],
            diff=[f"{name}_{component}_diffuse.dds"],
            spec=[f"{name}_{component}_properties.dds"],
            n=[f"{name}_{component}_normal.dds"],
        ),
        f"PDXmat_{name}_{component}",
        str(texture_dir),
    )
    material.name = f"PDXmat_{name}_{component}"
    return material


def weight_audit(obj: bpy.types.Object, rig: bpy.types.Object) -> dict[str, object]:
    rig_bones = set(rig.data.bones.keys())
    used_groups: set[str] = set()
    zero = 0
    over_limit = 0
    unnormalised = 0
    for vertex in obj.data.vertices:
        assignments = [item for item in vertex.groups if item.weight > 1e-6]
        total = sum(item.weight for item in assignments)
        zero += not assignments
        over_limit += len(assignments) > 4
        unnormalised += assignments and abs(total - 1.0) > 1e-4
        for item in assignments:
            used_groups.add(obj.vertex_groups[item.group].name)
    missing = sorted(used_groups - rig_bones)
    if zero or over_limit or unnormalised or missing:
        raise RuntimeError(
            f"Weight audit failed for {obj.name}: zero={zero} over_limit={over_limit} "
            f"unnormalised={unnormalised} missing={missing}"
        )
    return {"bones": sorted(used_groups), "vertices": len(obj.data.vertices)}


def mesh_audit(obj: bpy.types.Object) -> dict[str, int]:
    if not obj.data.uv_layers.active:
        raise RuntimeError(f"Missing UV map: {obj.name}")
    obj.data.calc_loop_triangles()
    zero_area = sum(triangle.area <= 1e-10 for triangle in obj.data.loop_triangles)
    if zero_area:
        raise RuntimeError(f"Zero-area triangles in {obj.name}: {zero_area}")
    return {
        "vertices": len(obj.data.vertices),
        "triangles": len(obj.data.loop_triangles),
        "materials": len(obj.data.materials),
    }


def join_components(objects: list[bpy.types.Object], shape_name: str) -> bpy.types.Object:
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    joined = objects[0]
    joined.name = shape_name
    joined.data.name = shape_name
    joined.data["meshindex"] = 0
    return joined


def select_only(*objects: bpy.types.Object) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.hide_set(False)
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]


def export_mesh(path: Path, mesh: bpy.types.Object, rig: bpy.types.Object | None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    objects = [mesh] + ([rig] if rig else [])
    select_only(*objects)
    result = bpy.ops.io_pdx_mesh.export_mesh(
        filepath=str(path),
        chk_mesh=True,
        # CK3 blend-shape files retain the base mesh's fully split vertex
        # layout.  The add-on's special "as blendshape" mode drops normal and
        # tangent splits, producing a vertex count the engine cannot pair.
        chk_mesh_blendshape=False,
        chk_skel=rig is not None,
        chk_locs=False,
        chk_selected=True,
        chk_debug=False,
    )
    if result != {"FINISHED"} or not path.is_file():
        raise RuntimeError(f"PDX export failed: {path}: {result}")


def apply_reference_delta(
    target: bpy.types.Object,
    reference_base: bpy.types.Object,
    reference_morph: bpy.types.Object,
) -> None:
    base_mesh = reference_base.data
    morph_mesh = reference_morph.data
    if len(base_mesh.vertices) != len(morph_mesh.vertices):
        raise RuntimeError("Reference base/morph vertex counts differ")
    base_mesh.calc_loop_triangles()
    tree = BVHTree.FromObject(reference_base, bpy.context.evaluated_depsgraph_get())
    for vertex in target.data.vertices:
        world_position = target.matrix_world @ vertex.co
        nearest = tree.find_nearest(world_position)
        if nearest is None:
            raise RuntimeError(f"Could not sample morph field for {target.name}")
        location, _, polygon_index, _ = nearest
        polygon = base_mesh.polygons[polygon_index]
        if len(polygon.vertices) != 3:
            raise RuntimeError("Reference mesh contains a non-triangle polygon")
        indices = polygon.vertices[:]
        base_points = [reference_base.matrix_world @ base_mesh.vertices[index].co for index in indices]
        morph_points = [reference_morph.matrix_world @ morph_mesh.vertices[index].co for index in indices]
        mapped = geometry.barycentric_transform(location, *base_points, *morph_points)
        vertex.co = target.matrix_world.inverted() @ (world_position + mapped - location)
    target.data.update()


def morph_reference_path(slot: str, filename: str) -> Path:
    return REFERENCES[slot].parent / filename


def main() -> None:
    args = parse_args()
    enable_addons()
    reset_scene()

    source_collection = new_collection("SOURCE_TW3K_ORIGINAL")
    reference_collection = new_collection("CK3_REFERENCE_RETARGET")
    export_collections = {
        slot: new_collection(f"EXPORT_{slot.upper()}") for slot in COMPONENTS
    }

    reference_meshes: dict[str, bpy.types.Object] = {}
    rigs: dict[str, bpy.types.Object] = {}
    for slot in ("clothes", "headgear", "legwear"):
        meshes, imported_rigs = import_pdx(REFERENCES[slot], skeleton=True)
        reference_meshes[slot] = meshes[0]
        reference_meshes[slot].name = f"CK3_REFERENCE_{slot}"
        move_to_collection(reference_meshes[slot], reference_collection)
        if len(imported_rigs) == 1:
            rigs[slot] = imported_rigs[0]
            rigs[slot].name = f"CK3_RIG_{slot}"
            move_to_collection(rigs[slot], reference_collection)
        elif slot == "legwear":
            # The importer reuses the already loaded body rig when the
            # embedded skeleton is identical, so no new armature is added.
            rigs[slot] = rigs["clothes"]
        else:
            raise RuntimeError(f"Expected one CK3 {slot} rig, got no armature")

    built: dict[str, bpy.types.Object] = {}
    for slot, component_rows in COMPONENTS.items():
        imported: list[bpy.types.Object] = []
        for component, rigid, shader in component_rows:
            source_name = f"{slot}_{component}.rigid_model_v2"
            source_path = args.source_dir / source_name
            if not source_path.is_file():
                raise RuntimeError(f"Missing staged source: {source_path}")
            obj = import_rmv2(source_path)
            obj.name = f"SOURCE_{slot}_{component}"
            original = obj.copy()
            original.data = obj.data.copy()
            original.name = f"ORIGINAL_{slot}_{component}"
            source_collection.objects.link(original)
            original.hide_set(True)
            original.hide_render = True

            if slot == "headgear":
                rigid_head_weights(obj)
            else:
                transfer_weights(obj, reference_meshes[slot])
                if rigid:
                    make_rigid_weights(obj)

            resource_name = RESOURCE_NAMES[slot]
            material = create_pdx_material(
                resource_name,
                shader,
                args.output_dir / resource_name,
                component,
            )
            obj.data.materials.clear()
            obj.data.materials.append(material)
            imported.append(obj)

        if slot == "headgear":
            reference_min, reference_max = bounds(reference_meshes[slot])
            helmet_min, helmet_max = bounds(imported[0])
            delta = (reference_min + reference_max - helmet_min - helmet_max) * 0.5
            for obj in imported:
                obj.location += delta
                apply_transform(obj)

        shape_name = f"{RESOURCE_NAMES[slot]}Shape"
        joined = join_components(imported, shape_name)
        bind_to_rig(joined, rigs[slot])
        move_to_collection(joined, export_collections[slot])
        built[slot] = joined
        print(
            "BASE_AUDIT",
            slot,
            mesh_audit(joined),
            weight_audit(joined, rigs[slot]),
            bounds(joined),
        )

    if args.inspect_only:
        bpy.ops.wm.save_as_mainfile(filepath=str(args.output_dir / "hd_historic_sabre_infantry_01_inspect.blend"))
        print("INSPECT_ONLY_OK")
        return

    for slot, mesh in built.items():
        resource_name = RESOURCE_NAMES[slot]
        slot_dir = args.output_dir / resource_name
        export_mesh(slot_dir / f"{resource_name}.mesh", mesh, rigs[slot])
        for morph_name, filename in REFERENCE_MORPHS[slot].items():
            morph_meshes, _ = import_pdx(morph_reference_path(slot, filename), skeleton=False)
            reference_morph = morph_meshes[0]
            duplicate = mesh.copy()
            duplicate.data = mesh.data.copy()
            bpy.context.scene.collection.objects.link(duplicate)
            duplicate.name = duplicate.data.name = f"{resource_name}_bs_{morph_name}Shape"
            duplicate.data["meshindex"] = 0
            for modifier in list(duplicate.modifiers):
                duplicate.modifiers.remove(modifier)
            apply_reference_delta(duplicate, reference_meshes[slot], reference_morph)
            mesh_audit(duplicate)
            export_mesh(slot_dir / f"{resource_name}_bs_{morph_name}.mesh", duplicate, None)
            bpy.data.objects.remove(duplicate, do_unlink=True)
            bpy.data.objects.remove(reference_morph, do_unlink=True)

    bpy.ops.wm.save_as_mainfile(
        filepath=str(args.output_dir / "hd_historic_sabre_infantry_01_master.blend")
    )
    print("BUILD_OK", args.output_dir)


if __name__ == "__main__":
    main()
