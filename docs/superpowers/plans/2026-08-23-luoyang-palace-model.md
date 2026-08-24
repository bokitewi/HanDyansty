# Luoyang Palace Model Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the authorized Luoyang FBX into a three-LOD CK3 special-building mesh and make only the mod's Luoyang building use it.

**Architecture:** A new self-contained `hd_luoyang_palace` resource owns the mesh and textures. The existing Luoyang special-building definition directly consumes its `pdxmesh`; existing locator, history, gameplay, and unrelated dirty work remain untouched.

**Tech Stack:** Blender 4.2.23 LTS, io_pdx_mesh, CK3 PDX mesh/asset format, Pillow DDS encoding, PowerShell static validation.

**Spec:** `docs/superpowers/specs/2026-08-23-luoyang-palace-model-design.md`

## Global Constraints

- The user authorized modification and public redistribution with the mod.
- Produce exactly three LOD indices.
- LOD0 retains all 14,866 source triangles and deletes no building structure.
- Do not launch CK3; runtime acceptance belongs to the user.
- Do not install additional software.
- Do not add a reusable model content generator to the mod.
- Do not commit because the user did not authorize a commit.
- Preserve all unrelated existing worktree changes.

---

### Task 1: Freeze Inputs and Establish the Failing Acceptance Baseline

**Files:**
- Read: `C:/Users/15550/Downloads/JDH5455714463_fbx.rar`
- Read: `D:/TEMP/hd_luoyang_model_20260823/source/3d66.com_JDH5455714463.fbx`
- Test: target resource paths and Luoyang asset reference

**Interfaces:**
- Consumes: approved source archive and design spec.
- Produces: immutable source hashes and a confirmed RED acceptance result.

