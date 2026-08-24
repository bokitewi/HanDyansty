param()

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
function Read-OrEmpty([string]$Relative) {
    $path = Join-Path $repo $Relative
    if (Test-Path -LiteralPath $path) { return Get-Content -LiteralPath $path -Raw -Encoding UTF8 }
    return ''
}

$onActions = Read-OrEmpty 'common\on_action\zz_hd_historical_war_on_actions.txt'
$triggers = Read-OrEmpty 'common\scripted_triggers\zz_hd_historical_war_triggers.txt'
$effects = Read-OrEmpty 'common\scripted_effects\zz_hd_historical_war_effects.txt'
$cb = Read-OrEmpty 'common\casus_belli_types\zz_hd_historical_war_cb.txt'
$stories = Read-OrEmpty 'common\story_cycles\zz_hd_historical_character_story_cycles.txt'
$fengying = Read-OrEmpty 'events\zz_hd_fengying_events.txt'
$worldEvents = Read-OrEmpty 'events\zz_hd_historical_world_events.txt'
$liuBeiEvents = Read-OrEmpty 'events\zz_hd_liu_bei_late_events.txt'
$peachGardenEvents = Read-OrEmpty 'events\zz_hd_peach_garden_events.txt'
$liuBeiAftermathEvents = Read-OrEmpty 'events\zz_hd_liu_bei_aftermath_events.txt'
$adventurerStartup = Read-OrEmpty 'common\on_action\zz_hd_184_adventurers_startup.txt'
$yellowTurbanEffects = Read-OrEmpty 'common\scripted_effects\zz_hd_yellow_turban_effects.txt'
$modifiers = Read-OrEmpty 'common\modifiers\zz_hd_historical_world_modifiers.txt'
$loc = Read-OrEmpty 'localization\simp_chinese\zz_hd_historical_world_chains_l_simp_chinese.yml'
$phase2All = $onActions + $triggers + $effects + $cb + $stories + $fengying + $worldEvents + $liuBeiEvents + $modifiers + $loc
$all = $onActions + $triggers + $effects + $cb + $stories + $fengying + $worldEvents + $liuBeiEvents + $peachGardenEvents + $liuBeiAftermathEvents + $adventurerStartup + $yellowTurbanEffects + $modifiers + $loc
$script:Failures = 0

function Assert-True([bool]$Condition, [string]$Name) {
    if ($Condition) { Write-Host "PASS: $Name" -ForegroundColor Green }
    else { Write-Host "FAIL: $Name" -ForegroundColor Red; $script:Failures++ }
}

function Assert-MatchCount([string]$Text, [string]$Pattern, [int]$Expected, [string]$Name) {
    $count = [regex]::Matches($Text, $Pattern, [Text.RegularExpressions.RegexOptions]::Multiline).Count
    Assert-True ($count -eq $Expected) "$Name (expected $Expected, got $count)"
}

function Test-BraceBalance([string]$Text) {
    $depth = 0
    foreach ($line in ($Text -split "`r?`n")) {
        $code = ($line -replace '#.*$', '') -replace '"(?:[^"\\]|\\.)*"', ''
        foreach ($char in $code.ToCharArray()) {
            if ($char -eq '{') { $depth++ }
            elseif ($char -eq '}') { $depth--; if ($depth -lt 0) { return $false } }
        }
    }
    return $depth -eq 0
}

function Get-NamedBlock([string]$Text, [string]$Name) {
    $match = [regex]::Match($Text, "(?m)^$([regex]::Escape($Name))\s*=\s*\{")
    if (-not $match.Success) { return '' }
    $open = $Text.IndexOf('{', $match.Index)
    $depth = 0
    for ($i = $open; $i -lt $Text.Length; $i++) {
        if ($Text[$i] -eq '{') { $depth++ }
        elseif ($Text[$i] -eq '}') {
            $depth--
            if ($depth -eq 0) { return $Text.Substring($match.Index, $i - $match.Index + 1) }
        }
    }
    return ''
}

