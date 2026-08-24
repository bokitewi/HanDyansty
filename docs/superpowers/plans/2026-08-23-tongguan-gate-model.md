# Tongguan Gate Model Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the authorized Tongguan FBX into a three-LOD CK3 special-building mesh and make only the mod's Tongguan building use it.

**Architecture:** A new self-contained `hd_tongguan_gate` resource owns one Shape per LOD and three local textures. The existing `TK_20_36_TongGuan` definition directly consumes the new `pdxmesh`; existing locator, history, gameplay, and unrelated dirty work remain untouched.

**Tech Stack:** Blender 4.2.23 LTS, current `io_pdx_mesh`, CK3 PDX mesh/asset format, Pillow DDS encoding, PowerShell static validation.

**Spec:** `docs/superpowers/specs/2026-08-23-tongguan-gate-model-design.md`

## Global Constraints

- The user authorized modification and public redistribution with the mod.
- Produce exactly three real LOD indices.
- LOD0 retains all 4,020 source triangles and deletes no building structure.
- LOD1 target is 2,600-3,000 triangles; LOD2 target is 1,200-1,600.
- Use the approved Luoyang material, LOD-threshold, culling, isolation, and runtime-test options.
- Do not launch CK3; runtime acceptance belongs to the user.
- Do not install software, add a reusable content generator, or commit.
- Preserve every unrelated existing worktree change.

---

### Task 1: Freeze Inputs and Establish the RED Baseline

**Files:**
- Read: `C:/Users/15550/Downloads/JEH5455812520_fbx.rar`
- Read: `C:/Users/15550/AppData/Local/Temp/hd_tongguan_audit_20260823_191431/3d66.com_JEH5455812520.fbx`
- Test: target resource paths and `TK_20_36_TongGuan` reference

**Interfaces:**
- Consumes: approved source archive and design spec.
- Produces: immutable source hashes, target-file baseline, and an exact backup/hash record of the overlapping building file.

- [ ] Recompute the archive and FBX SHA-256 values and require the exact hashes from the spec.
- [ ] Record the current SHA-256 of `common/buildings/tk_special_buildings.txt` and its current targeted Git diff.
- [ ] Run the acceptance probe and observe RED because `gfx/models/buildings/special/hd_tongguan_gate/hd_tongguan_gate.mesh` and the new consumer reference are absent.
- [ ] Create a new staging tree at `D:/TEMP/hd_tongguan_model_20260823/` without deleting or overwriting any existing path.

### Task 2: Normalize the Structurally Complete LOD0

**Files:**
- Read: source FBX.
- Read: installed `ep3_cilician_gates.mesh` and `.asset`.
- Create temporarily: `D:/TEMP/hd_tongguan_model_20260823/work/hd_tongguan_gate.blend`.

**Interfaces:**
- Consumes: one source mesh, source diffuse, and installed Cilician building-Shape bounds.
- Produces: `hd_tongguan_gate_LOD0` with identity object transforms and exactly 4,020 triangles.

- [ ] Import the FBX, snapshot the final source matrix, preserve its evaluated mesh and custom normals, and remove camera/empty/action data.
- [ ] Bake the source transform exactly once, then normalize using the source architectural axes.
- [ ] Apply a uniform scale of approximately `4.541` so the model height matches the installed Cilician building Shape.
- [ ] Translate the horizontal center to approximately `(2.063370,-1.577291)` and the base to approximately `Z=-0.334562`.
- [ ] Keep the original UVs, all source triangles, all disconnected architectural components, and one material slot.
- [ ] Save the working Blender file and assert exactly one LOD0 mesh, 4,020 triangles, finite data, nonzero UV triangle areas, expected bounds, and identity transforms.

### Task 3: Build Independent LOD1 and LOD2

**Files:**
- Modify temporarily: `D:/TEMP/hd_tongguan_model_20260823/work/hd_tongguan_gate.blend`.

**Interfaces:**
- Consumes: normalized LOD0.
- Produces: `hd_tongguan_gate_LOD1` and `hd_tongguan_gate_LOD2` with matching origin/material and protected structural silhouettes.

- [ ] Duplicate normalized LOD0 independently for LOD1 and LOD2 before simplification.
- [ ] Protect boundaries, UV seams, sharp edges, ground contacts, gate opening, wall ends/tops, roof/eave silhouettes, towers, battlements, and railings.
- [ ] Simplify LOD1 conservatively to 2,600-3,000 triangles without deleting any major architectural component.
- [ ] Simplify LOD2 independently to 1,200-1,600 triangles while retaining both wall wings, gate opening, gatehouse, towers, roofs, major battlements, and ground contacts.
- [ ] Validate per-LOD triangles, finite data, nonzero UV triangle areas, one material, identity transforms, and closely matched bounds; render pre-export front/oblique/top comparisons.

