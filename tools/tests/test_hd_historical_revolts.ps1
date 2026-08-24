param()

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$effectPath = Join-Path $repo 'common\scripted_effects\zz_hd_historical_revolt_effects.txt'
$triggerPath = Join-Path $repo 'common\scripted_triggers\zz_hd_historical_revolt_triggers.txt'
$eventPath = Join-Path $repo 'events\zz_hd_historical_revolt_events.txt'
$cbPath = Join-Path $repo 'common\casus_belli_types\zz_hd_historical_revolt_cb.txt'
$nicknamePath = Join-Path $repo 'common\nicknames\zz_hd_historical_revolt_nicknames.txt'
$locPath = Join-Path $repo 'localization\simp_chinese\zz_hd_historical_revolts_l_simp_chinese.yml'
$nameListPath = Join-Path $repo 'common\culture\name_lists\zz_hd_historical_revolt_names.txt'
$hanHistoryPath = Join-Path $repo 'history\characters\east_asian_han_180_200.txt'
$qiangHistoryPath = Join-Path $repo 'history\characters\east_asian_qiang_180_200.txt'

$effects = Get-Content -LiteralPath $effectPath -Raw -Encoding UTF8
$triggers = Get-Content -LiteralPath $triggerPath -Raw -Encoding UTF8
$events = Get-Content -LiteralPath $eventPath -Raw -Encoding UTF8
$cb = Get-Content -LiteralPath $cbPath -Raw -Encoding UTF8
$nicknames = if (Test-Path -LiteralPath $nicknamePath) { Get-Content -LiteralPath $nicknamePath -Raw -Encoding UTF8 } else { '' }
$loc = Get-Content -LiteralPath $locPath -Raw -Encoding UTF8
$hanHistory = Get-Content -LiteralPath $hanHistoryPath -Raw -Encoding UTF8
$qiangHistory = Get-Content -LiteralPath $qiangHistoryPath -Raw -Encoding UTF8
$script:Failures = 0

function Assert-True([bool]$Condition, [string]$Name) {
    if ($Condition) { Write-Host "PASS: $Name" -ForegroundColor Green }
    else { Write-Host "FAIL: $Name" -ForegroundColor Red; $script:Failures++ }
}

function Assert-MatchCount([string]$Text, [string]$Pattern, [int]$Expected, [string]$Name) {
    $actual = [regex]::Matches($Text, $Pattern, [Text.RegularExpressions.RegexOptions]::Multiline).Count
    Assert-True ($actual -eq $Expected) "$Name (expected $Expected, got $actual)"
}