Assert-True ($stories.Length -gt 0) 'Phase 2 story-cycle file exists'
Assert-True ($fengying.Length -gt 0) 'Fengying event file exists'
Assert-True ($worldEvents.Length -gt 0) 'Guandu and Chibi world-event file exists'
Assert-True ($liuBeiEvents.Length -gt 0) 'Liu Bei late-chain event file exists'
Assert-True ($peachGardenEvents.Length -gt 0) 'Peach Garden opening event file exists'
Assert-True ($modifiers.Length -gt 0) 'historical war risk modifier file exists'
Assert-True ($loc -match '^l_simp_chinese:') 'Phase 2 Simplified Chinese localization exists'

foreach ($text in @($onActions,$triggers,$effects,$cb,$stories,$fengying,$worldEvents,$liuBeiEvents,$modifiers)) {
    Assert-True (Test-BraceBalance $text) 'Phase 2 script fragment has balanced braces'
}

Assert-True ($onActions -notmatch 'hd_historical_war_(fengying|guandu|chibi|rushu|yiling)_effect') 'monthly pulse never directly launches a historical result or war'
Assert-True ($all -notmatch 'hd_historical_war_rushu_effect|hd_historical_war_rushu_ready_trigger|hd_war_rushu') 'standalone Rushu launcher is removed'
Assert-True ($effects -match 'hd_migrate_legacy_historical_war_flags_effect[\s\S]*?hd_fengying_fired[\s\S]*?hd_guandu_fired[\s\S]*?hd_chibi_fired[\s\S]*?hd_rushu_fired[\s\S]*?hd_yiling_fired') 'legacy fired flags map to no-repeat terminal state'
Assert-True ($all -notmatch 'current_date\s*>=\s*(196\.7\.1|200\.2\.1|208\.9\.1|212\.10\.1|221\.7\.1)') 'old single-date launch thresholds are removed'

$worldStates = @(
    'hd_fengying_world_open','hd_fengying_world_claimed','hd_fengying_world_resolved',
    'hd_guandu_world_open','hd_guandu_world_active','hd_guandu_world_resolved',
    'hd_chibi_world_open','hd_chibi_world_active','hd_chibi_world_resolved',
    'hd_lb24_world_open','hd_lb24_world_resolved','hd_lb25_world_open','hd_lb25_world_resolved'
)
foreach ($state in $worldStates) { Assert-True ($all -match [regex]::Escape($state)) "world state exists: $state" }

$storyIds = @('hd_story_cao_fengying','hd_story_yuan_fengying','hd_story_liu_bei_life','hd_story_liu_bei_lb24','hd_story_liu_bei_lb25')
foreach ($id in $storyIds) {
    Assert-True ($stories -match "(?m)^$([regex]::Escape($id))\s*=\s*\{") "story exists: $id"
}
Assert-MatchCount $stories 'on_owner_death\s*=\s*\{' 5 'each personal story handles owner death'
Assert-MatchCount $stories 'on_end\s*=\s*\{' 5 'each personal story cleans up on end'
Assert-MatchCount $stories 'on_owner_death\s*=\s*\{\s*set_global_variable\s*=\s*hd_fengying_world_resolved' 2 'both Fengying owner-death terminals permanently resolve the opportunity'
Assert-True ($stories -match 'effect_group\s*=\s*\{[\s\S]*?months\s*=') 'story checks use bounded month timers'