### Task 4: Produce Three CK3-Compatible DDS Textures

**Files:**
- Create: `gfx/models/buildings/special/hd_tongguan_gate/hd_tongguan_gate_diffuse.dds`
- Create: `gfx/models/buildings/special/hd_tongguan_gate/hd_tongguan_gate_normal.dds`
- Create: `gfx/models/buildings/special/hd_tongguan_gate/hd_tongguan_gate_properties.dds`

**Interfaces:**
- Consumes: the packed 2048x2048 source diffuse and approved neutral channel values.
- Produces: three decodable BC3/DXT5 textures with complete mip chains.

- [ ] Extract the packed source diffuse without changing the 2048x2048 base pixels or UV layout.
- [ ] Encode the diffuse as BC3/DXT5 with 12 mip levels through 1x1.
- [ ] Encode the normal texture with RGBA `(132,130,0,128)` and the properties texture with `(0,0,0,179)`, both as small BC3/DXT5 complete-mip DDS files.
- [ ] Parse every DDS header and payload independently; decode with Pillow and verify dimensions, format, mip count, alpha range, and neutral base channels.

### Task 5: Export and Round-Trip the PDX Mesh

**Files:**
- Create: `gfx/models/buildings/special/hd_tongguan_gate/hd_tongguan_gate.mesh`
- Create: `gfx/models/buildings/special/hd_tongguan_gate/hd_tongguan_gate.asset`

**Interfaces:**
- Consumes: three final Blender LOD objects and three DDS textures.
- Produces: project-owned `hd_building_special_tongguan_gate_mesh`.

- [ ] Export only the three final mesh objects through the current `io_pdx_mesh` exporter.
- [ ] Re-import the produced `.mesh` immediately with `io_pdx_mesh` and record actual Shape names, LOD indices, triangles, PDX vertices, bounds, and UV data.
- [ ] Require LOD0 to round-trip at exactly 4,020 triangles and require all Shape/index/finite/nonzero-UV checks to pass.
- [ ] Author the `.asset` from the actual round-tripped Shape names with `snap_to_terrain`, `gfx/FX/pdxmesh.shader`, the three local DDS files, LOD percentages 20/10, and `cull_distance=300`.
- [ ] Add no entity or map-object registration.

### Task 6: Attach Only the Tongguan Special Building

**Files:**
- Modify: `common/buildings/tk_special_buildings.txt` only inside `TK_20_36_TongGuan`.

**Interfaces:**
- Consumes: `hd_building_special_tongguan_gate_mesh`.
- Produces: the final special-building consumer chain.

- [ ] Replace only `name = "ep3_cilician_gates_mesh"` with `name = "hd_building_special_tongguan_gate_mesh"` inside `TK_20_36_TongGuan` using a narrow direct patch.
- [ ] Inspect the targeted diff and prove every pre-existing unrelated hunk remains untouched.
- [ ] Verify no other Tongguan/pass/city definition consumes the new key.

### Task 7: Final Offline Acceptance

**Files:**
- Read: the five new resources and modified building definition.
- Create temporarily: `D:/TEMP/hd_tongguan_model_20260823/final_preview/*.png` and validation reports.

**Interfaces:**
- Consumes: complete offline implementation.
- Produces: machine-verifiable results and user-facing renders.

- [ ] Round-trip the final `.mesh` in a fresh Blender process and record per-Shape/LOD counts, largest PDX Shape vertex count, bounds, transforms, indices, finite values, UV areas, and materials.
- [ ] Parse the `.asset`; assert exact one-to-one Shape bindings, local texture existence, shader values, LOD percentages, and cull distance.
- [ ] Resolve the static chain `TK_20_36_TongGuan -> hd_building_special_tongguan_gate_mesh -> hd_tongguan_gate.mesh -> three DDS textures`.
- [ ] Render matching front, oblique, and top views from the final round-tripped LOD0, LOD1, and LOD2.
- [ ] Compare source, pre-export, and round-trip silhouettes; require both wall wings, gate, gatehouse, towers, roofs, and ground contacts in every required LOD.
- [ ] Run `git diff --check`, targeted hashes/status, duplicate-key/reference checks, and an approved-boundary audit.
- [ ] Report that CK3 was not launched and leave placement, terrain deformation, LOD transitions, culling, and fresh runtime log cleanliness to the user's in-game test.
