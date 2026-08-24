# Historical Revolts Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair the nine approved post-Yellow-Turban forced uprising wars so every uprising uses the locked data, legal current-ruler targets, formal war objectives, fixed troops, one-shot lifecycle, and clean localization.

**Architecture:** Keep Phase 1 as a narrow monthly on_action plus nine character events. Shared scripted triggers resolve eligibility; shared effects resolve the defender, formal targets, leaders, war, and bound armies. A PowerShell structural test reads the actual CK3 scripts and fails on every known regression before production edits are made.

**Tech Stack:** CK3 1.19.0.6 P language, YAML localization, PowerShell 7-compatible static tests, installed vanilla scripts as schema evidence.

**Spec:** `docs/superpowers/specs/2026-08-23-historical-event-chain-phase1-phase2-design.md`

## Global Constraints

- Exactly nine uprisings; do not add story cycles or unrelated narrative content.
- Dates are exclusive windows, not historical backfill.
- Defender is the current top ruler; only titles owned by that defender may be formal targets.
- Fixed troop compositions; start the war before spawning war-bound armies.
- Preserve user dirty work and restrict edits to the listed Phase 1 files and tests.
- Do not launch CK3 until separate runtime authorization is obtained.
- Do not add Python content generators.

---

### Task 1: Phase 1 structural regression test

**Files:**
- Create: `tools/tests/test_hd_historical_revolts.ps1`
- Read: `events/zz_hd_historical_revolt_events.txt`
- Read: `common/scripted_triggers/zz_hd_historical_revolt_triggers.txt`
- Read: `common/scripted_effects/zz_hd_historical_revolt_effects.txt`
- Read: `common/casus_belli_types/zz_hd_historical_revolt_cb.txt`
- Read: `common/culture/name_lists/zz_hd_historical_revolt_names.txt`

**Interfaces:**
- Consumes: the eight Phase 1 production files named in the design.
- Produces: a nonzero exit status with individual assertion names; later tasks use it as their RED/GREEN gate.

- [ ] **Step 1: Create assertions for the locked surface**

The script loads production files with `Get-Content -Raw`, defines `Assert-True`, `Assert-MatchCount`, and `Assert-NotMatch`, then checks: nine event IDs, nine fired flags, nine window pairs, no `holder ?= { is_alive`, no `dynasty = generate`, no empty custom name list, `top_liege` use, repeated `target_title` support, every fixed troop total, `uses_supply = yes`, `inheritable = no`, `war = scope:war`, and no siege regiment.

- [ ] **Step 2: Run the test and verify RED**

Run:

```powershell
pwsh -NoProfile -File tools/tests/test_hd_historical_revolts.ps1
```

Expected: FAIL reports at least the effect-context error, generated anonymous dynasties, absent top-ruler resolution, broken name list, and locked-data mismatches.

- [ ] **Step 3: Confirm failures name production defects**

Each failure must print `FAIL: <requirement>` and the script must exit `1`; syntax errors in the test are corrected and rerun until failures are requirement failures.

### Task 2: Legal defender and formal-target resolution

**Files:**
- Modify: `common/scripted_triggers/zz_hd_historical_revolt_triggers.txt`
- Modify: `common/scripted_effects/zz_hd_historical_revolt_effects.txt`
- Modify: `common/casus_belli_types/zz_hd_historical_revolt_cb.txt`
- Test: `tools/tests/test_hd_historical_revolts.ps1`

**Interfaces:**
- Consumes: target title keys already used by the nine event effects.
- Produces: saved scopes `hd_revolt_defender`, `hd_revolt_primary_target`, optional repeated target scopes, and `hd_revolt_war`; the CB transfers only formal targets.

- [ ] **Step 1: Add failing assertions for `holder.top_liege` and formal multi-target wars**

Assert that defender selection contains `holder.top_liege`, that no direct-holder life trigger is used as an effect, and that multi-target start blocks contain repeated `target_title` entries rather than post-victory title lists.

- [ ] **Step 2: Run the test and verify RED**

Expected: FAIL on current direct-holder and single-target code.

- [ ] **Step 3: Implement the minimal current-ruler resolver**

Replace invalid `holder ?= { is_alive = yes }` effect blocks with legal conditional/limit scopes. Resolve each candidate title's current `holder.top_liege`, count eligible titles per ruler for multi-target uprisings, use stable title-order tie-breaking, and save only titles held under the selected defender.

- [ ] **Step 4: Implement formal repeated targets**

Build one `start_war` call per uprising with the selected defender and every selected formal `target_title`. Remove victory-time extra-title transfers that duplicate formal war resolution. Preserve defender victory and white-peace no-transfer behavior.

- [ ] **Step 5: Run the test and verify GREEN**

Run the Phase 1 test; all scope and target assertions must pass.

### Task 3: One-shot lifecycle and army cleanup

**Files:**
- Modify: `common/scripted_effects/zz_hd_historical_revolt_effects.txt`
- Modify: `common/casus_belli_types/zz_hd_historical_revolt_cb.txt`
- Modify: `common/on_action/zz_hd_historical_revolt_on_actions.txt`
- Test: `tools/tests/test_hd_historical_revolts.ps1`

**Interfaces:**
- Consumes: per-uprising permanent `hd_revolt_*_fired` flags and saved war scope.
- Produces: duplicate-safe committed/active/resolved state and cleanup on victory, defeat, white peace, and invalidation.

- [ ] **Step 1: Add failing ordering and terminal-cleanup assertions**

For each launch effect, assert the textual order `start_war` before `spawn_army`; assert every CB terminal block invokes the shared cleanup effect; assert all spawned armies have supply, noninheritance, and war binding.