Assert-True ($onActions -match 'on_game_start_after_lobby\s*=\s*\{[\s\S]*?hd_liu_bei_life_after_lobby') 'new games attach Liu Bei life story after lobby setup'
Assert-True ($onActions -match 'hd_historical_world_monthly_check[\s\S]*?hd_update_liu_bei_life_story_effect') 'monthly pulse backfills and advances Liu Bei life story in existing saves'
Assert-True ($effects -match 'hd_update_liu_bei_life_story_effect[\s\S]*?NOT\s*=\s*\{\s*any_owned_story\s*=\s*\{\s*type\s*=\s*hd_story_liu_bei_life') 'life-story creation is guarded by actual owned-story state'
Assert-True ($effects -match 'create_story\s*=\s*\{\s*type\s*=\s*hd_story_liu_bei_life') 'lifetime story is created for Liu Bei'
$liuBeiLifeUpdate = Get-NamedBlock $effects 'hd_update_liu_bei_life_story_effect'
Assert-MatchCount $liuBeiLifeUpdate 'character:liu_bei\s*=\s*\{' 3 'story mutation and Peach delivery re-enter Liu Bei character scope separately'
$lifeStory = Get-NamedBlock $stories 'hd_story_liu_bei_life'
Assert-True ($lifeStory -match 'on_owner_death\s*=\s*\{[\s\S]*?hd_lb24_world_resolved[\s\S]*?hd_lb25_world_resolved[\s\S]*?end_story\s*=\s*yes') 'lifetime story resolves open late phases before ending on Liu Bei death'
Assert-True ($lifeStory -match 'set_variable\s*=\s*\{\s*name\s*=\s*hd_liu_bei_life_phase\s*value\s*=\s*flag:hd_liu_bei_phase_rising') 'lifetime story initializes a visible phase milestone'
Assert-True ($loc -match "Story\.MakeScope\.Var\('hd_liu_bei_life_phase'\)\.GetFlagName") 'story visualization reads the lifetime phase milestone'
Assert-True ($effects -match 'current_date\s*>=\s*184\.1\.1[\s\S]{0,500}?current_date\s*<=\s*184\.12\.31[\s\S]{0,900}?hd_peach_garden_event_pending[\s\S]{0,300}?trigger_event\s*=\s*hd_peach_garden\.0001') 'Peach Garden retries idempotently inside the approved 184 window'
Assert-True ($effects -match 'add_character_flag\s*=\s*\{\s*flag\s*=\s*hd_peach_garden_event_pending\s*days\s*=\s*60\s*\}') 'Peach Garden dispatch lock expires if the event never opens'
Assert-True ($effects -match 'NOT\s*=\s*\{\s*has_character_flag\s*=\s*hd_peach_garden_event_opened\s*\}') 'an opened Peach Garden event blocks duplicate dispatch'
Assert-True ($effects -match 'NOT\s*=\s*\{\s*has_character_flag\s*=\s*hd_liu_bei_dispatch_state_v2_migrated\s*\}[\s\S]{0,220}?remove_character_flag\s*=\s*hd_peach_garden_event_pending[\s\S]{0,220}?add_character_flag\s*=\s*hd_liu_bei_dispatch_state_v2_migrated') 'intermediate saves migrate the old permanent Peach Garden dispatch lock once'
Assert-True ($peachGardenEvents -notmatch 'current_date\s*=\s*184\.1\.1') 'Peach Garden event is not pinned to one exact date'
Assert-True ($peachGardenEvents -match 'current_date\s*>=\s*184\.1\.1' -and $peachGardenEvents -match 'current_date\s*<=\s*184\.12\.31') 'Peach Garden event validates the full retry window'
Assert-True ($peachGardenEvents -match 'remove_character_flag\s*=\s*hd_peach_garden_event_opened[\s\S]{0,180}?add_character_flag\s*=\s*hd_peach_garden_oath_completed') 'Peach Garden success clears opened state before terminalizing the oath phase'
Assert-True ($peachGardenEvents -match 'immediate\s*=\s*\{[\s\S]{0,220}?remove_character_flag\s*=\s*hd_peach_garden_event_pending[\s\S]{0,120}?add_character_flag\s*=\s*hd_peach_garden_event_opened') 'Peach Garden converts the expiring dispatch lock when the event actually opens'
Assert-True ($adventurerStartup -notmatch 'hd_peach_garden\.0001') 'one-shot camp startup no longer owns Peach Garden delivery'
Assert-True ($effects -match 'hd_liu_bei_aftermath_pending[\s\S]{0,500}?hd_liu_bei_aftermath\.0001') 'lifetime update backfills the Yellow Turban aftermath without duplicate scheduling'
Assert-True ($effects -match 'flag\s*=\s*hd_liu_bei_aftermath_pending\s*days\s*=\s*150' -and $yellowTurbanEffects -match 'flag\s*=\s*hd_liu_bei_aftermath_pending\s*days\s*=\s*150') 'both aftermath launchers use an expiring dispatch lock'
Assert-True ($liuBeiAftermathEvents -match 'remove_character_flag\s*=\s*hd_liu_bei_aftermath_pending[\s\S]{0,120}?add_character_flag\s*=\s*hd_liu_bei_aftermath_started') 'aftermath becomes terminal only when its event opens'

