# Historical World Chains Phase 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the five date-driven historical-war launchers with one-state world opportunities and CK3 story cycles for Fengying, Guandu, Chibi, LB-22 integration, LB-24, and LB-25.

**Architecture:** A lightweight world pulse checks only broad windows and hard state. World opportunity flags own unique facts; personal story cycles provide viewpoints and decisions without duplicating wars. Actual CB outcomes feed terminal events. The implementation adapts to the existing Cao/Liu Bei/palace-crisis chain through narrow hooks and does not rebuild unapproved personal content.

**Tech Stack:** CK3 1.19.0.6 story cycles, events, on_actions, scripted triggers/effects, CB, Simplified Chinese YAML, PowerShell structural tests.

**Spec:** `docs/superpowers/specs/2026-08-23-historical-event-chain-phase1-phase2-design.md`

## Global Constraints

- Fengying adds only the approved Cao Cao and Yuan Shao perspectives.
- Guandu and Chibi are world-state opportunities; dates alone never start wars.
- Rushu is removed as a standalone launcher and belongs to Liu Bei LB-22.
- Add only LB-24 and LB-25 to Liu Bei's approved line; do not add LB-23 or rewrite LB-18 through LB-21.
- Historical AI weight is extremely high but never absolute.
- Each personal story supports historical, nonhistorical, alternate-success, and alternate-failure terminal states.
- Preserve user dirty work and use project-owned additive files, not vanilla global replacements.
- Do not launch CK3 until separate runtime authorization is obtained.

---

### Task 1: Phase 2 structural regression test

**Files:**
- Create: `tools/tests/test_hd_historical_world_chains.ps1`
- Read: the four existing `zz_hd_historical_war_*` files
- Read: `events/zz_hd_cao_chain_events.txt`
- Read: `events/zz_hd_liu_bei_aftermath_events.txt`

**Interfaces:**
- Consumes: current Phase 2 files and future story/event/localization files.
- Produces: a nonzero structural gate covering direct-date launch removal, story lifecycle, unique world facts, four terminal classes, localization, and stale key removal.

- [ ] **Step 1: Create assertions for known invalid architecture**

Assert that no monthly effect directly calls Fengying/Guandu/Chibi/Rushu/Yiling launch effects; no trigger consists only of a date and character presence; no `set_diarch` occurs without a nearby active-diarchy check; `hd_historical_war_rushu_effect` is absent; all referenced localization keys exist.

- [ ] **Step 2: Run and verify RED**

```powershell
pwsh -NoProfile -File tools/tests/test_hd_historical_world_chains.ps1
```

Expected: FAIL on all five current date-driven launchers, missing localization, and missing story cycles.

### Task 2: Unique world-opportunity state and pulse

**Files:**
- Modify: `common/on_action/zz_hd_historical_war_on_actions.txt`
- Modify: `common/scripted_triggers/zz_hd_historical_war_triggers.txt`
- Modify: `common/scripted_effects/zz_hd_historical_war_effects.txt`
- Test: `tools/tests/test_hd_historical_world_chains.ps1`

**Interfaces:**
- Produces: `hd_fengying_world_open/claimed/resolved`, `hd_guandu_world_open/active/resolved`, `hd_chibi_world_open/active/resolved`, `hd_lb24_world_open/resolved`, and `hd_lb25_world_open/resolved` state families.
- Consumes: actual current characters, titles, top lieges, wars, geographic reach, and the broad approved windows.

- [ ] **Step 1: Add failing unique-state and hard-condition assertions**

Require separate `open`, `active/claimed`, and `resolved` states; require every ready trigger to include the full approved hard-condition family; reject direct `start_war` from the monthly pulse.

- [ ] **Step 2: Run and verify RED**

Expected: current files fail because they only use date thresholds and direct launch effects.

- [ ] **Step 3: Implement the minimal windowed world pulse**

The pulse checks each opportunity at bounded frequency, opens it once when hard conditions hold, expires it after the approved window or when permanently meaningless, and calls only an event/story setup effect. Remove direct war creation and direct political conversion from the pulse.

- [ ] **Step 4: Run and verify GREEN**

All world-state, hard-condition, and no-direct-launch assertions pass.

### Task 3: Personal story-cycle definitions

**Files:**
- Create: `common/story_cycles/zz_hd_historical_character_story_cycles.txt`
- Test: `tools/tests/test_hd_historical_world_chains.ps1`

**Interfaces:**
- Produces story types for Cao Fengying, Yuan Fengying, Liu Bei LB-24, and Liu Bei LB-25 with `on_setup`, bounded `effect_group`, `on_owner_death`, and `on_end`.
- Consumes world state from Task 2 and terminal event IDs from later tasks.

