# 汉晋春秋 mod 宣战理由（CB）清单

生成于 2026-10-21。范围：`common/casus_belli_types/` 下全部 56 个文件、151 个 CB 定义。
原版 1.20.1.2 的 CB 目录在 `D:\SteamLibrary\...\game\common\casus_belli_types`，本清单以它为对照，区分「自制」「覆盖原版」「原版同步副本」。

图例：
- **UI** = 玩家/AI 可在宣战界面或 AI 自选；**脚本** = `valid_to_start = { always = no }` 或只由脚本 `start_war`，玩家与 AI 都不能手选。
- 花费里的「威望 / 金」指宣战时一次性支付；「无」= `cost = {}`。
- 「引用」只列 CB 目录之外的位置（脚本效果、触发器、事件、互动、派系、本地化）。本地化四语（simp_chinese/english/japanese/korean）一律只记为「本地化」。

---

## 一、天朝循环（乱世四阶段）自制 CB

阶段名：崩溃 `hd_collapse` → 群雄割据/斗争 `chaos`(struggle) → 鼎足对峙 `hd_standoff` → 治世含扩张期 `stability_expansion`。

### 1. hd_dc_tunbing_cb「吞并」——群雄割据期主力 CB
- 文件：`hd_dc_kit_cha_tunbing_cb.txt`　组：conquest　UI（AI 战略派发器也用）
- 解锁：斗争期；攻方为独立君主或摄政（`hd_court_independent_or_regent_trigger`）、有地、非佣兵/冒险者/骑士团（`cannot_be_vassal_or_liege`）、在天下内；守方独立且在天下内，最高领主不同；AI 尊汉者不攻天子（`hd_court_ai_respects_emperor_trigger`）；玩家须与守方接壤（AI 另有 `ai_only_against_neighbors`）。离开斗争期或攻方失地/变佣兵则战争作废。
- 花费：威望 = 守方持有县所在的**每个郡 200**（`hd_dc_tunbing_prestige_per_duchy`）× 斗争期折扣 0.4（`hd_cycle_war_cost_mult_value`）。守方是被挟持的天子时，按权臣持有的郡计价。
- 效果：战斗分上限 200%，占领分上限 10%，首都与俘虏照原版算分。胜利：守方本人持有的全部头衔（霸权头衔除外）归攻方，封臣归属交引擎；守方是被挟持天子时改以权臣为结算对象；威望经验 medium，停战为原版胜利停战。
- 引用：`scripted_effects/hd_strategic_ai_effects.txt:221-234`（战略 AI `can_declare_war`/`start_war`）；`zz_hd_chinese_consolidation_cb.txt` 注释；本地化（zz_tr_hd_dc_kit_taoni、hd_dc_kit_taoni）。

### 2. chinese_consolidation_cb「逐鹿中原/统一」——对峙期（覆盖原版）
- 文件：`zz_hd_chinese_consolidation_cb.txt`（覆盖 `10_tgp_china_wars.txt`）　组：celestial　UI
- 解锁：**仅鼎足对峙期**；不能是持「蒙古入侵」故事的 AI；AI 另需「有 conqueror 变量/汉文化/游牧且想征服中国」之一；攻方须邻接（含隔水）持霸权 `h_china` 的帝国；守方须在天命局势内，且 AI 尊汉者不攻天子。目标限接壤的郡（duchy 级）；目标郡内有「刚遭劫掠」县则 5 年内不能再打。
- 花费：虔诚（同信仰 100 + 10×领地大小，上限 800，× 通用虔诚乘数）与威望（异信仰 150 + 10×领地大小，上限 800）两项，均乘 `hd_cycle_consolidation_cost_mult_value`（斗争 ×0.4 / **对峙 ×3**）。
- 效果：战争约 2 年见分晓（`defender_ticking_warscore 0.15`、3 个月延迟）。胜利：只转让目标郡内守方疆域的县（郡头衔若在其疆域内一并转让），守方疆域内其余被攻方占领的县按「边境劫掠」掠夺（金币/控制度/发展度/建筑，5 年冷却）；调 `hd_cycle_count_conquest_effect`（夺 ≥5 县触发对峙→斗争诱因）；AI 若没有夺天命故事则创建 `story_take_mandate_of_heaven`。
- 引用：`scripted_effects/hd_cycle_catalyst_effects.txt:178`、`hd_strategic_ai_effects.txt:253,258`、`zz_hd_chinese_consolidation_effects.txt`、`scripted_triggers/zz_hd_chinese_consolidation_triggers.txt`、`story_cycles/zz_hd_story_take_mandate_guards.txt:118`；原版 `10_tgp_china_wars.txt` 内还有一份已被覆盖的旧定义（已改为只在对峙期可用）。

### 3. hd_strategic_annex_cb「兼并」——已停用
- 文件：`hd_cycle_luanshi_wars.txt`　组：celestial
- `allowed_for_character` 首行 `always = no`，`ai_score_mult = 0`，战略 AI 已改用吞并。保留定义（含 300 威望×折扣的花费、夺目标战略区内伯爵领的效果）是死代码。
- 引用：只有本地化与 `hd_dc_kit_cha_tunbing_cb.txt` 注释。

