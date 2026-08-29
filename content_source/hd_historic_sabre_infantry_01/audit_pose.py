"""Representative offline pose audit for the master Blender build."""

from __future__ import annotations

import math

import bpy


TESTS = {
    "m_headgear_hd_historic_sabre_infantry_01Shape": ["bn_h_head"],
    "m_clothes_hd_historic_sabre_infantry_01Shape": [
        "bn_l_shoulder",
        "bn_l_elbow",
        "bn_l_forearm",
        "bn_l_hip",
        "bn_sp_cervical",
    ],
    "m_legwear_hd_historic_sabre_infantry_01Shape": [
        "bn_l_hip",
        "bn_l_knee",
        "bn_l_ankle",
        "bn_l_ftBall",
    ],
}


def evaluated_positions(obj: bpy.types.Object) -> list:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    positions = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    evaluated.to_mesh_clear()
    return positions


def side_vertices(obj: bpy.types.Object, prefix: str) -> set[int]:
    group_indices = {group.index for group in obj.vertex_groups if group.name.startswith(prefix)}
    return {
        vertex.index
        for vertex in obj.data.vertices
        if any(assignment.group in group_indices and assignment.weight > 1e-6 for assignment in vertex.groups)
    }


def main() -> None:
    for mesh_name, bones in TESTS.items():
        obj = bpy.data.objects.get(mesh_name.removesuffix("Shape"))
        if obj is None:
            obj = next(
                (candidate for candidate in bpy.data.objects if candidate.data and candidate.data.name == mesh_name),
                None,
            )
        if obj is None:
            raise RuntimeError(f"Missing export mesh: {mesh_name}")
        armature_modifiers = [modifier for modifier in obj.modifiers if modifier.type == "ARMATURE"]
        if len(armature_modifiers) != 1:
            raise RuntimeError(f"Expected one armature modifier: {mesh_name}")
        rig = armature_modifiers[0].object
        left = side_vertices(obj, "bn_l_")
        right = side_vertices(obj, "bn_r_")
        for bone_name in bones:
            pose_bone = rig.pose.bones.get(bone_name)
            if pose_bone is None:
                raise RuntimeError(f"Missing pose bone {bone_name} on {mesh_name}")
            before = evaluated_positions(obj)
            pose_bone.rotation_mode = "XYZ"
            pose_bone.rotation_euler.y = math.radians(15.0)
            bpy.context.view_layer.update()
            after = evaluated_positions(obj)
            displacement = [(after[index] - before[index]).length for index in range(len(before))]
            moved = [value for value in displacement if value > 1e-5]
            if not moved:
                raise RuntimeError(f"Pose did not move geometry: {mesh_name}/{bone_name}")
            if bone_name.startswith("bn_l_") and left:
                left_max = max(displacement[index] for index in left)
                right_only = right - left
                right_max = max((displacement[index] for index in right_only), default=0.0)
                if left_max <= 1e-4 or right_max > 1e-3:
                    raise RuntimeError(
                        f"Side contamination {mesh_name}/{bone_name}: left={left_max} right={right_max}"
                    )
            else:
                left_max = max(moved)
                right_max = 0.0
            print(
                "POSE_OK",
                mesh_name,
                bone_name,
                f"moved={len(moved)}",
                f"max={max(moved):.6f}",
                f"left_max={left_max:.6f}",
                f"opposite_max={right_max:.6f}",
            )
            pose_bone.rotation_euler = (0.0, 0.0, 0.0)
            bpy.context.view_layer.update()
    print("POSE_AUDIT_OK")


if __name__ == "__main__":
    main()