- [ ] **Step 1: Add failing lifecycle assertions**

For every story type assert `on_setup`, at least one bounded timer group, explicit fallback, `on_owner_death`, `on_end`, one owner, and cleanup of temporary scopes.

- [ ] **Step 2: Run and verify RED**

Expected: FAIL because no Phase 2 story-cycle file exists.

- [ ] **Step 3: Implement minimal story skeletons using vanilla 1.19 patterns**

Use `make_story_owner` only where verified, save only required participant scopes, end on owner death, and route timed checks to named events. Internal world coordination remains flags/effects, not visible duplicate stories.

- [ ] **Step 4: Run and verify GREEN**

Lifecycle assertions pass; no unbounded monthly character scan is introduced.

### Task 4: Fengying single-world competition

**Files:**
- Create: `events/zz_hd_fengying_events.txt`
- Modify: `common/story_cycles/zz_hd_historical_character_story_cycles.txt`
- Modify: `common/scripted_effects/zz_hd_historical_war_effects.txt`
- Modify: `events/zz_hd_cao_chain_events.txt` only for a narrow story hook
- Modify: `localization/simp_chinese/zz_hd_historical_world_chains_l_simp_chinese.yml`
- Test: `tools/tests/test_hd_historical_world_chains.ps1`

**Interfaces:**
- Consumes: one living accessible Han emperor, Cao/Yuan autonomous political capacity, world claim state.
- Produces: exactly one claimant outcome, verified diarchy/protection relation when legal, Cao/Yuan perspective memories, and four terminal classes.

- [ ] **Step 1: Add failing assertions for options and single ownership**

Require Cao's receive/escort/refuse/control options, Yuan's receive/hesitate/limited-aid/obstruct options, non-100 AI weights, atomic world claim, and terminal events for historical/nonhistorical/alternate-success/alternate-failure.

- [ ] **Step 2: Run and verify RED**

Expected: missing events/story behavior and unsafe current diarchy effect.

- [ ] **Step 3: Implement Cao and Yuan perspective events**

Both stories refer to the same emperor and claim state. The first legal completed claim wins; the other receives a perspective result. Choices apply limited immediate costs/memories, not duplicate world transformations.

- [ ] **Step 4: Implement safe court-control result**

Call `try_start_diarchy = regency`, verify `has_active_diarchy = yes`, then assign the intended diarch using the installed vanilla pattern. If the independent-warlord relation is rejected in runtime, leave the script on the existing palace-crisis-compatible protection state rather than asserting success.

- [ ] **Step 5: Run and verify GREEN**

Fengying assertions and localization references pass.

### Task 5: Guandu world event and actual-war outcomes

**Files:**
- Create: `events/zz_hd_historical_world_events.txt`
- Modify: `common/casus_belli_types/zz_hd_historical_war_cb.txt`
- Modify: `common/scripted_triggers/zz_hd_historical_war_triggers.txt`
- Modify: `common/scripted_effects/zz_hd_historical_war_effects.txt`
- Modify: `localization/simp_chinese/zz_hd_historical_world_chains_l_simp_chinese.yml`
- Test: `tools/tests/test_hd_historical_world_chains.ps1`

**Interfaces:**
- Consumes: Cao/Yuan hegemon, autonomy, rivalry, reach, 198–203, optional Xu You facts.
- Produces: one Guandu war opportunity; actual attacker/defender victory, white peace, and invalidation feed graded terminal events.

- [ ] **Step 1: Add failing Guandu-condition and outcome assertions**

Require all hard conditions, four Cao strategic options, conditional Xu You path with scout fallback, temporary Wuchao/logistics state, and no unconditional annexation.

- [ ] **Step 2: Run and verify RED**

Expected: current direct war effect fails condition and outcome assertions.

- [ ] **Step 3: Implement the world event and legal CB**

Create one formal war only after a participant chooses battle and the CB is legal. Keep Wuchao effects temporary and war-bound. Use actual CB callbacks for Cao victory, Yuan victory, white peace, and invalidation.

- [ ] **Step 4: Implement graded aftermath**

Cao victory modifies prestige/loyalty pressure without instant河北 annexation. Yuan victory produces major political effects only if capture, capital, or emperor-control facts support them. Limited and failed outcomes end the world opportunity cleanly.

- [ ] **Step 5: Run and verify GREEN**

Guandu structural, lifecycle, and localization assertions pass.

### Task 6: Chibi world event and alliance gate