### 4. hd_siyi_raid_cb「四夷入寇」
- 文件：`hd_cycle_luanshi_wars.txt`　组：conquest　UI（AI 评分 1，只打邻居）
- 解锁：斗争期；攻方独立且**非汉文化**（`hd_cycle_non_han_trigger`）；守方在天下内；目标为法理在 `h_china` 之下的郡（duchy 级），且该郡内守方有县。
- 花费：威望 300（`hd_siyi_raid_prestige_cost`）× 通用乘数。
- 效果：胜利夺目标郡及封臣；`hd_occupation_settle_effect`（战时占领的县一并夺取）；按郡内每县发展度，攻方得威望×20，若是游牧再得牧群×30；`hd_cycle_count_conquest_effect`；**停战 1 年**。白和/败则清占领记录。
- 引用：`character_interactions/hd_dc_kit_cha_interactions.txt:5,768`（「请求入侵」互动 `casus_belli = hd_siyi_raid_cb`）、`scripted_effects/hd_dc_kit_hook_effects.txt:74`、`hd_occupation_effects.txt`、`scripted_triggers/hd_cycle_phase_triggers.txt:120`（占领战争判定）、`events/hd_dc_kit_cha_events.txt`、本地化。

### 5. hd_dc_cha_border_raid_cb「边境劫掠」——斗争期
- 文件：`hd_dc_kit_cha_casus_belli.txt`　组：celestial　UI（AI 评分 0.5）
- 解锁：斗争期且攻方在天下内、有地、非冒险者；守方在天下内且与攻方（或攻方主君）陆上接壤、最高领主不同；目标为接壤的一个县。
- 花费：**无**。
- 效果：不夺地。胜利：守方付金 = 50 + 守方领地大小×5（上限 400，且不超过守方现金），守方失威望 100、攻方得 100，守方对攻方出「被劫掠」好感修正；**单向停战 730 天**；贡献者各得小量威望与好感。攻方死亡则作废。
- 引用：只有本地化（zz_tr_hd_dc_kit_cha）。

### 6. hd_dc_sta_border_clash_cb「边境郡小冲突」——对峙期
- 文件：`hd_dc_kit_sta_casus_belli.txt`　组：celestial　UI（AI 评分 1，只打邻居）
- 解锁：对峙期；攻方为独立君主、有地、非冒险者；守方在天下内且陆上接壤；目标为守方的一个郡，郡内守方有县且郡与攻方领土接壤。
- 花费：**威望 150 + 金 100**。
- 效果：胜利取「战争结束时由攻方占领」的该郡内县；**单向停战 1825 天（5 年）**；威望经验 minor。
- 引用：只有本地化。

### 7. hd_dc_exp_frontier_cb「开边」——扩张期
- 文件：`hd_dc_kit_exp_cb.txt`　组：celestial　UI（只对邻居；AI 评分 50 + 对方每个邻接县 60，对方比天子强则 ×0.1）
- 解锁：仅**天子**（持 `h_china`）在**扩张期**；守方为独立君主、天下之外、且不是天子的朝贡国；守方至少一县与天子疆域相邻。
- 花费：威望 500（`hd_dc_exp_frontier_prestige_cost`）。
- 效果：胜利调 `hd_dc_exp_frontier_victory_effect`（取对方与天子接壤的郡中属对方疆域的县），**停战 10 年**（胜/白/败皆然），并发射 `catalyst_hd_frontier_victory`。天子易位则作废。
- 引用：只有本地化。

### 8. hd_dc_demand_independence_war「要求独立」被拒后的独立战争
- 文件：`hd_dc_kit_independence_cb.txt`　组：independence　**脚本**（`ai = no`）
- 解锁：攻方有地且最高头衔 ≥ 县，守方是其直属主君；`scope:attacker.liege != defender` 则作废。
- 花费：威望 0。
- 效果：胜利：攻方独立，**各层级封臣全部随之独立**，攻方得 3 年「刚独立」标记 `hd_dc_recently_independent`，**停战 1825 天**。
- 引用：`scripted_effects/hd_dc_kit_taoni_effects.txt:44`（被拒后 `start_war`）、本地化（simp_chinese）。

### 9. hd_dc_taoni_cb「讨逆」
- 文件：`hd_dc_kit_taoni_cb.txt`　组：vassalization　UI
- 解锁：攻方有地；守方独立，且其主头衔上带 `hd_dc_taoni_rebel` 叛离标记，标记值头衔的现任持有者正是攻方（原主君，或其继承者）。原主君头衔易手或叛离者不再独立则作废。
- 花费：威望 0。
- 效果：`hd_dc_kit_taoni_victory_effect`：对方连同领地重新臣服，本人下狱；停战沿原版内战 1825 天。
- 引用：`scripted_effects/zz_hd_22_history_effects.txt:713`、`hd_dc_kit_taoni_effects.txt`（授标记）；本地化。