function Get-CharacterBlock([string]$Text, [string]$Id) {
    $match = [regex]::Match($Text, "(?ms)^$([regex]::Escape($Id))=\{.*?^\}")
    if (-not $match.Success) { return '' }
    return $match.Value
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

Assert-True (Test-BraceBalance $effects) 'scripted effects have balanced braces'
Assert-True (Test-BraceBalance $triggers) 'scripted triggers have balanced braces'
Assert-True (Test-BraceBalance $events) 'events have balanced braces'
Assert-True (Test-BraceBalance $cb) 'casus belli has balanced braces'

$ids = 1..9 | ForEach-Object { 'hd_historical_revolts.{0:d4}' -f $_ }
foreach ($id in $ids) {
    Assert-True ($events -match [regex]::Escape($id)) "event exists: $id"
}
Assert-MatchCount $events '^hd_historical_revolts\.\d{4}\s*=\s*\{' 9 'exactly nine revolt events'

$flags = @(
    'hd_revolt_jiaozhi_fired', 'hd_revolt_beigong_fired', 'hd_revolt_heishan_fired',
    'hd_revolt_jiangxia_fired', 'hd_revolt_wangguo_fired', 'hd_revolt_zhangchun_fired',
    'hd_revolt_bingzhou_hu_fired', 'hd_revolt_maxiang_fired', 'hd_revolt_yanbaihu_fired'
)
foreach ($flag in $flags) {
    Assert-True (($triggers + $effects) -match [regex]::Escape($flag)) "fired flag exists: $flag"
}

$windows = @(
    @('184.6.1','186.12.31'), @('184.10.1','186.12.31'), @('185.2.1','188.12.31'),
    @('185.4.1','187.12.31'), @('187.4.1','189.12.31'), @('187.6.1','189.12.31'),
    @('188.3.1','190.12.31'), @('188.6.1','190.12.31'), @('196.1.1','199.12.31')
)
foreach ($window in $windows) {
    Assert-True ($triggers.Contains("current_date >= $($window[0])") -and $triggers.Contains("current_date <= $($window[1])")) "window $($window[0]) through $($window[1])"
}

Assert-True ($effects -notmatch 'holder\s*\?=\s*\{\s*is_alive\s*=') 'no trigger used as an effect in holder scope'
Assert-True ($effects -match 'holder\s*=\s*scope:hd_revolt_defender' -and $cb -match 'target_top_liege_if_outside_realm\s*=\s*no') 'defender resolution uses the current direct holder without redirecting to the top liege'
Assert-True ($effects -notmatch 'dynasty\s*=\s*generate') 'anonymous revolt leaders are lowborn'
Assert-True (-not (Test-Path -LiteralPath $nameListPath)) 'obsolete empty revolt name list is absent'
Assert-True ($effects -match 'name\s*=\s*hd_jiaozhi_garrison_leader' -and $loc -match 'hd_jiaozhi_garrison_leader:0\s+"交趾屯帅"') 'Jiaozhi anonymous leader has a role name rather than a title as the personal name'
Assert-True ($nicknames -match '(?m)^nick_hd_zhutian_general\s*=\s*\{' -and $effects -match 'give_nickname\s*=\s*nick_hd_zhutian_general' -and $loc -match 'nick_hd_zhutian_general:0\s+"柱天将军"') 'Jiaozhi leader receives Zhutian General as a nickname'

Assert-True ($effects -match 'province:.*#.*Huangzhong|province:.*#.*湟中|title:b_[a-z0-9_]*huangzhong') 'Beigong primary spawn is Huangzhong'
Assert-True ($effects -match 'character:luan_ti_qiang_qu') 'Bingzhou revolt prioritizes Qiangqu political identity'
Assert-MatchCount $effects 'NOT\s*=\s*\{\s*scope:hd_revolt_leader\s*=\s*scope:hd_revolt_defender\s*\}' 9 'leaders cannot revolt against themselves'
Assert-True ($effects -match 'province:3295') 'Ma Xiang is hard-locked to Mianzhu province 3295'
Assert-True ($effects -match 'assign_commander\s*=\s*character:zhang_chun') 'Zhang Chun is primary commander'
Assert-True ($triggers -notmatch 'character:(bei_gong_yu|chu_yan|wang_guo|zhang_ju|bai_ma_tong|ma_xiang|yan_bai_hu)\s*=\s*\{\s*is_alive') 'historical leader survival is not an extra readiness blocker'

$leaderChecks = @(
    @($qiangHistory, 'bei_gong_yu', 'diplomacy="9"', 'martial="16"', 'intrigue="11"', 'learning="5"', 'prowess="14"', '149.10.1={'),
    @($hanHistory, 'chu_yan', 'diplomacy="8"', 'martial="17"', 'stewardship="8"', 'intrigue="12"', 'learning="5"', 'prowess="16"', '157.2.1={'),
    @($hanHistory, 'zhang_niu_jiao', 'martial="15"', 'intrigue="9"', 'prowess="15"', '147.2.1={'),
    @($hanHistory, 'zhang_ju', 'diplomacy="11"', 'martial="12"', 'stewardship="8"', 'intrigue="12"', 'learning="7"', 'prowess="9"', '147.6.1={'),
    @($hanHistory, 'zhang_chun', 'diplomacy="8"', 'martial="17"', 'stewardship="7"', 'intrigue="12"', 'learning="5"', 'prowess="15"', '151.6.1={'),
    @($hanHistory, 'bai_ma_tong', 'culture="xiongnu"', 'diplomacy="7"', 'martial="16"', 'stewardship="6"', 'intrigue="10"', 'learning="4"', 'prowess="15"', '152.3.1={'),
    @($hanHistory, 'ma_xiang', 'diplomacy="10"', 'martial="14"', 'stewardship="7"', 'intrigue="12"', 'learning="5"', 'prowess="12"', '154.6.1={'),
    @($hanHistory, 'yan_bai_hu', 'diplomacy="8"', 'martial="15"', 'stewardship="7"', 'intrigue="11"', 'learning="5"', 'prowess="15"', '158.1.1={')
)
foreach ($check in $leaderChecks) {
    $block = Get-CharacterBlock $check[0] $check[1]
    $ok = $block.Length -gt 0
    foreach ($needle in $check[2..($check.Count - 1)]) { $ok = $ok -and $block.Contains($needle) }
    Assert-True $ok "locked history data: $($check[1])"
}

$armyTotals = @(6000,18000,16000,12000,16000,18000,18000,15000,12000)
foreach ($total in $armyTotals) {
    Assert-True ($effects -match "#\s*TOTAL\s*=\s*$total\b") "documented and checked army total $total"
}
Assert-MatchCount $effects 'uses_supply\s*=\s*yes' 10 'all ten spawn branches use supply'
Assert-MatchCount $effects 'inheritable\s*=\s*no' 10 'all ten spawn branches are noninheritable'
Assert-True (([regex]::Matches($effects, 'war\s*=\s*scope:hd_revolt_war').Count + [regex]::Matches($effects, 'war\s*=\s*scope:hd_revolt_beigong_war').Count) -eq 10) 'all ten spawn branches are war-bound'
Assert-True ($effects -notmatch 'siege_weapon|onager|mangonel|trebuchet|bombard') 'no siege regiments in revolt armies'

Assert-True ($effects -match 'hd_historical_revolt_start_one_target_war_effect' -and $effects -match 'hd_historical_revolt_start_two_target_war_effect' -and $effects -match 'hd_historical_revolt_start_three_target_war_effect') 'war helpers exist before army spawning'

Assert-True ($effects -notmatch 'hd_revolt_war_targets') 'victory does not use a parallel non-war target list'
Assert-True ($effects -match 'hd_historical_revolt_start_two_target_war_effect\s*=\s*\{[\s\S]*?target_title\s*=\s*\$TARGET1\$[\s\S]*?target_title\s*=\s*\$TARGET2\$') 'two-title wars use repeated formal target_title entries'
Assert-True ($effects -match 'hd_historical_revolt_start_three_target_war_effect\s*=\s*\{[\s\S]*?target_title\s*=\s*\$TARGET3\$') 'three-title wars use repeated formal target_title entries'
Assert-True ($effects -match 'hd_revolt_wangguo_joined' -and $effects -match 'title:d_fufeng[\s\S]*?conquest_cb_title_transfer') 'Wang Guo join preserves Fufeng claim in the same war'
Assert-MatchCount $effects 'set_global_variable\s*=\s*hd_revolt_[a-z_]+_committed' 9 'nine launches enter committed state'
Assert-MatchCount $triggers 'NOT\s*=\s*\{\s*exists\s*=\s*global_var:hd_revolt_[a-z_]+_committed\s*\}' 9 'nine readiness triggers block duplicate committed launches'
Assert-True ($cb -match 'on_invalidated\s*=\s*\{[\s\S]*?hd_historical_revolt_war_ended_cleanup_effect') 'invalidation cleans temporary revolt state'
Assert-True ($cb -match 'on_white_peace\s*=\s*\{[\s\S]*?hd_historical_revolt_war_ended_cleanup_effect') 'white peace cleans temporary revolt state'
Assert-True ($cb -match 'on_defeat\s*=\s*\{[\s\S]*?hd_historical_revolt_war_ended_cleanup_effect') 'defeat cleans temporary revolt state'

if ($script:Failures -gt 0) {
    Write-Host "FAILED: $script:Failures Phase 1 assertion(s)" -ForegroundColor Red
    exit 1
}

Write-Host 'PASSED: all Phase 1 historical revolt assertions' -ForegroundColor Green
exit 0