- [ ] **Step 1: Recompute both source hashes**

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath 'C:\Users\15550\Downloads\JDH5455714463_fbx.rar'
Get-FileHash -Algorithm SHA256 -LiteralPath 'D:\TEMP\hd_luoyang_model_20260823\source\3d66.com_JDH5455714463.fbx'
```

Expected hashes are the exact values in the design spec.

- [ ] **Step 2: Run the acceptance probe before creating outputs**

```powershell
$target = 'gfx\models\buildings\special\hd_luoyang_palace'
if (-not (Test-Path "$target\hd_luoyang_palace.mesh")) { throw 'RED: target mesh is absent' }
rg -n 'hd_building_special_luoyang_palace_mesh' common/buildings/tk_special_buildings.txt
```

Expected: failure because the target mesh and reference are absent.

### Task 2: Normalize LOD0 and Fit the Existing Luoyang Locator Convention

**Files:**
- Read: source FBX
- Read: `D:/SteamLibrary/steamapps/common/Crusader Kings III/game/gfx/models/buildings/special/tgp/tgp_building_special_heian_kyo.mesh`
- Produce temporarily: `D:/TEMP/hd_luoyang_model_20260823/work/hd_luoyang_palace.blend`

**Interfaces:**
- Consumes: three source mesh objects and Heian LOD0 footprint/origin evidence.
- Produces: normalized LOD0 objects named `hd_luoyang_part_01_LOD0`,
  `hd_luoyang_part_02_LOD0`, and `hd_luoyang_part_03_LOD0`.

- [ ] **Step 1: Import and normalize the source**

Run Blender headlessly, clear the scene, import the FBX, preserve the three
mesh partitions and custom normals, then bake transforms.

- [ ] **Step 2: Apply the verified uniform fit**

Use the smaller horizontal ratio between the source and Heian main-building
footprints, align the main gate to the Heian forward axis, align the ground
plane, and translate the horizontal bounds center to the Heian pivot-relative
bounds center.

- [ ] **Step 3: Repair only the four zero UV records**

Copy the corresponding nonzero UV from the nearest matching polygon corner;
do not clamp, wrap, or repack any other UV.

- [ ] **Step 4: Save and inspect LOD0**

```powershell
& 'D:\SteamLibrary\steamapps\common\Blender\blender.exe' --background 'D:\TEMP\hd_luoyang_model_20260823\work\hd_luoyang_palace.blend' --python-expr "import bpy; print(sum(len(o.data.loop_triangles) for o in bpy.data.objects if o.type=='MESH' and '_LOD0' in o.name))"
```

Expected: `14866`, with three LOD0 mesh objects and identity object transforms.

### Task 3: Build Structure-Preserving LOD1 and LOD2

**Files:**
- Modify temporarily: `D:/TEMP/hd_luoyang_model_20260823/work/hd_luoyang_palace.blend`

**Interfaces:**
- Consumes: normalized LOD0 objects.
- Produces: three `LOD1` and three `LOD2` objects with matching origin,
  material, and placement.

- [ ] **Step 1: Duplicate LOD0 independently for each lower LOD**

Duplicate from LOD0 twice before simplification so LOD2 is not derived from
LOD1.

- [ ] **Step 2: Protect structural boundaries**

Mark UV seams, material boundaries, sharp edges, boundary edges, roof/eave
silhouettes, wall tops, gates, towers, pagoda tiers, and ground-contact edges
as non-collapsible.

- [ ] **Step 3: Simplify LOD1**

Apply topology-safe planar/angle reduction only to unprotected surface detail
until the combined result is between 8,000 and 10,000 triangles.

- [ ] **Step 4: Simplify LOD2 from the clean LOD0 duplicate**

Apply the same protected-boundary strategy with a stronger reduction until the
combined result is between 4,000 and 6,000 triangles.

- [ ] **Step 5: Verify all LOD contracts in Blender**

Print per-object and per-LOD triangle totals, bounds, transform matrices,
material slots, and UV-layer counts. Expected: 14,866 / 8,000-10,000 /
4,000-6,000 triangles and three objects per LOD.

### Task 4: Produce CK3-Compatible Textures

**Files:**
- Create: `gfx/models/buildings/special/hd_luoyang_palace/hd_luoyang_palace_diffuse.dds`
- Create: `gfx/models/buildings/special/hd_luoyang_palace/hd_luoyang_palace_normal.dds`
- Create: `gfx/models/buildings/special/hd_luoyang_palace/hd_luoyang_palace_properties.dds`

**Interfaces:**
- Consumes: packed source JPEG and verified neutral channel values.
- Produces: three decodable mipmapped DDS textures.

- [ ] **Step 1: Extract the packed diffuse without resampling the base level**

Write the 2048x2048 source pixels as BC3/DXT5 and append successively halved
BC3 mip payloads through 1x1, with a DDS header declaring the complete chain.

- [ ] **Step 2: Produce neutral support textures**

Create small mipmapped DDS textures using RGBA `(132,130,0,128)` for normal
and `(0,0,0,179)` for properties.

- [ ] **Step 3: Decode every mipmapped DDS**

Use Pillow to open each result and independently parse the DDS header.
Expected: BC3/DXT5, positive dimensions, valid payload size, and mip count
matching `floor(log2(max(width,height))) + 1`.

### Task 5: Export the PDX Mesh and Author the Asset Binding

**Files:**
- Create: `gfx/models/buildings/special/hd_luoyang_palace/hd_luoyang_palace.mesh`
- Create: `gfx/models/buildings/special/hd_luoyang_palace/hd_luoyang_palace.asset`

**Interfaces:**
- Consumes: nine Blender LOD objects and three DDS textures.
- Produces: `hd_building_special_luoyang_palace_mesh`.

- [ ] **Step 1: Export through io_pdx_mesh**

Export only the nine final mesh objects, with object transforms already baked
and with one material slot per source partition.

- [ ] **Step 2: Record the actual exported Shape names**

Round-trip the `.mesh` immediately and use the returned Shape names verbatim
in the asset file.

- [ ] **Step 3: Create the minimal `.asset`**

Define one `pdxmesh` named `hd_building_special_luoyang_palace_mesh`, file
`hd_luoyang_palace.mesh`, LOD index 1 at 20 percent, LOD index 2 at 10
percent, `cull_distance = 300`, and one `meshsettings` block per Shape using
the three Luoyang textures, `snap_to_terrain`, and `gfx/FX/pdxmesh.shader`.
Do not add an unused entity or a map-object registration.

### Task 6: Attach Only the Luoyang Special Building

**Files:**
- Modify: `common/buildings/tk_special_buildings.txt` in the
  `TK_20_21_LuoYangCheng` block only.

**Interfaces:**
- Consumes: `hd_building_special_luoyang_palace_mesh`.
- Produces: the final static special-building consumer chain.

- [ ] **Step 1: Change the single asset name**

Replace:

```txt
name = "tgp_building_special_heian_kyo_mesh"
```

with:

```txt
name = "hd_building_special_luoyang_palace_mesh"
```

inside `TK_20_21_LuoYangCheng`; leave every other line unchanged.

- [ ] **Step 2: Inspect the narrow diff**

```powershell
git diff -U5 -- common/buildings/tk_special_buildings.txt
```

Expected: the pre-existing unrelated deletions remain untouched and the only
new hunk changes the Luoyang mesh name.

### Task 7: Round-Trip, Static-Chain, and Visual Verification

**Files:**
- Read: all five new resource files and the modified building definition.
- Produce temporarily: `D:/TEMP/hd_luoyang_model_20260823/final_preview/*.png`

**Interfaces:**
- Consumes: complete offline implementation.
- Produces: machine-readable validation evidence and user-facing renders.

- [ ] **Step 1: PDX round-trip the final mesh**

Import the exported `.mesh` into an empty Blender scene and print Shape count,
LOD index, triangle count, PDX vertex count, bounds, UV validity, index
validity, and finite-value checks.

- [ ] **Step 2: Validate the asset and texture bindings**

Assert every `meshsettings.name` exists in the round-trip Shapes, all texture
files exist and decode, shader names match the spec, and LOD/cull values are
exact.

- [ ] **Step 3: Validate the CK3 consumer chain**

Assert exactly one definition of `TK_20_21_LuoYangCheng`, exactly one new
Luoyang `pdxmesh`, and that the building's name resolves to that mesh and its
local `.mesh` file.

- [ ] **Step 4: Render comparison previews**

Render matching oblique, front, and top views for LOD0, LOD1, and LOD2 using
the source diffuse and identical camera/light settings.

- [ ] **Step 5: Audit the approved edit boundary**

Use targeted hashes and `git diff`/`git status` to distinguish the new work
from pre-existing dirty changes. Confirm no locator, history, gameplay
modifier, other city asset, vanilla file, or unrelated worktree content was
modified by this implementation.

- [ ] **Step 6: Report the runtime boundary**

Deliver the offline results and preview paths, then list placement, terrain
fit, forward direction, LOD transitions, and log cleanliness as checks the
user must perform when they launch CK3.