### 10. hd_dc_ten_qingjunce_cb「清君侧」——紧张期
- 文件：`hd_dc_kit_ten_cb.txt`　组：civil_war　**脚本**（互动 `hd_dc_ten_qingjunce_interaction` 或党锢「一网打尽」反弹）
- 解锁：攻方身上有 `var:hd_dc_ten_qjc_target`（指名权臣）；守方持 `h_china` 且是攻方的主君。宣战时变量转存到战争上。
- 花费：无。
- 效果：不涉及领地。胜：权臣罢官下狱，攻方次日成为天子的终身辅政（摄政）；败：攻方下狱。`on_primary_attacker_death = invalidate`。
- 引用：`scripted_effects/hd_dc_kit_ten_effects.txt:614`，本地化。

### 11. hd_collapse_warlord_war「军阀称帝」——崩溃期
- 文件：`hd_collapse_warlord_war.txt`　组：civil_war　UI（派系战争）
- 解锁：攻方正在领导 `hd_collapse_warlord_faction`；守方是该派系特殊头衔现持有者。
- 花费：无（派系战争）。
- 效果：套用原版 claimant 派系战争的结算（`on_claimant_faction_war_win_common`），胜利拥立者夺霸权头衔；停战 1825 天；败则派系崩溃、攻方失势。攻方分数比例 0.8。
- 引用：`common/factions/hd_collapse_warlord_faction.txt:4`、`scripted_triggers/hd_collapse_crisis_triggers.txt:33,54`、`hd_dc_kit_col_triggers.txt:8`、本地化。

### 12. hd_court_fengzhao_cb「奉诏讨伐」
- 文件：`hd_court_fengzhao_cb.txt`　组：conquest　UI（只对邻居）
- 解锁：**乱世（斗争/对峙）**；攻方为独立君主或摄政、有地；授权来自 `var:hd_court_fengzhao_target`（「令征伐」「求诏讨伐」授予，5 年；令征伐时双方互得此 CB）；守方独立且不是天子，与攻方最高领主不同；目标为郡，且郡内有守方之国的县。
- 花费：**免费**。
- 效果：胜利取该郡内守方之国持有的县（及郡头衔，若在其国内），清掉授权变量，威望经验 medium；败则付小额赔偿。停战与赔偿沿用原版征服标准。
- 引用：只有本地化（zz_tr_hd_court）。授权变量由乱世霸权的互动/事件写入（见 `docs` 乱世霸权草案）。

### 13. hd_court_taocuan_cb「讨篡」
- 文件：`hd_court_taocuan_cb.txt`　组：conquest　UI
- 解锁：攻方为 `hd_court_warlord_trigger`（独立、有地、天朝政体、非天子、在天下内）；`title:h_china.var:hd_court_usurper` 存在（权臣篡位后 10 年内）；守方正是该篡位者且持 `h_china`。
- 花费：**威望 500**。
- 效果：胜利：威望经验 major，攻方触发 `hd_court.0022`（讨篡者取天命交接）；战斗分上限 200%，首都/俘虏给分。
- 引用：只有本地化。

### 14. hd_cao_fengying_cb「奉迎天子」——曹操
- 文件：`zz_hd_cao_fengying_wars.txt`　组：civil_war　**脚本/限曹操**
- 解锁：攻方满足 `hd_cao_fengying_actor_valid_trigger`、带 `hd_cao_fengying_authorized` 标记、且无「董卓后过渡」；守方满足 `hd_cao_fengying_target_trigger`（持天子者或天子本人）。目标/攻方失效时作废但授权保留，可以对新目标再打。
- 花费：无。
- 效果：胜利 `hd_cao_fengying_victory_effect`（天子东归）并向全局发 `hd_world_news.0012`；白和/败为「无胜负」描述。主攻方/主守方死亡都作废。
- 引用：`scripted_effects/zz_hd_historical_war_effects.txt:198,200`、`scripted_triggers/zz_hd_historical_war_triggers.txt:70,75,80`、本地化。

---

## 二、史实剧本 CB（多为脚本专用）

### 15. hd_historical_war_cb「史实战争（184 年起）」
- 文件：`zz_hd_historical_war_cb.txt`　组：conquest　**脚本**；无花费
- 效果：胜利 `conquest_cb_title_transfer`，夺封臣和头衔，`hd_occupation_settle_effect`（战时占领一并夺取），`hd_historical_world_war_victory_effect`；无完全占领自动胜利。
- 引用：`scripted_effects/hd_occupation_effects.txt`、`zz_hd_lbxz_effects.txt:1149,1155`、`zz_hd_lubu_exile_effects.txt:458-467`、`scripted_triggers/hd_cycle_phase_triggers.txt:121`、`events/zz_hd_historical_world_events.txt`（8 处），`zz_hd_sg218_war_cb.txt` 注释。

### 16. hd_historical_revolt_cb「史实地方叛乱」
- 文件：`zz_hd_historical_revolt_cb.txt`　组：civil_war　**脚本**（月度脉冲）；无花费
- 效果：9 场 184–196 年地方叛乱共用。胜利 `hd_historical_revolt_victory_effect` + `hd_wuhu_xiutu_war_ended_effect`；叛军首领初为无地冒险者，用战争绑定的事件兵。
- 引用：`scripted_effects/zz_hd_historical_revolt_effects.txt:378-418`、`zz_hd_wuhu_effects.txt:1037`、`customizable_localization/zz_hd_historical_revolt_custom_loc.txt:67`、本地化。