Assert-True ($fengying -match 'hd_fengying_cao_receive' -and $fengying -match 'hd_fengying_cao_escort' -and $fengying -match 'hd_fengying_cao_refuse' -and $fengying -match 'hd_fengying_cao_control') 'Cao Fengying has four approved choices'
Assert-True ($fengying -match 'hd_fengying_yuan_receive' -and $fengying -match 'hd_fengying_yuan_hesitate' -and $fengying -match 'hd_fengying_yuan_aid' -and $fengying -match 'hd_fengying_yuan_obstruct') 'Yuan Fengying has four approved choices'
Assert-True ($fengying -match 'try_start_diarchy\s*=\s*regency[\s\S]*?has_active_diarchy\s*=\s*yes[\s\S]*?set_diarch') 'Fengying verifies diarchy creation before assigning Cao or Yuan'
Assert-True ($phase2All -notmatch 'ai_chance\s*=\s*\{\s*base\s*=\s*100\s*\}') 'historical AI choices are not absolute'

Assert-True ($triggers -match 'hd_guandu_world_ready_trigger[\s\S]*?character:cao_cao[\s\S]*?character:yuan_shao') 'Guandu requires both Cao Cao and Yuan Shao'
Assert-True ($worldEvents -match 'hd_guandu_decide_battle' -and $worldEvents -match 'hd_guandu_defend_yellow_river' -and $worldEvents -match 'hd_guandu_compromise' -and $worldEvents -match 'hd_guandu_clear_other_enemies') 'Guandu exposes four strategic choices'
Assert-True ($worldEvents -match 'character:xu_you[\s\S]*?is_alive[\s\S]*?is_imprisoned\s*=\s*no') 'Xu You path checks actual availability'
Assert-True ($worldEvents -match 'hd_guandu_scout_fallback') 'Guandu has weaker scout fallback'
Assert-True ($modifiers -match '(?m)^hd_guandu_xu_you_wuchao_modifier\s*=\s*\{' -and $worldEvents -match 'add_character_modifier\s*=\s*\{\s*modifier\s*=\s*hd_guandu_xu_you_wuchao_modifier') 'Xu You and Wuchao path changes Yuan Shao actual war advantage temporarily'
Assert-True ($modifiers -match '(?m)^hd_guandu_scout_wuchao_modifier\s*=\s*\{' -and $worldEvents -match 'add_character_modifier\s*=\s*\{\s*modifier\s*=\s*hd_guandu_scout_wuchao_modifier') 'fallback scouting changes Yuan Shao actual war advantage more weakly'
Assert-True ($effects -match 'hd_clear_guandu_wuchao_effect[\s\S]*?remove_character_modifier\s*=\s*hd_guandu_xu_you_wuchao_modifier') 'every Guandu terminal can remove temporary Wuchao modifiers'

Assert-True ($triggers -match 'hd_chibi_world_ready_trigger[\s\S]*?character:cao_cao[\s\S]*?character:sun_quan[\s\S]*?character:liu_bei') 'Chibi requires Cao, Sun, and Liu Bei actors'
Assert-True ($all -match 'hd_chibi_sun_liu_alliance') 'Chibi requires an actual Sun-Liu alliance state'
Assert-True ($effects -match 'title:k_uuii_jingzhou\.holder[\s\S]{0,260}?trigger_event\s*=\s*hd_historical_world\.0210') 'Chibi opens through an event for the actual Jingzhou holder'
Assert-True ($worldEvents -match 'hd_historical_world\.0210[\s\S]*?character:liu_cong_2') 'Jingzhou surrender event recognizes the actual Liu Biao son Liu Cong when present'
Assert-True ($worldEvents -match 'hd_chibi_jingzhou_surrender[\s\S]*?title:k_uuii_jingzhou[\s\S]*?change_title_holder_include_vassals[\s\S]*?character:cao_cao') 'Jingzhou surrender changes actual title control to Cao Cao'
Assert-True ($worldEvents -match 'hd_chibi_jingzhou_resist') 'actual Jingzhou holder can resist instead of being date-forced to surrender'
foreach ($risk in @('disease','expedition','naval','jingzhou_loyalty','tied_ships','logistics','huang_gai')) {
    Assert-True ($all -match "hd_chibi_risk_$risk") "Chibi risk represented: $risk"
    Assert-True ($modifiers -match "(?m)^hd_chibi_risk_${risk}_modifier\s*=\s*\{" -and $worldEvents -match "add_character_modifier\s*=\s*\{\s*modifier\s*=\s*hd_chibi_risk_${risk}_modifier") "Chibi risk changes actual Cao army advantage: $risk"
}
Assert-True ($effects -match 'hd_clear_chibi_risks_effect[\s\S]*?remove_character_modifier\s*=\s*hd_chibi_risk_disease_modifier') 'every Chibi terminal can remove applied risk modifiers'

