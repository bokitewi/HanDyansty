# Luoyang Palace Model Design

## Objective

Convert the authorized external FBX archive at
`C:/Users/15550/Downloads/JDH5455714463_fbx.rar` into a project-owned CK3
map special-building resource and make only `TK_20_21_LuoYangCheng` consume
it.

The user will perform all CK3 runtime testing. Codex must not launch the game.

## Source Evidence

- Archive SHA-256: `AAE41BF4B23F40A0EE8C357761019F8FC3A31CE5285F592CD00EE89C1D5FDAA9`
- FBX SHA-256: `12F57104DB22103944114880861CDD79AC73C309755BD3E7C8599B42473411C7`
- FBX payload: `3d66.com_JDH5455714463.fbx`
- Three mesh objects, 28,041 Blender vertices, and 14,866 triangles.
- One opaque 2048x2048 embedded JPEG diffuse texture.
- No armature, animation, camera, or light is required for the CK3 resource.
- The user confirmed authorization to modify and publicly redistribute the
  model as part of the mod.

## Chosen Architecture

Use a new project-owned `pdxmesh` named
`hd_building_special_luoyang_palace_mesh`. Do not override the vanilla
Heian resource. Change only the `asset.name` field of
`TK_20_21_LuoYangCheng` to point to the new mesh.

The existing province 787 special-building locator remains the placement
authority. The vanilla Heian consumer chain proves that a building definition
can consume a `pdxmesh` directly, so no new static `map_object_data` object or
locator is added.

## Files

Create under `gfx/models/buildings/special/hd_luoyang_palace/`:

- `hd_luoyang_palace.mesh`
- `hd_luoyang_palace.asset`
- `hd_luoyang_palace_diffuse.dds`
- `hd_luoyang_palace_normal.dds`
- `hd_luoyang_palace_properties.dds`

Modify only the Luoyang asset reference in:

- `common/buildings/tk_special_buildings.txt`

Do not modify province or title history, locator data, building modifiers,
localization, vanilla resources, or any other city model.

## Geometry and Placement

- Bake the imported `0.01` object scale and all orientation transforms.
- Keep the three source mesh partitions instead of globally joining or
  welding them.
- Use uniform scaling only.
- Match the usable footprint, forward direction, ground plane, and deliberate
  horizontal pivot offset of the current Heian Palace analogue so the existing
  Luoyang locator remains valid.
- Preserve source UV tiling outside the `0..1` interval.
- Repair only the four detected zero UV records in the second source mesh;
  do not repack the atlas.
- Do not globally merge by distance, voxel-remesh, delete loose components,
  or globally recalculate custom normals.

## LOD Contract

The final mesh contains three LOD indices. Each LOD contains the same three
logical source partitions.

### LOD0

- Retain exactly all 14,866 source triangles.
- Delete no building structure.
- Preserve every wall, gate, gate tower, corner tower, hall, courtyard,
  subsidiary building, pagoda tier, roof, eave, and ridge.

### LOD1

- Target 8,000 to 10,000 triangles.
- Preserve the complete city footprint, building count, compound divisions,
  major roofs, walls, gates, towers, and ground contacts.
- Simplify only surface details that cannot affect the readable mid-distance
  silhouette.

### LOD2

- Target 4,000 to 6,000 triangles.
- Preserve the outer wall, gates, corner towers, main palace, major building
  groups, pagoda silhouette, roof tiers, compound divisions, and ground
  contacts.
- Remove only distant micro-detail.

LOD1 and LOD2 are derived independently from the normalized LOD0 source, not
cascaded from one another. The three LODs must share origin, scale, material,
forward direction, and bounds closely enough to avoid visible jumps.

## Material Contract

- Use `snap_to_terrain` with `gfx/FX/pdxmesh.shader`.
- Do not use transparency or alpha-to-coverage.
- Convert the source diffuse to mipmapped BC3/DXT5 DDS without changing its
  UV layout or color design.
- Use a neutral RRxG normal texture with encoded channels equivalent to
  R=132, G=130, B=0, A=128.
- Use a neutral properties texture with R=0, G=0, B=0, A=179.
- LOD0, LOD1, and LOD2 share the same texture set.
- Use the vanilla-equivalent LOD thresholds: index 1 at 20 percent and index 2
  at 10 percent; use `cull_distance = 300`.

## Validation Contract

Offline completion requires all of the following:

1. A pre-implementation acceptance check fails because the target resource
   files and Luoyang reference do not yet exist.
2. LOD0 round-trips through `io_pdx_mesh` with exactly 14,866 triangles and
   all three partitions present.
3. LOD1 and LOD2 triangle totals fall within their specified ranges.
4. The exported `.mesh` round-trips with three LOD indices and nine expected
   Shapes, with legal indices, finite positions/normals/UVs, and no Shape over
   the CK3 vertex limit.
5. All three LODs have consistent placement transforms and valid UVs.
6. Every DDS has the intended dimensions, compression, and a complete mip
   chain and can be decoded.
7. Every `.asset` Shape name exists in the round-tripped `.mesh` and references
   the intended textures and shader.
8. The static consumer chain resolves as
   `TK_20_21_LuoYangCheng -> hd_building_special_luoyang_palace_mesh -> hd_luoyang_palace.mesh -> DDS textures`.
9. A targeted diff shows no edits outside the approved files, apart from this
   design and its implementation plan.
10. Offline renders are produced for all three LODs so the user can inspect
    the structure and silhouette before their own game launch.

Runtime placement, terrain interaction, LOD transition appearance, and final
in-game visual acceptance remain explicitly unverified until the user launches
CK3.