### 17. hd_yellow_turban_rebellion_war「黄巾起义」
- 文件：`zz_hd_yellow_turban_war.txt`　组：civil_war　**脚本**（184 开局事件）；无花费
- 效果：胜利 `hd_uprising_grant_independence_effect` + `hd_yellow_turban_war_victory_effect`；张角起为无地冒险者，兵由事件给。主攻方死亡则作废。
- 引用：`zz_hd_yellow_turban_effects.txt:132-206`、`zz_hd_liu_bei_aftermath_effects.txt:71-111`、`scripted_triggers/zz_hd_uprising_war_triggers.txt:4,43`、`hd_han_clothing_pool_triggers.txt:403`、本地化。

### 18. peasant_war / populist_war（覆盖原版）
- 文件：`zz_hd_uprising_wars.txt`（覆盖 `00_civil_war.txt`；`05_fp3_wars.txt` 另有同名引用）　组：civil_war　派系入口（UI/派系）
- 解锁：`peasant_war` 攻方为农民派系领袖、非冒险者；`populist_war` 为平民/升级农民派系领袖。
- 效果：宣战给守方「起义」好感与合法性损失、触发 struggle 诱因、按郡修正生成兵；胜利先调 `hd_uprising_settle_occupied_counties_on_victory_effect`（占领的县只在胜利时结算），再 `hd_uprising_grant_independence_effect`，派系成员对守方停战 1825 天，派系解散。
- 引用：`scripted_triggers/hd_cycle_phase_triggers.txt:112-113`（派系战争判定）、`hd_collapse_crisis_triggers.txt:46`、`character_interactions/zz_hd_dc_kit_cha_fp2_interactions.txt:472,965`、`on_action/war_on_actions.txt`、`combat_on_actions.txt`、`00_war_effects.txt`、`00_war_and_peace_triggers.txt`、`events/factions/faction_demands.txt`、本地化。

### 19. hd_li_jue_changan_cb「李傕攻长安」
- 文件：`zz_hd_dong_aftermath_wars.txt`　组：civil_war　**脚本，限李傕**
- 解锁：攻方为李傕；`hd_li_jue_war_pending/active` 全局变量存在且未结束；守方持 `d_jingzhao`。
- 效果：胜利 `hd_li_jue_victory_effect`；若主守方是吕布则保护其旧部（张辽/高顺/陈宫）并让吕布流亡 `hd_lbx_begin_exile_effect`。主攻/守死亡则作废。
- 引用：`events/zz_hd_dong_aftermath_events.txt:89,91`、本地化。

### 20. hd_confederation_subjugation_cb「联盟降服」与 hd_anti_regent_punitive_cb「讨权臣」
- 文件：`zz_hd_confederation_wars.txt`
- hd_confederation_subjugation_cb（组 subjugation）：攻方是汉防御联盟盟主（`hd_league_leader`），守方是其下未入邦联、最高头衔低于王国的封臣；花费**威望 150**；胜利得威望 100，触发 `hd_confederation.0600`。引用：仅本文件（原生 UI），无外部引用。
- hd_anti_regent_punitive_cb（组 civil_war）：攻方带 `hd_anti_regent_league_leader` 且是讨伐联盟成员；守方带 `hd_current_han_regent`；无花费；胜利奖励胜方参战者，首胜调 `hd_anti_regent_first_war_victory_effect`。引用：`zzzzzz_hds_core_effects.txt:73`、`zzzzzz_hds_sun_effects.txt:8`、`zz_hd_anti_regent_lifecycle_effects.txt`、`zz_hd_anti_regent_membership_effects.txt`、`zz_hd_confederation_effects.txt:480`、`zz_hd_liu_bei_aftermath_effects.txt`。

### 21. hd_cao_expansion_cb「曹操扩张」与 hd_yuan_expansion_cb「袁绍扩张」
- 文件：`zz_hd_cao_expansion_cb.txt`、`zz_hd_yuan_expansion_cb.txt`　组：invasion　**脚本**（60 天控制器；`ai_score_mult 0`）；花费 0
- 曹：攻方只能是曹操（在世、有地、有 `hd_cao_expansion_region`、无菜单待决）；目标为州内一个郡（duchy），不同郡可并行开战；胜利 `hd_cao_expansion_victory_effect`。
- 袁：攻方只能是袁绍；目标由个人故事变量 `hd_yuan_expansion_region` 白名单限定（3 王国 + 7 郡）；胜利 `hd_yuan_expansion_victory_effect`。
- 引用：`zz_hd_cao_expansion_effects.txt:115-252`、`zz_hd_yuan_expansion_effects.txt:121-189`、`zz_hd_yuan_expansion_triggers.txt:121`；本地化。

### 22. hd_yuan_jizhou_cb「公孙瓒入冀州」
- 文件：`zz_hd_yuan_jizhou_wars.txt`　组：conquest　**脚本，限公孙瓒 vs 韩馥**；花费 0
- 解锁：攻方公孙瓒、持幽州、带 `hd4_jizhou_authorized`，`hd4_jizhou_finished` 未设；目标 `k_uuii_jizhou`，守方韩馥须持该州。
- 效果：胜利夺冀州王国及其封臣，设全局 `hd4_jizhou_finished`，`hd_yuan_jizhou_end_effect`。袁绍死/韩馥交州则作废。
- 引用：`zzzzzz_hd4_gongsun_effects.txt:59-228`、`zz_hd_yuan_jizhou_triggers.txt:45`、`zz_hd_yuan_expansion_triggers.txt:121-122`、本地化。

