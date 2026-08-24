# Tongguan Gate Model Design

## Objective

Convert the authorized external FBX archive at
`C:/Users/15550/Downloads/JEH5455812520_fbx.rar` into a project-owned CK3
map special-building resource and make only `TK_20_36_TongGuan` consume it.

The production choices follow the previously approved Luoyang import:
three real LODs, a structurally complete LOD0, an isolated project resource,
one narrow building-reference change, no locator change, and user-owned CK3
runtime testing. Codex must not launch the game.

## Source Evidence

- Archive SHA-256:
  `44C5E2803910D51420351760CFE4405C43BAF3D60032E8276E424F19011D1D05`
- FBX SHA-256:
  `09F96B33AE29799CC49374D5A7B2228C97919912A0C0046E45EEED216355E7EC`
- FBX payload: `3d66.com_JEH5455812520.fbx`
- One mesh object, 6,952 Blender vertices, and 4,020 triangles.
- One opaque 2048x2048 embedded JPEG diffuse texture.
- One UV set with zero zero-area UV triangles. Twenty loop UV coordinates
  extend no more than approximately `0.0011` beyond `U=1`; preserve them as
  source-authored tiling rather than clamp or repack them.
- No armature is present. The imported camera, empty, and zero-frame transform
  actions are export-scene data and are not part of the CK3 resource.
- Local source bounds are approximately `2.802122 x 0.625617 x 1.038016`.
  The local horizontal center is effectively zero and the wall base is at
  local height zero.
- The user confirmed authorization to modify and publicly redistribute the
  model as part of the mod.

## Installed-Version Evidence

`TK_20_36_TongGuan` currently consumes `ep3_cilician_gates_mesh` directly as
a `pdxmesh`. The installed CK3 resource is:

`D:/SteamLibrary/steamapps/common/Crusader Kings III/game/gfx/models/buildings/special/ep3_cilician_gates/ep3_cilician_gates.asset`

The vanilla asset proves the dynamic special-building direct-consumer chain.
Its building Shape has approximately these round-tripped bounds:

- size: `14.283869 x 7.497528 x 4.714656`;
- center: `2.063370, -1.577291, 2.022767`;
- ground minimum: `Z=-0.334562`.

Province history assigns `TK_20_36_TongGuan` to province 849. The existing
special-building locator with ID 849 remains the placement and rotation
authority. Its current map position lies on the province 848/849 border; that
existing map placement is intentionally left unchanged.

## Chosen Architecture

Create one project-owned `pdxmesh` named
`hd_building_special_tongguan_gate_mesh`. Do not override or alter the
vanilla Cilician Gates resource. Change only the `asset.name` field of
`TK_20_36_TongGuan` to point to the new mesh.

Do not add a static `map_object_data` object, duplicate locator, entity,
component, or state layer. Do not change the existing province/title history,
holding, special-building state, modifiers, localization, or locator.

## Files

Create under `gfx/models/buildings/special/hd_tongguan_gate/`:

- `hd_tongguan_gate.mesh`
- `hd_tongguan_gate.asset`
- `hd_tongguan_gate_diffuse.dds`
- `hd_tongguan_gate_normal.dds`
- `hd_tongguan_gate_properties.dds`

Modify only the Tongguan asset reference in:

- `common/buildings/tk_special_buildings.txt`

The design document and implementation plan are the only additional project
files permitted. Temporary Blender scenes, audit reports, and renders stay
outside the mod in `D:/TEMP/hd_tongguan_model_20260823/`.

## Geometry, Orientation, and Placement

- Snapshot and bake the imported mesh transform exactly once, then remove the
  source camera, empty, and zero-frame animation data.
- Preserve the single logical source mesh partition. Do not globally merge by
  distance, voxel-remesh, remove loose components, fill openings, or delete
  hidden faces from LOD0.
- Keep the source architectural orientation: the wall spans local X, the gate
  passage runs along local Y, height is local Z, and the principal facade
  faces local negative Y. The existing locator quaternion supplies the map
  rotation.
- Use a uniform fit derived from the vanilla Cilician building Shape. Match
  the source height to the analogue height, giving a uniform scale of
  approximately `4.541`. The expected normalized dimensions are about
  `12.72 x 2.84 x 4.71`.
- Align the normalized gate center to the analogue building-Shape horizontal
  center near `X=2.063370, Y=-1.577291`, and align its base near
  `Z=-0.334562`. This preserves the current Tongguan locator convention and
  leaves a small terrain-embedding margin.