Assert-True ($effects -match 'hd_lb22_success_adapter_effect') 'LB-22 factual-success adapter exists'
Assert-True ($liuBeiEvents -match 'title:k_uuii_jingzhou') 'Guan Yu appointment uses the actual Jingzhou kingdom title'
Assert-True ($liuBeiEvents -match 'character:guan_yu') 'Guan Yu appointment uses the historical character'
Assert-True ($triggers -match 'hd_lb24_world_ready_trigger[\s\S]*?character:guan_yu[\s\S]*?k_uuii_jingzhou') 'LB-24 requires Guan Yu actual Jingzhou control'
Assert-True ($all -notmatch 'kill_character[\s\S]{0,120}?current_date') 'LB-24 never kills Guan Yu because a date arrived'
Assert-True ($effects -notmatch 'create_story\s*=\s*\{\s*type\s*=\s*hd_story_liu_bei_lb2[45]') 'new LB24 and LB25 opportunities continue the lifetime story instead of creating duplicate phase stories'
Assert-True ($effects -match 'hd_open_lb24_world_opportunity_effect[\s\S]{0,420}?hd_update_liu_bei_life_story_effect' -and $effects -match 'hd_open_lb25_world_opportunity_effect[\s\S]{0,420}?hd_update_liu_bei_life_story_effect') 'both late Liu Bei phases ensure the lifetime story before opening'
Assert-True ($effects -match 'hd_lb22_success_adapter_effect[\s\S]{0,500}?random_owned_story\s*=\s*\{\s*type\s*=\s*hd_story_liu_bei_life[\s\S]{0,180}?flag:hd_liu_bei_phase_yizhou') 'LB22 records its milestone on the lifetime story object'
Assert-True ($effects -match 'hd_open_lb24_world_opportunity_effect[\s\S]{0,500}?random_owned_story\s*=\s*\{\s*type\s*=\s*hd_story_liu_bei_life[\s\S]{0,180}?flag:hd_liu_bei_phase_jingzhou') 'LB24 records its milestone on the lifetime story object'
Assert-True ($effects -match 'hd_open_lb25_world_opportunity_effect[\s\S]{0,500}?random_owned_story\s*=\s*\{\s*type\s*=\s*hd_story_liu_bei_life[\s\S]{0,180}?flag:hd_liu_bei_phase_yiling') 'LB25 records its milestone on the lifetime story object'
foreach ($adapterName in @('hd_lb22_success_adapter_effect','hd_open_lb24_world_opportunity_effect','hd_open_lb25_world_opportunity_effect')) {
    $adapterBlock = Get-NamedBlock $effects $adapterName
    Assert-MatchCount $adapterBlock 'character:liu_bei\s*=\s*\{' 2 "$adapterName re-enters Liu Bei scope after mutating the story"
}
$lb24Story = Get-NamedBlock $stories 'hd_story_liu_bei_lb24'
$lb25Story = Get-NamedBlock $stories 'hd_story_liu_bei_lb25'
Assert-True ($lb24Story -match 'visible\s*=\s*no' -and $lb25Story -match 'visible\s*=\s*no') 'legacy phase stories remain loadable but are hidden after migration'