### 23. hd4_guandu_cb「官渡」与 hd4_tao_xuzhou_cb「陶谦徐州」
- 文件：`zzzzzz_hd4_guandu_cb.txt`　组：conquest　**脚本**；花费 0
- hd4_guandu_cb：攻方曹操（带 `hd4_guandu_authorized`）、守方袁绍；`h_china` 上要有「北方只剩两家」公告变量、官渡未打过；目标为 `hd4_guandu_targets` 名单里的郡。宣战时全局通报 `hd_world_news.0013`，清除曹袁历史和平好感。胜利 `hd4_guandu_victory_effect`。
- hd4_tao_xuzhou_cb：攻方须陶谦且 `hd4_tao_can_campaign_trigger`；守方是非陶谦的有地者；目标为有效郡。胜利 `hd4_target_conquest_effect` + 保护新封臣。
- 引用：`zzzzzz_hd4_guandu_effects.txt:61`、`zzzzzz_hd4_guandu_targets_generated.txt`（513 处，目标名单）、`zzzzzz_hd4_tao_effects.txt:292-422`、本地化（replace）。

### 24. hds_regional_cb、hds_wu_invasion_cb「孙家入吴/丹阳」
- 文件：`zzzzzz_hds_wars.txt`、`zzzzzzzz_hds_sun_danyang_war_override.txt`（覆盖 hds_wu_invasion_cb）　组：conquest　**脚本**；花费 0
- hds_regional_cb：独立有地的 `hds_regional_actor_trigger` 者，需 `hds_launch_authorized`，目标为 `var:hds_requested_duchy`；胜利 `hds_cb_victory_effect`。
- hds_wu_invasion_cb（现行版本=覆盖版）：攻方可为孙策（`wj_hchar_sun_ce`）、孙坚或接续的孙权；目标限 `d_danyang`；胜利除通用效果外**攻方 +3000 威望**；`landless_attacker_needs_armies = no`。
- 引用：`zzzzzzzzzzz_hds_sun_rework_effects.txt:189-252`、`zzzzzzzz_hds_sun_danyang_override.txt:113,122`、`zzzzzz_hds_war_effects.txt`、`zz_hd_sun_ce_war_diag_effects.txt`、`zzzzzz_hds_triggers.txt:114`、`zzzzzzzzzzz_hds_sj_triggers.txt:85`、`zzzzzzzzzz_hds_20260919_campaigns.txt`、本地化（replace）。

### 25. 218 剧本：hd_sg218_war_cb、hd_sg218_baiyi_cb、hd_sg218_xiangfan_cb
- 文件：`zz_hd_sg218_war_cb.txt`　组：conquest　**脚本**；无花费
- 通用版：胜利夺主目标及 `hd_sg218_extra_targets`（战争变量里的额外郡）及封臣；结局调 `hd218_war_result_effect`，设全局标记 `hd_sg218_<场次>_won/_lost/_white/_invalid`。
- baiyi（白衣渡江）：胜利改为整个荆州：荆州王国头衔、守方在荆州法理内的郡县、守方名下全部封臣一并归孙权；调试日志 `HD218 BAIYI WHOLE_JINGZHOU_TRANSFERRED`。
- xiangfan（襄樊）：与通用版结算相同，仅战争名不同。
- 引用：`zz_hd_218_history_effects.txt:6,57,431,779,847-896`、`zz_hd_218_startup_effects.txt:1307-1340`、本地化。`hd_historical_war_cb` 同族。

### 26. hd253_beifa_cb、hd253_beifa_opening_cb、hd253_history_war_cb（253 姜维北伐）
- 文件：`zz_hd_253_beifa_cb.txt`、`zz_hd_253_history_war_cb.txt`
- hd253_beifa_cb（组 celestial，UI，AI 评分 1 但守方兵力 > 己方 2 倍则 0）：攻方为 253 开局蜀汉梁州/汉中都督、汉帝封臣（`hd253_beifa_attacker_trigger`）且无「北伐休整」修正；守方为魏国境内郡级以上封臣、不打天子；目标为接壤县；**花费威望 50**。宣战 30 天后触发 `hd253.0100`（羌胡响应）、240 天后 `hd253.0110`（粮尽）；胜利取目标县，触发 `hd253.0120`，调 `hd253_beifa_end_effect`。战后停战两年 + 北伐冷却。
- hd253_beifa_opening_cb（脚本，开局「姜维出洮西」专用）：`valid_to_start = no`，可打郡级目标，花费同上（脚本宣战实际不扣），事件与结局同北伐。
- hd253_history_war_cb（脚本）：诸葛恪围新城等史实场次；花费无；胜利只转目标头衔，调 `hd253_war_result_effect`。
- 引用：`zz_hd_253_startup_effects.txt:973`、`zz_hd_253_history_effects.txt:9-69`、`zz_hd_263_history_effects.txt:6-286`、`zz_hd_253_events.txt`、`scripted_triggers/zz_hd_263_triggers.txt:16,21`、本地化。