- Bake all final transforms. Every exported object must have identity
  location, rotation, and scale.
- Preserve the source UV layout and custom normals for LOD0. Triangulate
  deterministically and require finite positions, normals, and UVs.

## LOD Contract

The final mesh contains exactly three LOD indices and one logical Shape per
LOD. LOD1 and LOD2 are generated independently from the normalized LOD0
source, not cascaded from one another.

### LOD0

- Retain exactly all 4,020 source triangles.
- Delete no architectural structure.
- Preserve both wall wings, the central gate opening and doors, the complete
  gatehouse, both towers, all roofs and eaves, railings, braces, foundations,
  wall faces, battlements, and readable decorative silhouette.

### LOD1

- Target 2,600 to 3,000 triangles.
- Preserve the complete wall span, central gate opening, both towers,
  gatehouse, major roofs/eaves, battlement rhythm, and ground contacts.
- Simplify only surface and repeated micro-detail that does not change the
  mid-distance silhouette.

### LOD2

- Target 1,200 to 1,600 triangles.
- Preserve both wall wings, gate opening, gatehouse mass, both towers, roof
  silhouettes, major battlements, and ground contacts.
- Remove only distant micro-detail. If a target conflicts with the protected
  silhouette, structural preservation takes priority and the measured higher
  triangle count must be reported rather than deleting a whole structure.

The three LODs share the same origin, scale, material, forward direction, and
closely matching bounds so transitions do not jump.

## Material Contract

Follow the approved Luoyang material options:

- Use `snap_to_terrain` with `gfx/FX/pdxmesh.shader` for all three Shapes.
- Do not use transparency, alpha-to-coverage, decals, or two-sided materials.
- Convert the embedded diffuse to mipmapped BC3/DXT5 DDS without changing its
  UV layout, color design, or 2048x2048 base level.
- Use a small mipmapped neutral RRxG normal DDS with encoded channels
  equivalent to `R=132, G=130, B=0, A=128`.
- Use a small mipmapped neutral properties DDS with
  `R=0, G=0, B=0, A=179`.
- LOD0, LOD1, and LOD2 share the same three texture files.
- Use LOD index 1 at 20 percent, LOD index 2 at 10 percent, and
  `cull_distance = 300`.

The source material is genuinely opaque: its embedded JPEG has no alpha
channel and Blender reports decoded alpha exactly `1.0` everywhere.

## Approved Edit Boundary

Allowed production changes:

1. Five new files under
   `gfx/models/buildings/special/hd_tongguan_gate/`.
2. One `asset.name` replacement inside the existing
   `TK_20_36_TongGuan` block.
3. This design document and its implementation plan.

Forbidden changes include locator files, province/title history, holding
definitions, modifiers, localization, any other pass or city building,
vanilla resources, and unrelated dirty work. Do not commit because the user
did not authorize a commit.

## Validation Contract

Offline completion requires all of the following:

1. A pre-implementation acceptance probe fails because the Tongguan resource
   and new consumer reference do not yet exist.
2. Source archive and FBX hashes exactly match this specification.
3. LOD0 round-trips through the current `io_pdx_mesh` with exactly 4,020
   triangles and the complete source structure.
4. LOD1 and LOD2 satisfy their triangle ranges unless the protected-silhouette
   exception is triggered and documented with measured evidence.
5. The exported mesh round-trips with exactly three LOD indices and three
   expected Shapes, legal indices, finite values, nonzero UV triangle area,
   no negative transforms, and no Shape near the verified exporter limit.
6. Round-tripped LOD bounds and origins remain consistent enough to prevent
   placement jumps.
7. Every DDS decodes, reports BC3/DXT5, has the intended dimensions and
   channels, and contains a complete mip chain through 1x1.
8. Every `.asset` Shape name exists exactly once in the round-tripped mesh and
   references the intended textures, shader, LOD thresholds, and cull value.
9. The static consumer chain resolves as
   `TK_20_36_TongGuan -> hd_building_special_tongguan_gate_mesh -> hd_tongguan_gate.mesh -> three local DDS textures`.
10. A targeted diff confirms no edits beyond the approved production files,
    design, and implementation plan.
11. Matching front, oblique, and top previews are produced for all three LODs
    after the final PDX round trip.

Runtime placement, terrain deformation under `snap_to_terrain`, final scale,
forward direction, LOD transition appearance, visibility/culling, and fresh
runtime log cleanliness remain explicitly unverified until the user launches
CK3.
