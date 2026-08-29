"""Offline PDX round-trip audit for the three portrait resources."""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import bpy


PDX_ADDON_ROOT = Path(
    r"E:\documents\Paradox Interactive\Crusader Kings III\mod\tools\third_party"
    r"\io_pdx_mesh\0.91\official_release"
)

RESOURCES = {
    "headgear": ("m_headgear_hd_historic_sabre_infantry_01", ["fat"], 2, 2379),
    "clothes": (
        "m_clothes_hd_historic_sabre_infantry_01",
        ["fat", "gaunt", "musc", "old", "dwarf"],
        13,
        8572,
    ),
    "legwear": (
        "m_legwear_hd_historic_sabre_infantry_01",
        ["fat", "gaunt", "musc", "old", "dwarf", "clothed"],
        2,
        1685,
    ),
}


def args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-dir", type=Path, required=True)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])


def reset() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for material in list(bpy.data.materials):
        bpy.data.materials.remove(material)


def import_mesh(path: Path, skeleton: bool) -> tuple[list[bpy.types.Object], bpy.types.Object | None]:
    before = set(bpy.data.objects)
    result = bpy.ops.io_pdx_mesh.import_mesh(
        filepath=str(path),
        chk_mesh=True,
        chk_skel=skeleton,
        chk_locs=False,
        chk_joinmats=False,
        chk_bonespace=False,
    )
    if result != {"FINISHED"}:
        raise RuntimeError(f"Import failed: {path}")
    added = [obj for obj in bpy.data.objects if obj not in before]
    meshes = [obj for obj in added if obj.type == "MESH"]
    rigs = [obj for obj in added if obj.type == "ARMATURE"]
    if not meshes or (skeleton and len(rigs) != 1):
        raise RuntimeError(f"Unexpected objects: {path}: meshes={len(meshes)} rigs={len(rigs)}")
    return meshes, rigs[0] if rigs else None


def audit_skin(mesh: bpy.types.Object, rig: bpy.types.Object) -> dict[str, object]:
    bones = set(rig.data.bones.keys())
    used: set[str] = set()
    zero = over = unnormalised = 0
    for vertex in mesh.data.vertices:
        weights = [item for item in vertex.groups if item.weight > 1e-6]
        zero += not weights
        over += len(weights) > 4
        unnormalised += weights and abs(sum(item.weight for item in weights) - 1.0) > 1e-4
        used.update(mesh.vertex_groups[item.group].name for item in weights)
    missing = sorted(used - bones)
    if zero or over or unnormalised or missing:
        raise RuntimeError(
            f"Skin failed: zero={zero} over={over} unnormalised={unnormalised} missing={missing}"
        )
    return {"bones": sorted(used), "bone_count": len(used)}


def topology(mesh: bpy.types.Object) -> tuple[int, int]:
    mesh.data.calc_loop_triangles()
    if not mesh.data.uv_layers.active:
        raise RuntimeError(f"No UV: {mesh.name}")
    if any(not math.isfinite(value) for vertex in mesh.data.vertices for value in vertex.co):
        raise RuntimeError(f"Non-finite position: {mesh.name}")
    return len(mesh.data.vertices), len(mesh.data.loop_triangles)


def main() -> None:
    parsed = args()
    sys.path.insert(0, str(PDX_ADDON_ROOT))
    import io_pdx_mesh

    io_pdx_mesh.register()
    for slot, (resource, morphs, material_count, triangle_count) in RESOURCES.items():
        reset()
        directory = parsed.build_dir / resource
        base_meshes, rig = import_mesh(directory / f"{resource}.mesh", True)
        base_topology = [topology(mesh) for mesh in base_meshes]
        vertices = sum(item[0] for item in base_topology)
        triangles = sum(item[1] for item in base_topology)
        if triangles != triangle_count or len(base_meshes) != material_count:
            raise RuntimeError(
                f"Base topology/material mismatch for {slot}: vertices={vertices} "
                f"triangles={triangles} materials={len(base_meshes)}"
            )
        if any(not mesh.data.name.startswith(f"{resource}Shape") for mesh in base_meshes):
            raise RuntimeError(
                f"Shape name mismatch for {slot}: {[mesh.data.name for mesh in base_meshes]}"
            )
        if any(mesh.data.get("meshindex") != 0 for mesh in base_meshes):
            raise RuntimeError(f"Shape index mismatch for {slot}")
        material_order = [
            mesh.data.materials[0].name.removeprefix("PDXmat_") for mesh in base_meshes
        ]
        skin = [audit_skin(mesh, rig) for mesh in base_meshes]
        base_positions = [
            [vertex.co.copy() for vertex in mesh.data.vertices] for mesh in base_meshes
        ]
        print(
            "ROUNDTRIP_BASE_OK",
            slot,
            f"vertices={vertices}",
            f"triangles={triangles}",
            f"materials={material_order}",
            f"skin={skin}",
        )
        for morph in morphs:
            morph_meshes, _ = import_mesh(directory / f"{resource}_bs_{morph}.mesh", False)
            morph_topology = [topology(mesh) for mesh in morph_meshes]
            morph_vertices = sum(item[0] for item in morph_topology)
            morph_triangles = sum(item[1] for item in morph_topology)
            if morph_topology != base_topology:
                raise RuntimeError(
                    f"Morph topology mismatch {slot}/{morph}: "
                    f"{morph_topology} != {base_topology}"
                )
            displacement = sum(
                (vertex.co - base_positions[mesh_index][vertex_index]).length
                for mesh_index, mesh in enumerate(morph_meshes)
                for vertex_index, vertex in enumerate(mesh.data.vertices)
            )
            if displacement <= 1e-4:
                raise RuntimeError(f"Empty morph: {slot}/{morph}")
            print(
                "ROUNDTRIP_MORPH_OK",
                slot,
                morph,
                f"vertices={morph_vertices}",
                f"triangles={morph_triangles}",
                f"displacement_sum={displacement:.6f}",
            )
            for morph_mesh in morph_meshes:
                bpy.data.objects.remove(morph_mesh, do_unlink=True)
    print("ROUNDTRIP_AUDIT_OK")


if __name__ == "__main__":
    main()