### 27. hd_89_war_cb（89 窦宪北伐）、hd_nbc_war_cb（南北朝剧本）
- 文件：`zz_hd_89_war_cb.txt`、`zz_hd_nbc_war_cb.txt`　组：conquest　**脚本**；无花费
- hd_89_war_cb：胜利**不转头衔**，只设全局 `hd_89_<场次>_won/…`，`hd_89_war_result_effect`。
- hd_nbc_war_cb：胜利转目标头衔与封臣，清被灭之国的 `hd_nbc_style` 与国号；结局 `hd_nbc_war_result_effect`。
- 引用：89：`zz_hd_89_history_effects.txt:4-141`；nbc：`zz_hd_nbc_history_effects.txt`、`zz_hd_nbc_startup_effects.txt`、`zz_hd_304/370/531_history_effects.txt`、`events/zz_hd_nbc_events.txt:62`、本地化。

---

## 三、入侵/迁徙/起义 CB

### 28. hd_hi_invasion_cb「历史入侵」
- 文件：`zz_hd_hi_cb.txt`　组：event　**脚本**；无花费
- 效果：目标为当前阶段一个郡；胜利夺守方在本阶段所有郡内伯爵领（玩家封臣豁免）；`hd_hi.2001`。战争分上限 200，占领分上限 25/150。攻方死亡作废。
- 引用：`zz_hd_hi_effects.txt:499,506,772`、`zz_hd_hi_triggers.txt:32`、本地化。

### 29. hd_wuhu_petition_cb「胡帅求地」、hd_wuhu_chanyu_cb「大单于起兵」
- 文件：`zz_hd_wuhu_cb.txt`　组：event　**脚本**；无花费
- petition：目标为郡或县；胜利给地并让胡帅独立，写内附标记；`truce_days 3650`。
- chanyu：目标为王国；胜利取目标王国法理内守方的郡与县（玩家封臣豁免），独立，触发 `hd_wuhu.4001`（取得/创建王国、国号）。
- 引用：`zz_hd_wuhu_effects.txt:153,693,700,876-906`、`zz_hd_hi_cb.txt:2`、本地化。

### 30. hd_liao_migration_cb「僚人入蜀」
- 文件：`zz_hd_liao_cb.txt`　组：invasion　**脚本**（`ai = no`，年度脉冲宣战）；花费在决定里
- 解锁：攻方带 `hd_liao_undertaking`；目标固定 `k_uuii_yizhou`；守方在 `hd_liao_target_region` 内有县。
- 效果：宣战时设全局 `hd_liao_migration_launched`、生成迁徙军；胜利：独立、夺该区域内守方土地、`hd_liao_migration_effect`（迁都、首都改僚文化、僚化故事）。攻方升到帝国级则作废。
- 引用：`zz_hd_liao_effects.txt:145`、本地化。

### 31. hd_yiguan_uprising_cb「义军起义」、hd_yiguan_guinan_cb「举州归南」
- 文件：`zz_hd_yiguan_cb.txt`　**脚本**；无花费
- uprising（civil_war）：目标为县；胜利 `hd_yiguan_uprising_victory_effect`；完全占领即胜。
- guinan（independence）：目标 none，胜利 `hd_yiguan_guinan_victory_effect`（沦陷区汉人封臣改投接壤南方宗主）。
- 引用：`zz_hd_yiguan_war_effects.txt:60-86,279,285`、`zz_hd_yiguan_triggers.txt:218`、本地化。

---

## 四、烛广「教化」与「雪耻」CB

文件：`zgrc_cb_types.txt`，组 `zgrc_jiaohua_cb_group`，三条均为 **UI**；引用只有本地化（zz_tr_zgrc_war / zgrc_war）。触发器在 `scripted_triggers/zgrc_scripted_triggers.txt`。

### 32. zgrc_county_rangyi_cb「攘夷·夺县」
- 解锁：攻方 `zgrc_can_use_jiaohua_cb_trigger`（主君为「华夏礼乐」文化，或通汉语且有儒学教育；且 rite 有 `zgrc_jiaohua_cb_enabled`）、非冒险者；守方是「蛮夷」（`zgrc_is_manyi_character_trigger`：文化无「华夏礼乐」传统，主君亦无，且不是「通汉语 + 尊王攘夷」者）；两者最高领主不同、非上下级。目标为接壤的县，且持有者为蛮夷。
- 花费：同信仰：虔诚 25 + 5×领地大小（上限 75）；异信仰：威望 50 + 5×领地大小（上限 100）。均乘通用乘数。
- 效果：原版夺县结算，威望经验 minor，停战，战分 150%。

### 33. zgrc_duchy_rangyi_cb「攘夷·夺郡」
- 解锁：同上，另需合法性等级 ≥ 4 才在界面显示；目标为郡，郡内有邻县；AI 另需守方在该郡至少 2 个县。
- 花费：同信仰：虔诚 100 + 10×领地大小（上限 800）并加 `common_cb_impious_piety_cost`；异信仰：威望 150 + 10×领地大小（上限 800），与 fp2 斗争的文化敌意折扣/妥协加价照原版公国征服。
- 效果：原版夺郡结算（郡及封臣），威望经验 medium。