- [ ] **Step 2: Run the test and verify RED**

Expected: FAIL where current fired timing and cleanup coverage are incomplete.

- [ ] **Step 3: Implement duplicate-safe launch state**

Set a narrow temporary committed state immediately before war creation. Only after a valid `scope:war` exists, set the permanent fired flag, clear committed, save active war, and spawn armies. If the war scope does not exist, clear committed and leave permanent fired absent so the window may retry.

- [ ] **Step 4: Normalize all terminal cleanup**

Use one shared cleanup effect from attacker victory, defender victory, white peace, and invalidation. Remove bound armies and temporary saved scopes/modifiers without deleting historical leaders.

- [ ] **Step 5: Run the test and verify GREEN**

All lifecycle, order, and army assertions pass.

### Task 4: Locked leader, culture, province, and troop data

**Files:**
- Modify: `common/scripted_effects/zz_hd_historical_revolt_effects.txt`
- Modify: `common/customizable_localization/zz_hd_historical_revolt_custom_loc.txt`
- Modify: `events/zz_hd_historical_revolt_events.txt`
- Test: `tools/tests/test_hd_historical_revolts.ps1`

**Interfaces:**
- Consumes: the REV-01 through REV-09 table in the spec and actual project title/province/culture keys.
- Produces: nine correctly configured leaders and fixed armies; Zhang Chun saved as the primary commander for REV-06.

- [ ] **Step 1: Add one failing data assertion group per uprising**

Each group asserts the exact window, fallback province order, regiment counts, target keys, leader ages/stats/prowess, and named special rule. Assertions use anchored event/effect blocks so equal numbers elsewhere cannot create false passes.

- [ ] **Step 2: Run the test and verify RED**

Expected: failures include Beigong's wrong primary spawn, Zhang Yan's martial, Baimatong's culture/traits, anonymous generated dynasties, Qiangqu priority, and Wang Guo target loss.

- [ ] **Step 3: Correct REV-01 through REV-04 minimally**

Apply the exact table values. Use lowborn anonymous characters, Huangzhong as Beigong's first location, Zhang Yan martial 17, Zhang Niujiao as deputy only, and the approved Jiangxia date shift.

- [ ] **Step 4: Correct REV-05 through REV-09 minimally**

Implement Wang Guo's same-defender join without erasing existing targets; Zhang Chun as main commander; Qiangqu political-identity priority; Mianzhu hard lock; and Yan Baihu's locked data.

- [ ] **Step 5: Run the test and verify GREEN**

All nine data groups pass and troop totals equal 6k/18k/16k/12k/16k/18k/18k/15k/12k.

### Task 5: Localization and obsolete name-list removal

**Files:**
- Modify: `localization/simp_chinese/zz_hd_historical_revolts_l_simp_chinese.yml`
- Modify: `common/customizable_localization/zz_hd_historical_revolt_custom_loc.txt`
- Delete: `common/culture/name_lists/zz_hd_historical_revolt_names.txt`
- Test: `tools/tests/test_hd_historical_revolts.ps1`

**Interfaces:**
- Consumes: all keys referenced by Phase 1 events and CB.
- Produces: one Simplified Chinese definition for every referenced key and no empty name-list definition.

- [ ] **Step 1: Add failing reference-to-localization assertions**

Extract Phase 1 event titles/descriptions/options, CB names/descriptions, and custom localization outputs; assert every key exists exactly once in the YAML and that the obsolete name-list file is absent.

- [ ] **Step 2: Run the test and verify RED**

Expected: FAIL on the current broken name list and any missing/duplicate key.

- [ ] **Step 3: Add only required localization and remove the unused name list**

Preserve existing approved prose where correct. Add or correct only missing keys, ensure UTF-8 BOM/YAML header, verify the name list has no references with `rg`, then delete it.

- [ ] **Step 4: Run the test and verify GREEN**

The localization/reference assertions pass with no empty list.

### Task 6: Phase 1 full static gate

**Files:**
- Test: `tools/tests/test_hd_historical_revolts.ps1`
- Read: all Phase 1 production files

**Interfaces:**
- Consumes: completed Phase 1 implementation.
- Produces: a recorded static PASS suitable for the later combined regression gate.

- [ ] **Step 1: Run the dedicated test from a clean PowerShell process**

```powershell
pwsh -NoProfile -File tools/tests/test_hd_historical_revolts.ps1
```

Expected: exit `0`, every named assertion PASS.

- [ ] **Step 2: Run repository-wide collision and encoding checks**

```powershell
python tools/verify_encoding.py
rg -n "holder \?= \{ is_alive|dynasty\s*=\s*generate|hd_revolt_.*_fired" common events localization
```

Expected: no invalid effect-context pattern in Phase 1, no anonymous generated dynasty there, and exactly the intended nine fired identifiers.

- [ ] **Step 3: Inspect the target-only diff**

```powershell
git diff -- events/zz_hd_historical_revolt_events.txt common/casus_belli_types/zz_hd_historical_revolt_cb.txt common/scripted_triggers/zz_hd_historical_revolt_triggers.txt common/scripted_effects/zz_hd_historical_revolt_effects.txt common/on_action/zz_hd_historical_revolt_on_actions.txt common/customizable_localization/zz_hd_historical_revolt_custom_loc.txt localization/simp_chinese/zz_hd_historical_revolts_l_simp_chinese.yml tools/tests/test_hd_historical_revolts.ps1
```

Expected: every changed line maps to the approved Phase 1 specification; no unrelated cleanup.