**Files:**
- Modify: `events/zz_hd_historical_world_events.txt`
- Modify: `common/casus_belli_types/zz_hd_historical_war_cb.txt`
- Modify: `common/scripted_triggers/zz_hd_historical_war_triggers.txt`
- Modify: `common/scripted_effects/zz_hd_historical_war_effects.txt`
- Modify: `localization/simp_chinese/zz_hd_historical_world_chains_l_simp_chinese.yml`
- Test: `tools/tests/test_hd_historical_world_chains.ps1`

**Interfaces:**
- Consumes: Cao southern expedition, Jingzhou crisis, Sun Jiangdong control, Liu Bei independent force, and an actual Sun-Liu alliance.
- Produces: one Chibi war/opportunity with observable temporary risk factors and actual outcomes.

- [ ] **Step 1: Add failing alliance/risk/outcome assertions**

Require all five hard gates, separate temporary factors for disease, expedition length, naval experience, new troop loyalty, tied ships, logistics, and Huang Gai; reject automatic Cao collapse.

- [ ] **Step 2: Run and verify RED**

Expected: current date effect lacks alliance and risk architecture.

- [ ] **Step 3: Implement the alliance-gated opportunity**

Handle Jingzhou surrender from actual holder choices, open Chibi only after Cao continues southeast and Sun-Liu alliance exists, and degrade named-character tactics to weaker functional alternatives when historical characters are absent.

- [ ] **Step 4: Bind risk mitigation and outcomes to the actual war**

Allow Cao preparation choices to reduce risks. On defeat, end expedition and apply finite losses/fatigue; do not explode the realm. Implement Cao victory, Sun-Liu victory, withdrawal/limited result, and invalidation.

- [ ] **Step 5: Run and verify GREEN**

Chibi assertions and localization pass.

### Task 7: Remove Rushu and restore the minimal LB-22 interface

**Files:**
- Modify: `common/on_action/zz_hd_historical_war_on_actions.txt`
- Modify: `common/scripted_triggers/zz_hd_historical_war_triggers.txt`
- Modify: `common/scripted_effects/zz_hd_historical_war_effects.txt`
- Create: `events/zz_hd_liu_bei_late_events.txt`
- Test: `tools/tests/test_hd_historical_world_chains.ps1`

**Interfaces:**
- Consumes: an existing/future LB-22 completion signal plus actual Chengdu, Liu Zhang surrender, Yizhou, and Jingzhou facts.
- Produces: `hd_lb22_yizhou_success` or failure terminal state and the Guan Yu appointment event hook.

- [ ] **Step 1: Add failing no-Rushu and factual-LB22 assertions**

Reject `hd_historical_war_rushu_effect` and its direct CB. Require the LB-22 adapter to test Chengdu control or Liu Zhang surrender; reject an unapproved percentage threshold.

- [ ] **Step 2: Run and verify RED**

Expected: the current Rushu launcher exists and no LB-22 adapter exists.

- [ ] **Step 3: Delete the date-driven Rushu path**

Remove its monthly call, trigger, effect, CB-only branch, flags, and orphaned localization while preserving unrelated Phase 2 identifiers.

- [ ] **Step 4: Add the minimal LB-22 completion adapter**

Accept a call from the user's existing LB chain and verify factual success. Do not synthesize LB-18 through LB-21 and do not independently initiate an Yizhou war.

- [ ] **Step 5: Run and verify GREEN**

No Rushu direct launcher remains; the adapter has only approved success conditions.

### Task 8: Guan Yu appointment and LB-24

**Files:**
- Modify: `events/zz_hd_liu_bei_late_events.txt`
- Modify: `common/story_cycles/zz_hd_historical_character_story_cycles.txt`
- Modify: `common/scripted_triggers/zz_hd_historical_war_triggers.txt`
- Modify: `common/scripted_effects/zz_hd_historical_war_effects.txt`
- Modify: `localization/simp_chinese/zz_hd_historical_world_chains_l_simp_chinese.yml`
- Test: `tools/tests/test_hd_historical_world_chains.ps1`

**Interfaces:**
- Consumes: factual LB-22 success, actual project Jingzhou title/governorship, Guan Yu availability, northern campaign, Sun/Cao relations, Jingzhou garrison facts.
- Produces: legal Guan Yu appointment and LB-24 terminal state; only historical Guan Yu death plus Sun control opens LB-25.

- [ ] **Step 1: Resolve the actual Jingzhou political title from project files**

Use `rg` across landed titles, title history, government/appointment scripts, and existing Liu Bei files. Record the exact key in the test fixture and fail if the appointment effect only sets a flag without changing legal political state.