### 34. zgrc_dafuchou_cb「大复仇」
- 解锁：攻方对守方持「不共戴天」好感修正（`zgrc_bugongdaitian_opinion`，该修正自带合法囚禁/处决理由）；非冒险者；守方是君主；最高领主不同、非上下级；目标只能是守方首都。关系被清则开战后作废。
- 花费：无。
- 效果：胜利**不夺地，只囚禁守方**；若守方位在帝国级以上，75% 概率获绰号「烈丈夫」`nick_zgrc_liezhangfu`。

---

## 五、覆盖/修改了原版的 CB

| CB | 位置 | 改动 |
|---|---|---|
| vassalization_cb | `00_vassalization.txt` | 斗争/对峙期汉地统治者可发动；乱世不要求 struggle 卷入；花费 × `hd_cycle_vassalization_cost_mult_value`（斗争 0.4 / 对峙 5） |
| county_conquest_cb、duchy_conquest_cb、ducal_conquest_cb | `00_conquest.txt` | 虔诚与威望花费均 × `hd_dc_sta_conquest_cost_mult_value`（**对峙期且守方在天下内 ×2**）；氏族判定换成 `dm_compat_uses_house_unity_trigger` |
| claim_the_mandate_cb | `10_tgp_china_wars.txt` | 崩溃期也可用；胜利改调窄版 `hd_transfer_mandate_to_claimant_effect`（不再整套重组） |
| chinese_consolidation_cb | `zz_hd_chinese_consolidation_cb.txt` | 见 §1 条 2 |
| chinese_reunification_cb | 三个文件同名：原版 `10_tgp_china_wars.txt`、`zzzz_hd_unification_wars.txt`（自制「区域统一」版）、`zzzzzz_hd_removed_chinese_reunification_cb.txt` | 加载顺序最后者生效 = **已退役版**（`always = no`，进行中的战争直接作废）；`zzzz_` 的统一版实际被盖掉，是死定义 |
| silk_road_vassalization_cb、grand_campaign_kingdom_invasion_cb | `10_tgp_china_wars.txt` | 丝路判定改用 UUII 全局变量 `uuii_silk_road_enabled` 与三段相位 |
| liberty_faction_war 等 | `00_civil_war.txt` | 增补行政/部落政体胜利描述 |
| retaliation_cb、domination_cb、de_jure_cb_nomadic | `zz_dm_obedience_mpo_wars.txt`（覆盖 `09_mpo_wars.txt`） | 仍限游牧/草原行政特权；`09_mpo_wars.txt` 里对游牧 CB 的 HD 改动（游牧胜后保持游牧、不换政体/不迁都、`sub_realm_size > 80`、需王国级）对这三条被覆盖不生效，其余 mpo CB 仍生效 |
| invasion_war、clan_invasion_war 等 | `00_invasion_war.txt`、`00_subjugation.txt`、`05_fp3_wars.txt` | 氏族判定换 `dm_compat_uses_house_unity_trigger` |
| 宗教战争/ep3 战争中的俘虏处理 | `00_religious_war.txt`、`07_ep3_wars.txt` | 加入 `hd_dc_begin_protection_positive_imprisonment_effect`（天朝保护囚禁） |
| fp1/ce1/ep3/mpo 若干 | 各 wars 文件 | UUII 删去图外地理分支（`always = no`） |
| 日本四条 CB | `10_tgp_japan_wars.txt` | 日本 CB 整体禁用（图外） |

---

## 六、原版同步副本（名称索引，未列效果）

下列文件是 1.19/1.20 原版的同步副本，除第五节所列改动外与原版一致。