Assert-True ($triggers -match 'hd_lb25_world_ready_trigger[\s\S]*?character:guan_yu\s*=\s*\{\s*is_alive\s*=\s*no[\s\S]*?character:sun_quan') 'LB-25 requires Guan Yu death and Sun control'
foreach ($choice in @('hd_yiling_attack_wu','hd_yiling_keep_alliance','hd_yiling_demand_jingzhou','hd_yiling_delay_revenge')) {
    Assert-True ($liuBeiEvents -match $choice) "Yiling choice exists: $choice"
}
foreach ($risk in @('supply','mountain','camps','lu_xun','heat')) {
    Assert-True ($all -match "hd_yiling_risk_$risk") "Yiling risk represented: $risk"
    Assert-True ($modifiers -match "(?m)^hd_yiling_risk_${risk}_modifier\s*=\s*\{" -and $effects -match "add_character_modifier\s*=\s*\{\s*modifier\s*=\s*hd_yiling_risk_${risk}_modifier") "Yiling risk changes actual Liu Bei army advantage: $risk"
}
Assert-True ($effects -match 'hd_clear_yiling_risks_effect[\s\S]*?remove_character_modifier\s*=\s*hd_yiling_risk_supply_modifier') 'every Yiling terminal can remove applied risk modifiers'
Assert-True ($liuBeiEvents -match 'NOT\s*=\s*\{\s*exists\s*=\s*scope:hd_lb25_war\s*\}[\s\S]{0,260}?hd_clear_yiling_risks_effect') 'failed Yiling war creation immediately clears applied risks'
Assert-True ($worldEvents -match 'limit\s*=\s*\{\s*exists\s*=\s*scope:hd_chibi_war\s*\}[\s\S]{0,180}?else\s*=\s*\{[\s\S]{0,120}?hd_clear_chibi_risks_effect') 'failed Chibi war creation immediately clears applied risks'
Assert-True ($stories -match 'on_end\s*=\s*\{[\s\S]{0,240}?remove_global_variable\s*=\s*hd_fengying_world_open') 'Fengying story termination clears its open state'
Assert-True ($stories -match 'on_end\s*=\s*\{[\s\S]{0,240}?remove_global_variable\s*=\s*hd_lb24_world_open') 'LB24 story termination clears its open state'
Assert-True ($stories -match 'on_end\s*=\s*\{[\s\S]{0,240}?remove_global_variable\s*=\s*hd_lb25_world_open') 'LB25 story termination clears its open state'

foreach ($terminal in @('historical','nonhistorical','alternate_success','alternate_failure')) {
    Assert-True ($all -match "hd_chain_terminal_$terminal") "terminal class represented: $terminal"
}
Assert-True ($cb -match 'on_victory[\s\S]*?hd_historical_world_war_victory_effect') 'world-war victory feeds actual outcome handler'
Assert-True ($cb -match 'on_white_peace[\s\S]*?hd_historical_world_war_white_peace_effect') 'world-war white peace feeds actual outcome handler'
Assert-True ($cb -match 'on_defeat[\s\S]*?hd_historical_world_war_defeat_effect') 'world-war defeat feeds actual outcome handler'
Assert-True ($cb -match 'on_invalidated[\s\S]*?hd_historical_world_war_invalidated_effect') 'world-war invalidation feeds actual outcome handler'

foreach ($eventId in @('2510','2491','2492','2590','2591')) {
    Assert-True ($liuBeiEvents -match "hd_liu_bei_late\.$eventId\s*=\s*\{[\s\S]{0,220}?theme\s*=") "late Liu Bei event has a theme: $eventId"
}
Assert-MatchCount $loc '(?m)^\s*hd_chibi_risk_disease_modifier_desc:' 1 'Chibi disease modifier description key exists exactly once'
Assert-MatchCount $loc '(?m)^\s*hd_chibi_risk_expedition_modifier_desc:' 1 'Chibi expedition modifier description key exists exactly once'
Assert-True ($all -notmatch 'set_global_variable\s*=\s*hd_lb22_yizhou_success') 'unused Liu Bei state is no longer set: hd_lb22_yizhou_success'
foreach ($unusedFlag in @('hd_lb24_mi_fang_checked','hd_lb24_fu_shi_ren_checked','hd_lb24_aligned_with_cao','hd_lb22_kept_jingzhou_arrangement')) {
    Assert-True ($all -notmatch "add_character_flag\s*=\s*$([regex]::Escape($unusedFlag))") "unused Liu Bei flag is no longer set: $unusedFlag"
}
foreach ($unusedWaitingFlag in @('hd_lb24_story_waiting','hd_lb25_story_waiting')) {
    Assert-True ($all -notmatch [regex]::Escape($unusedWaitingFlag)) "unused waiting flag is fully removed: $unusedWaitingFlag"
}
Assert-True ($all -notmatch 'hd_lb22_liu_zhang_surrendered') 'read-never-set Liu Zhang surrender state is removed'

if ($script:Failures -gt 0) {
    Write-Host "FAILED: $script:Failures Phase 2 assertion(s)" -ForegroundColor Red
    exit 1
}

Write-Host 'PASSED: all Phase 2 historical world-chain assertions' -ForegroundColor Green
exit 0
