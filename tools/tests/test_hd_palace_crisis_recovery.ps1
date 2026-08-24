param()

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path

function Read-RepoFile([string]$Relative) {
    return Get-Content -LiteralPath (Join-Path $repo $Relative) -Raw -Encoding UTF8
}

function Assert-True([bool]$Condition, [string]$Name) {
    if ($Condition) { Write-Host "PASS: $Name" -ForegroundColor Green }
    else { Write-Host "FAIL: $Name" -ForegroundColor Red; $script:Failures++ }
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

$onActions = Read-RepoFile 'common\on_action\zz_hd_palace_crisis_on_actions.txt'
$effects = Read-RepoFile 'common\scripted_effects\zz_hd_palace_crisis_effects.txt'
$palace = Read-RepoFile 'events\zz_hd_palace_crisis_events.txt'
$antiRegent = Read-RepoFile 'events\zz_hd_anti_regent_events.txt'
$cao = Read-RepoFile 'events\zz_hd_cao_chain_events.txt'
$confederationTriggers = Read-RepoFile 'common\scripted_triggers\zz_hd_confederation_triggers.txt'
$confederationEffects = Read-RepoFile 'common\scripted_effects\zz_hd_confederation_effects.txt'
$confederationWars = Read-RepoFile 'common\casus_belli_types\zz_hd_confederation_wars.txt'
$script:Failures = 0

# This suite deliberately reads only active hd_* files. Disabled rp_* content is
# outside both the implementation contract and the assertion corpus.
foreach ($text in @($onActions, $effects, $palace, $antiRegent, $cao, $confederationTriggers, $confederationEffects, $confederationWars)) {
    Assert-True (Test-BraceBalance $text) 'active historical-chain script has balanced braces'
}

# The palace conclusion must prefer living Yuan Shao, but must have a real
# fallback dispatcher at the same decision point when he is already dead.
$palaceConclusion = Get-NamedBlock $palace 'hd_palace_crisis.0015'
Assert-True ($palaceConclusion -match 'if\s*=\s*\{\s*limit\s*=\s*\{\s*character:yuan_shao\s*\?=\s*\{\s*is_alive\s*=\s*yes\s*\}' -and $palaceConclusion -match 'trigger_event\s*=\s*\{\s*id\s*=\s*hd_palace_crisis\.0016' -and $palaceConclusion -match 'else\s*=\s*\{\s*hd_anti_regent_select_fallback_leader_effect\s*=\s*yes') 'palace conclusion uses a valid Yuan-first if/else dispatcher'

$leaderEligibility = Get-NamedBlock $confederationTriggers 'hd_valid_anti_regent_leader_trigger'
foreach ($requirement in @(
    'is_alive\s*=\s*yes',
    'is_adult\s*=\s*yes',
    'is_ruler\s*=\s*yes',
    'is_landed\s*=\s*yes',
    'is_imprisoned\s*=\s*no',
    'is_incapable\s*=\s*no',
    'highest_held_title_tier\s*>=\s*tier_duchy',
    'capital_province\s*=\s*\{\s*geographical_region\s*=\s*uuii_empire_han_region',
    'is_confederation_member\s*=\s*no',
    'NOT\s*=\s*\{\s*has_title\s*=\s*title:h_china\s*\}',
    'NOT\s*=\s*\{\s*has_title\s*=\s*title:e_han\s*\}',
    'NOT\s*=\s*\{\s*has_character_flag\s*=\s*hd_current_han_regent\s*\}',
    'NOT\s*=\s*\{\s*has_character_flag\s*=\s*hd_anti_regent_league_excluded\s*\}'
)) {
    Assert-True ($leaderEligibility -match $requirement) "fallback leader eligibility contains $requirement"
}

$fallbackSelector = Get-NamedBlock $effects 'hd_anti_regent_select_fallback_leader_effect'
Assert-True ($fallbackSelector -match 'any_ruler\s*=\s*\{[\s\S]*?hd_valid_anti_regent_leader_trigger\s*=\s*yes' -and $fallbackSelector -match 'random_ruler\s*=\s*\{[\s\S]*?hd_valid_anti_regent_leader_trigger\s*=\s*yes') 'fallback existence check and random selection share one eligibility trigger'
Assert-True (([regex]::Matches($fallbackSelector, 'NOT\s*=\s*\{\s*this\s*=\s*scope:hd_anti_regent_fallback_target\s*\}')).Count -eq 2) 'fallback existence check and random selection both exclude the current regent'
Assert-True ($fallbackSelector -match 'set_global_variable\s*=\s*\{\s*name\s*=\s*hd_anti_regent_pending_leader\s*value\s*=\s*this\s*\}' -and $fallbackSelector -match 'add_character_flag\s*=\s*hd_anti_regent_dispatch_ready' -and $fallbackSelector -match 'trigger_event\s*=\s*\{\s*id\s*=\s*hd_anti_regent\.0001\s*months\s*=\s*3\s*\}') 'fallback selection persists one leader and dispatches the existing opening event'
Assert-True ($fallbackSelector -match 'else\s*=\s*\{[\s\S]*?hd_palace_crisis_cleanup_effect\s*=\s*yes') 'no fallback candidate reaches terminal palace cleanup'

$yuanDispatch = Get-NamedBlock $palace 'hd_palace_crisis.0016'
Assert-True ($yuanDispatch -match 'global_var:hd_anti_regent_pending_leader\s*=\s*root' -and $yuanDispatch -match 'hd_yuan_move_to_bohai_effect\s*=\s*yes') 'living Yuan Shao keeps the original Bohai migration and coalition dispatch route'

$opening = Get-NamedBlock $antiRegent 'hd_anti_regent.0001'
Assert-True ($opening -notmatch 'this\s*=\s*character:yuan_shao' -and $opening -match 'global_var:hd_anti_regent_pending_leader\s*=\s*root' -and $opening -match 'has_character_flag\s*=\s*hd_anti_regent_dispatch_ready') 'coalition opening consumes the persisted dynamic leader instead of hardcoding Yuan Shao'
Assert-True ($opening -match 'has_character_flag\s*=\s*hd_yuan_bohai_arrived[\s\S]*?NOT\s*=\s*\{\s*exists\s*=\s*global_var:hd_anti_regent_pending_leader\s*\}[\s\S]*?set_global_variable\s*=\s*\{\s*name\s*=\s*hd_anti_regent_pending_leader\s*value\s*=\s*root\s*\}[\s\S]*?trigger_event\s*=\s*\{\s*id\s*=\s*hd_anti_regent\.0001\s*days\s*=\s*1\s*\}') 'legacy post-arrival saves backfill the dynamic dispatch token once'
Assert-True ($opening -match 'scope:hd_anti_regent_target\s*=\s*\{\s*add_character_flag\s*=\s*hd_current_han_regent\s*set_variable\s*=\s*\{\s*name\s*=\s*hd_anti_regent_leader\s*value\s*=\s*root\s*\}') 'coalition target records the dynamic leader for death cleanup'
Assert-True (([regex]::Matches($antiRegent, 'create_confederation\s*=')).Count -eq 1) 'anti-regent chain has exactly one confederation creation site'

foreach ($id in @('0002','0004','0100','0101','0200','0201')) {
    $block = Get-NamedBlock $antiRegent "hd_anti_regent.$id"
    Assert-True ($block -notmatch 'character:yuan_shao') "anti-regent node $id follows the selected leader dynamically"
}

$antiDeath = Get-NamedBlock $onActions 'hd_anti_regent_on_death'
Assert-True ($antiDeath -match 'global_var:hd_anti_regent_pending_leader' -and $antiDeath -match 'hd_anti_regent_select_fallback_leader_effect') 'pending selected leader death redispatches before coalition creation'
Assert-True ($antiDeath -match 'var:hd_anti_regent_leader[\s\S]*?hd_anti_regent_failure_effect') 'regent death resolves the persisted dynamic league leader'
$migrationDeath = Get-NamedBlock $onActions 'hd_historical_migration_on_death'
Assert-True ($migrationDeath -match 'this\s*=\s*character:yuan_shao[\s\S]*?hd_yuan_abort_bohai_migration_effect\s*=\s*yes[\s\S]*?hd_anti_regent_select_fallback_leader_effect\s*=\s*yes') 'Yuan migration death redispatches independently of child on-action order'

$secondWar = Get-NamedBlock $confederationWars 'hd_enter_the_passes_cb'
Assert-True ($secondWar -notmatch 'is_attacker\s*=\s*scope:attacker' -and $secondWar -match 'every_confederation_member\s*=') 'second-war contribution collection stays in character scope'
$callMembers = Get-NamedBlock $confederationEffects 'hd_call_league_members_to_all_offensive_wars_effect'
Assert-True ($callMembers -match 'save_temporary_scope_as\s*=\s*hd_league_member_to_call' -and $callMembers -match 'add_attacker\s*=\s*scope:hd_league_member_to_call') 'league war call preserves each dynamic member across the war iterator'
$enterChaos = Get-NamedBlock $confederationEffects 'hd_enter_dynastic_chaos_effect'
Assert-True ($enterChaos -match 'situation_top_sub_region\s*=\s*\{[\s\S]*?change_phase\s*=') 'dynastic-cycle transition changes the situation sub-region phase'

$queuedRecovery = Get-NamedBlock $effects 'hd_palace_recover_queued_effect'
Assert-True ($queuedRecovery -match 'remove_character_flag\s*=\s*hd_palace_crisis_controller[\s\S]*?remove_global_variable\s*=\s*hd_palace_crisis_queued[\s\S]*?hd_palace_crisis_queue_retry_used') 'pre-start recovery consumes ownership before its single retry'
Assert-True ($queuedRecovery -match 'else\s*=\s*\{[\s\S]*?hd_palace_crisis_cleanup_effect\s*=\s*yes') 'pre-start second failure reaches terminal cleanup'
$tryStart = Get-NamedBlock $effects 'hd_try_start_palace_crisis_effect'
Assert-True ($tryStart -match 'else\s*=\s*\{\s*hd_palace_crisis_cleanup_effect\s*=\s*yes\s*\}\s*\}') 'pre-start selection failure with no surviving candidate terminates cleanly'

foreach ($id in @('0001','0002','0003','0004','0005','0006','0007','0010','0015','0016')) {
    $block = Get-NamedBlock $palace "hd_palace_crisis.$id"
    Assert-True ($block -match 'on_trigger_fail\s*=\s*\{') "palace delayed node $id has a failure route"
}
foreach ($id in @('0005','0001','0002','0003','0004','0100','0200')) {
    $block = Get-NamedBlock $antiRegent "hd_anti_regent.$id"
    Assert-True ($block -match 'on_trigger_fail\s*=\s*\{') "anti-regent delayed node $id has a failure route"
}

$onDeath = Get-NamedBlock $onActions 'on_death'
foreach ($child in @('hd_palace_crisis_on_death','hd_anti_regent_on_death','hd_historical_migration_on_death')) {
    Assert-True ($onDeath -match [regex]::Escape($child)) "on_death dispatches $child"
}
Assert-True ($onActions -match 'hd_palace_recover_started_controller_effect' -and $onActions -match 'hd_palace_continue_after_he_jin_loss_effect') 'palace death callbacks share idempotent recovery effects'
Assert-True ($onActions -match 'hd_anti_regent_failure_effect') 'leader or target death terminates the anti-regent league'
Assert-True ($onActions -match 'hd_cao_abort_chenliu_migration_effect' -and $onActions -match 'hd_yuan_abort_bohai_migration_effect') 'migration death callback clears both Cao and Yuan travel locks'

$caoMove = Get-NamedBlock $effects 'hd_cao_move_to_chenliu_effect'
$yuanMove = Get-NamedBlock $effects 'hd_yuan_move_to_bohai_effect'
Assert-True ($caoMove -match 'on_travel_planner_cancel_event\s*=\s*hd_cao_chain\.0091') 'Cao travel registers its cancellation event'
Assert-True ($yuanMove -match 'on_travel_planner_cancel_event\s*=\s*hd_anti_regent\.0006') 'Yuan travel registers its cancellation event'
Assert-True ($caoMove -match 'on_travel_planner_cancel_event\s*=\s*hd_cao_chain\.0093') 'Cao retry travel owns a distinct terminal cancellation event'
Assert-True ($yuanMove -match 'on_travel_planner_cancel_event\s*=\s*hd_anti_regent\.0008') 'Yuan retry travel owns a distinct terminal cancellation event'

$caoCancel = Get-NamedBlock $cao 'hd_cao_chain.0091'
$caoRetry = Get-NamedBlock $cao 'hd_cao_chain.0092'
$caoTerminalCancel = Get-NamedBlock $cao 'hd_cao_chain.0093'
$yuanCancel = Get-NamedBlock $antiRegent 'hd_anti_regent.0006'
$yuanRetry = Get-NamedBlock $antiRegent 'hd_anti_regent.0007'
$yuanTerminalCancel = Get-NamedBlock $antiRegent 'hd_anti_regent.0008'
Assert-True ($caoCancel -notmatch 'hd_cao_chain\.0090' -and $yuanCancel -notmatch 'hd_anti_regent\.0005') 'travel cancellation never impersonates arrival'
Assert-True ($caoCancel -match 'hd_cao_cancel_chenliu_migration_effect' -and $caoRetry -match 'hd_cao_retry_chenliu_migration_effect') 'Cao cancellation uses a separated one-shot retry'
Assert-True ($yuanCancel -match 'hd_yuan_cancel_bohai_migration_effect' -and $yuanRetry -match 'hd_yuan_retry_bohai_migration_effect') 'Yuan cancellation uses a separated one-shot retry'
Assert-True ($caoTerminalCancel -match 'hd_cao_abort_chenliu_migration_effect' -and $caoTerminalCancel -notmatch 'hd_cao_chain\.0090') 'Cao retry cancellation terminates without faking arrival'
Assert-True ($yuanTerminalCancel -match 'hd_yuan_abort_bohai_migration_effect' -and $yuanTerminalCancel -notmatch 'hd_anti_regent\.0005') 'Yuan retry cancellation terminates without faking arrival'

$palaceCleanup = Get-NamedBlock $effects 'hd_palace_crisis_cleanup_effect'
Assert-True ($palaceCleanup -match 'remove_global_variable\s*=\s*hd_palace_crisis_queue_retry_used') 'palace terminal cleanup clears its retry guard'
Assert-True ($palaceCleanup -match 'remove_global_variable\s*=\s*hd_palace_crisis_started') 'palace terminal cleanup clears the active-chain lock'
$antiCleanup = Get-NamedBlock $effects 'hd_anti_regent_cleanup_effect'
Assert-True ($antiCleanup -match 'every_confederation_member\s*=\s*\{[^{}]*remove_character_flag\s*=\s*hd_anti_regent_league_member[^{}]*\}') 'anti-regent cleanup clears member flags before disbanding'
$caoAbort = Get-NamedBlock $effects 'hd_cao_abort_chenliu_migration_effect'
$yuanAbort = Get-NamedBlock $effects 'hd_yuan_abort_bohai_migration_effect'
Assert-True ($caoAbort -match 'remove_character_flag\s*=\s*hd_cao_callous_after_escape') 'Cao terminal cancellation clears its migration-chain marker'
Assert-True ($yuanAbort -match 'remove_character_flag\s*=\s*hd_yuan_bohai_arrived') 'Yuan death abort clears a pending post-arrival dispatch marker'
Assert-True ($yuanAbort -match 'global_var:hd_anti_regent_pending_leader\s*=\s*root[\s\S]*?remove_global_variable\s*=\s*hd_anti_regent_pending_leader') 'Yuan terminal abort releases its pending coalition dispatch token'

$allActive = $onActions + $effects + $palace + $antiRegent + $cao
Assert-True ($allActive -notmatch '(?m)^\s*rp_') 'disabled rp_* definitions are not pulled into the active recovery implementation'

if ($script:Failures -gt 0) {
    Write-Host "FAILED: $script:Failures palace-crisis recovery assertion(s)" -ForegroundColor Red
    exit 1
}

Write-Host 'PASSED: palace-crisis, anti-regent, and migration recovery assertions' -ForegroundColor Green
exit 0