- `00_civil_war.txt`：independence_faction_war、liberty_faction_war、claimant_faction_war、depose_war、refused_liege_demand_war、independence_war、nation_fracturing_faction_war、nomadic_war（peasant_war/populist_war 已被自制版覆盖）
- `00_conquest.txt`：county/duchy/ducal_conquest_cb、ireland_laudabiliter_conquest_cb
- `00_dejure_war.txt`：de_jure_cb、individual_county_de_jure_cb、individual_duchy_de_jure_cb、imperial_reconquest_cb、dismantle_holy_pretender_cb、dismantle_byz_pretender_cb
- `00_event_war.txt`：norman_conquest_cb、norwegian_invasion_cb、sons_of_lothbrok_invasion_cb、hungarian_migration_cb、azariqa_rebellion_cb、raiktor_claim_cb、raiktor_conquest_cb、fp1_scandi_adventurer_conquest、diarch_vassalisation_cb、remove_regent_cb
- `00_invasion_war.txt`：invasion_war、clan_invasion_war、mongol_invasion_war、mongol_realm_invasion_war、pax_romana_invasion_war
- `00_religious_war.txt`：minor/religious/major_religious_war、excommunication_war、flowery_war_cb、undirected/directed_great_holy_war
- `00_subjugation.txt`：tribal_subjugation_cb；`00_tributarize.txt`：make_tributary_cb、tributary_independence_war；`00_vassalization.txt`：vassalization_cb（已改）
- `01_fp1_wars.txt`：fp1_varangian_adventurer_conquest
- `03_fp2_wars.txt`：fp2_border_raid、fp2_expel_interloper、fp2_mediterranean_conquest_cb
- `05_fp3_wars.txt`：fp3_install_loyalist_cb、fp3_turkic_invasion_cb、fp3_seljuk_invasion_cb、fp3_free_house_member_cb、fp3_unify_house_cb、fp3_zanj_rebellion_war
- `06_ce1_wars.txt`：mythical_ancestor_war、legendary_adventure、leg_demand_fealty_cb
- `07_ep3_wars.txt`：ep3_laamp_adventurer_county/duchy/kingdom/empire_invasion、ep3_laamp_raid_contract_cb、crusading_claim_cb、ep3_hasan_assassin_war、imperial_expedition_cb、ep3_pillaging_foray、ep3_roman_empire_border_war、ep3_laamp_apprehend_adventurer_cb、greek_anarchy_cb、ep3_laamp_peasant_war、admin_barbarian_conquest_cb
- `09_mpo_wars.txt`：migration_cb、mpo_nomad_invasion_cb、mpo_nomad_duchy_invasion_cb、humiliation_cb、retaliation_cb*、domination_cb*、de_jure_cb_nomadic*、sovereignty_cb、mpo_great_war_of_defiance_cb、mpo_gok_onslaught_cb（*被 zz_dm 覆盖）
- `10_tgp_china_wars.txt`：china_seize_county_cb、china_hegemon_seize_county_cb、china_seize_duchy_cb、china_hegemon_seize_duchy_cb、claim_the_mandate_cb（已改）、chinese_consolidation_cb（被覆盖）、chinese_reunification_cb（被覆盖）、silk_road_vassalization_cb（已改）、grand_campaign_kingdom_invasion_cb（已改）
- `10_tgp_faction_wars.txt`（与原版逐字相同）：replace_ceremonial_regent_faction_war、restore_ceremonial_liege_faction_war、ceremonial_claimant_faction_war、imperial_policy_faction_war
- `10_tgp_japan_wars.txt`：japan_imperial_expansion_cb、japan_imperial_reconquest_cb、japan_install_bloc_member_cb、japan_bloc_war_cb（图外，已禁用）

---

## 七、发现的问题 / 值得留意

1. **hd_strategic_annex_cb 是死代码**：`always = no` 且无脚本引用，可删（删前确认老存档里没有进行中的该 CB 战争）。
2. **chinese_reunification_cb 三处同名**：最后加载的退役版生效，`zzzz_hd_unification_wars.txt` 里的区域统一版与相关 `hd_unification_*` 触发器/效果实际不可达。若不打算恢复，可连文件一并清理；若要恢复，需先改掉退役版。
3. **hds_wu_invasion_cb 两份**：`zzzzzz_hds_wars.txt` 里的被 `zzzzzzzz_hds_sun_danyang_war_override.txt` 覆盖，属有意保留。
4. **retaliation_cb / domination_cb / de_jure_cb_nomadic 两份**：`09_mpo_wars.txt` 中的 HD 改动对这三条不生效（被 zz_dm 版覆盖），若要保持「游牧胜后仍为游牧」需把 HD 改动同步进 `zz_dm_obedience_mpo_wars.txt`。
5. **hd_confederation_subjugation_cb 无任何外部引用**，仅靠宣战界面选用；若本意是联盟盟主才能打，目前条件已限定，确认联盟玩法仍在即可。
6. 玩家可手选的自制 CB 一共 14 条：吞并、逐鹿中原、四夷入寇、边境劫掠、边境郡小冲突、开边、讨逆、奉诏讨伐、讨篡、联盟降服、北伐、攘夷两条、大复仇；其余全部为脚本专用。

---
## 2026-10-21 合并说明
- 删除：兼并 `hd_strategic_annex_cb`、边境劫掠 `hd_dc_cha_border_raid_cb`、边境郡冲突 `hd_dc_sta_border_clash_cb`。
- 奉诏讨伐 `hd_court_fengzhao_cb`、讨篡 `hd_court_taocuan_cb` 并入清君侧 `hd_dc_ten_qingjunce_cb`（战争变量 `hd_dc_qjc_mode`）。
- 8 个历史 CB（`hd_historical_war_cb`、`hd_cao_expansion_cb`、`hd_yuan_expansion_cb`、`hd_yuan_jizhou_cb`、`hd4_guandu_cb`、`hd4_tao_xuzhou_cb`、`hds_regional_cb`、`hds_wu_invasion_cb`）并入吞并 `hd_dc_tunbing_cb`：
  攻方临时变量 `hd_tb_kind`（`hd_tb_arm_effect`，3 天过期）选情境，`on_declaration` 写到战争变量；判别触发器见 `scripted_triggers/hd_tb_triggers.txt`。
  官渡目标生成文件 `zzzzzz_hd4_guandu_targets_generated.txt` 的生成器 build_patch.py 不在仓库，本次直接改了文本（`casus_belli`/`cb` 名与 arm）。