- [ ] **Step 2: Run the new appointment test and verify RED**

Expected: no current appointment effect exists.

- [ ] **Step 3: Implement the post-LB22 appointment event**

Offer appoint Guan Yu or retain existing arrangement. Transfer only Liu Bei-group legal titles or use the existing appointment mechanism; never seize third-party/protected land. Historical AI strongly, not absolutely, favors Guan Yu.

- [ ] **Step 4: Add LB-24 failing assertions**

Require Guan Yu actual Jingzhou control plus northern war, Sun/Cao relation checks, Mi Fang/Fu Shiren contextual checks, defense state, four terminal classes, and no date-kill effect.

- [ ] **Step 5: Implement LB-24 and verify GREEN**

Sun chooses attack/align/wait/maintain alliance based on facts. Garrison characters decide from relationships and danger. Actual war/siege/capture facts determine territory and Guan Yu's fate.

### Task 9: LB-25 Yiling

**Files:**
- Modify: `events/zz_hd_liu_bei_late_events.txt`
- Modify: `common/story_cycles/zz_hd_historical_character_story_cycles.txt`
- Modify: `common/casus_belli_types/zz_hd_historical_war_cb.txt`
- Modify: `common/scripted_triggers/zz_hd_historical_war_triggers.txt`
- Modify: `common/scripted_effects/zz_hd_historical_war_effects.txt`
- Modify: `localization/simp_chinese/zz_hd_historical_world_chains_l_simp_chinese.yml`
- Test: `tools/tests/test_hd_historical_world_chains.ps1`

**Interfaces:**
- Consumes: Guan Yu dead, Jingzhou controlled by Sun group, living autonomous Liu Bei.
- Produces: four approved Liu Bei choices, risk-based actual war, and four terminal classes.

- [ ] **Step 1: Add failing Yiling assertions**

Require the three hard facts, attack/accept alliance/demand Jingzhou/delay options, non-100 historical AI, separate supply/mountain/camp/Lu Xun/heat risks, and no automatic defeat.

- [ ] **Step 2: Run and verify RED**

Expected: current direct date war fails all story and choice checks.

- [ ] **Step 3: Implement choices and actual war path**

Only attack starts a legal war. Diplomatic options produce bounded results. Risks modify the war and can be mitigated; Lu Xun absence uses a weaker real Sun-side commander path.

- [ ] **Step 4: Implement actual terminal outcomes**

Read attacker victory, defender victory, white peace, withdrawal, invalidation, and owner death. Do not overwrite the result because the historical window elapsed.

- [ ] **Step 5: Run and verify GREEN**

All Yiling assertions and localization references pass.

### Task 10: Migration cleanup and combined static gate

**Files:**
- Modify/Delete: obsolete sections of the four existing `zz_hd_historical_war_*` files
- Modify: `localization/simp_chinese/zz_hd_historical_world_chains_l_simp_chinese.yml`
- Test: `tools/tests/test_hd_historical_world_chains.ps1`
- Test: `tools/tests/test_hd_historical_revolts.ps1`

**Interfaces:**
- Consumes: completed Phase 1 and Phase 2 implementations.
- Produces: old fired-flag no-repeat mapping, no orphaned direct launcher, clean cross-phase static PASS.

- [ ] **Step 1: Add failing migration/orphan assertions**

Require old fired flags to map only to terminal state, reject old active-war recreation, and detect unreferenced Phase 2 effects/CB/localization keys.

- [ ] **Step 2: Run and verify RED**

Expected: any residual direct launcher or orphan key fails.

- [ ] **Step 3: Remove obsolete code and add minimal fired-flag migration**

Preserve old flags solely as no-repeat markers. Do not promise migration of already-active test-save wars.

- [ ] **Step 4: Run both dedicated suites**

```powershell
pwsh -NoProfile -File tools/tests/test_hd_historical_revolts.ps1
pwsh -NoProfile -File tools/tests/test_hd_historical_world_chains.ps1
python tools/verify_encoding.py
```

Expected: all exit `0`; encoding output contains no changed-file failures.

- [ ] **Step 5: Run collision and target-diff review**

Search all mod script/localization files for duplicate event/story/CB IDs, missing keys, old Rushu/Yiling direct effects, and invalid scope patterns. Inspect only the target diff and confirm each line maps to the approved design.

- [ ] **Step 6: Stop at the runtime boundary**

Report static evidence and request explicit authorization before CK3 startup and scenario testing. Do not claim startup or runtime correctness from static results.
