# pX-B 最终报告（修正后合并版）

## 本轮审查意见处理结果

审查没有 blocker 或 major，共 4 条 minor，处理如下。

**1. P2 第②步 else_if 第二支与 R7「行为不变」字面不一致**
- 现做法保留，代码逻辑没改，只在暂存副本加了一条注释。
- 保留理由：任务原文明确要求「郡头衔先转给刘裕再收编郡内更低层级者」；审查也确认写法合法，下游不依赖这三名郡守继续持郡。
- 新增注释位于 zz_hd_j16_e5_395_effects.txt 该 else_if 上方，内容说明：本支夺的是 AI 郡守的郡（404 开局的毗陵、吴兴、会稽）；如果选严格 R7，删掉整支即可，后面那支 WARN 和第③步层级护栏照常生效。
- 选哪种由汇总人决定，见「需要汇总人处理」第 1 条。

**2. syj 两卡文案写死「朔州」**
不在本路文件范围，没改，交汇总人（第 4 条）。

**3. 346d_flavor 第 16 行注释指错文件**
不在本路文件范围，没改，交汇总人（第 2 条）。

**4. 冻结的 nbc 覆舟山效果有同样的层级问题**
冻结文件，没改，交汇总人（第 3 条）。

**复核**
- 闸门已复跑，结果：error 0，warn 0，相对基线新增 0，resolved_vs_baseline 8。
- 修改后 e5_395 暂存文件仍为 UTF-8 带 BOM、LF，花括号平衡（1640/1640）。
- 6 个 edit 文件的 base_sha256 与 mod 现文件再次逐个比对，全部一致，登记后没有人改过。

**仍未解决（都不在本路范围）**
- R7 取舍
- syj 文案
- 346d 注释
- nbc 冻结副本的层级问题
- Q2 的 k_pingzhou 部分
- 全局变量登记
- 02 §2.0 文档回填

---

## 暂存任务名与文件清单

暂存任务名：pX-B。暂存区路径为 D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\pX-B\files\…

**改现有文件（edit）**
- common/scripted_effects/zz_hd_asp_effects.txt：R2；Q2③ 的什翼犍卡他局补发。
- common/scripted_triggers/zz_hd_asp3_triggers.txt：Q2③，新增触发器，两张 syj 主目标改为调用它。
- common/scripted_effects/zz_hd_j16_e5_395_effects.txt：P2，本轮另加审查注释一行。
- common/scripted_effects/zz_hd_j16_304b_effects.txt：Q2①。
- common/scripted_effects/zz_hd_j16_e4_370_effects.txt：Q2②。
- localization/english/custom_localization/zz_tr_WJ_names_l_english.yml：C1。

**新建（new）**
- localization/english/zz_tr_hd_370_l_english.yml：C1、C2。

**编码与核对**
- 现有文件都保持 UTF-8 带 BOM、LF，没有 CRLF。
- 新建 yml 为 UTF-8 带 BOM、LF，首行 `l_english:`，键统一写 `:0`。
- 冻结文件没改。没跑生成器，没开游戏，没提交。
- 6 个 edit 文件的 base_sha256 与 mod 现文件一致（本轮复核过）。
- 闸门（--only-changed，对照 baseline.json）：error 0，warn 0，新增 0，resolved_vs_baseline 8。报告在 D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\pX-B_gate.txt
- 改动的 5 个脚本文件花括号都平衡。

## 逐条做法与证据

### R2（asp 卡他局补发，hd_asp2_mid_issue_effect）
旧条件用 `git show HEAD:common/scripted_effects/zz_hd_asp_effects.txt` 取，在 HEAD 第 2027–2054 行。两张卡都改成：

`OR = { AND = { NOT = { has_global_variable = hd_j16_pulse_started } <旧条件> } AND = { has_global_variable = hd_j16_pulse_started <现条件> } }`

- **苻坚卡**
  - 旧条件：`hd_asp_sun_threshold_trigger = yes`
  - j16 支：`hd_nbc_fujian_coup_done`，加 `hd_asp3_changan_lord_trigger`
- **刘裕卡**
  - 旧条件：`hd_asp2_serves_dyn_trigger = { DYN = sima }`，加 `hd_asp_sun_threshold_trigger`
  - j16 支：`OR { hd_j16_jingkou_started  hd_j16_liuyu_regent_result }`

两个旧触发器都还在（zz_hd_asp_triggers.txt:396、:2670）。关了史实规则的 j16 开局不跑心跳，走旧条件支，符合 06 §0.1 第 3 条。

### C1 / C2（英文缺键）
- **比对方法**：脚本 D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\pxb\keycmp.py 拿 zz_hd_370_l_simp_chinese.yml 的 76 个键对照 mod 内全部英文 yml。补之前缺 36 个，补之后缺 0，没有重复定义。
- **年号 8 键**，按 heping 的写法插进 zz_tr_WJ_names_l_english.yml：
  - `SG_nianhao_jianxi` / `_tt`：Jianxi
  - `SG_nianhao_shengping` / `_tt`：Shengping
  - `SG_nianhao_jianguo` / `_tt`：Jianguo
  - `SG_nianhao_xianan` / `_tt`：Xian'an
- **新文件 28 键**：
  - 部队名 5 个：hd_370_wangmeng、murongzang、murongping、jin、huanwen 的 `_army_name`
  - 书签 23 个：`bm_hd_370`、`bm_hd_370_desc`，加 7 人各自的名、subheading、desc
- **译名**：沿用 mod 现有英文惯例，例如 Prince of Le'an、Duke of Haixi。

### P2（e5_395 的 hd_j16_fuzhoushan_duchy_effect，只改 j16 副本）
每郡的处理顺序：
1. 桓玄、桓谦直辖的县转给刘裕（原样）。
2. 郡头衔先转给刘裕：
   - 持有者是桓玄或桓谦：照原样 usurped 转。
   - 持有者属于桓玄一系、是 AI、最高头衔恰为郡级：用 usurped 夺郡，不加宣称，记 `FIRE duchy_taken_<郡>`。本轮在这一支加了审查注释。
   - 其他情况（含玩家持有、最高头衔高于郡级）：不动，记 `WARN duchy_kept_<郡>`。
3. 郡内其余持有者，逐人比较层级：低于刘裕的才 swear_fealty，否则记 `WARN fealty_tier_<郡>`。这种 scope 比层级的写法原版有先例（coronation.txt:2317）。

404 开局五郡的走法，已在 zz_hd_404_titles.txt 核实：
- 丹阳、吴：桓玄、桓谦持有，走第②步第一支。
- 毗陵、吴兴、会稽：走第②步第二支。
- 丹阳最先处理，刘裕拿到后即为郡级，后面各郡的改投都能通过层级判断。

### Q2 之 k_suozhou
**① 304b hd_j16_daitong_effect**
- 条件：什翼犍未持 k_suozhou、本人独立、k_suozhou 无人持有。
- 满足时依次执行：
  1. 保存旧主头衔；
  2. `create_title_and_vassal_change { type = created }`，加 `change_title_holder`，加 `resolve_title_and_vassal_change`；
  3. `set_primary_title_to`；
  4. 记 `FIRE suozhou_granted`；
  5. 执行 found_realm。
- found_realm 之后，若旧主头衔已不是主头衔且带 hd_nbc_style，对它执行 `reset_title_name` 并去掉 style。
- 不满足时记 `WAIT suozhou_held` 或 `WAIT suozhou_not_indep`。
- k_suozhou 的法理郡由 zz_hd_nbc_dejure.txt 在 280.1.1 挂好。

**② e4_370 hd_j16_weichen_sides_effect**
- 先取 k_suozhou 持有者。
- 他不存在，或不是独立的拓跋王朝成员时，依次取 d_yunzhong、d_tuoba 持有者的 top_liege，同样要求独立、属拓跋王朝。
- 都取不到时仍用原结果，节点照旧 WAIT。
- 第一次回退记 `FIRE dai_fallback`，用全局变量 `hd_j16_weichen_dai_fb_log` 去重。

**③ 发卡与主目标条件**
- 新触发器 `hd_asp3_syj_dai_title_trigger`：`OR { has_title = title:k_suozhou  has_primary_title = title:d_yunzhong  has_primary_title = title:d_tuoba }`。
- 三处改为调用它：asp_effects 的什翼犍卡补发、`hd_asp_syj_jianguo_main_trigger`、`hd_asp_syj_kangqin_main_trigger`。

## 自拟与偏差
1. E4-T10 在持有者存在但不合格时也走回退，比任务字面宽。
2. P2 夺郡只针对 AI、且最高头衔恰为郡级的持有者，用 usurped、不加宣称；玩家和更高层级者只记 WARN。持有多个郡的人会被第③步拦下并记 WARN。
3. P2 的 fealty_tier WARN 可能对同一人重复记，没去重，只影响日志。
4. Q2① 另做了三件事：显式 `set_primary_title_to`、复原旧主头衔名、授头衔时 `add_claim_on_loss = no`。
5. Q2① 在什翼犍不独立时不授头衔，但仍照原逻辑执行 found_realm。
6. xianan 译作 Xian'an；jianxi、shengping 和书签键一并补了。
7. 新文件名按任务写作 zz_tr_hd_370_l_english.yml。
8. （本轮）P2 第②步第二支保留，只加注释，标明严格 R7 时如何删除。

## 需要汇总人处理（不在本路范围）
1. **P2 与 R7 的取舍。**
   - 推荐：接受现做法，五郡都归刘裕，三名郡守降为县级后改投。
   - 严格 R7：删掉 e5_395 暂存中带「pX-B 审查注」那一支 else_if。
2. zz_hd_j16_346d_flavor_effects.txt 约第 16 行注释要改为：「中文 zz_hd_370_l_simp_chinese.yml；英文 custom_localization/zz_tr_WJ_names_l_english.yml」。
3. 冻结文件 zz_hd_nbc_history_effects.txt 的 hd_nbc_fuzhoushan_duchy_effect（约 :555–598）有同样的层级问题。建议在 impl_notes 记为已知隐患，或注明它已被 j16 副本取代。
4. syj 两卡文案（zz_hd_asp3_l_simp_chinese.yml:520、524、541、544 及对应英文）需同步为「持有朔州，或以云中、拓跋郡为主头衔」。
5. Q2 的 k_pingzhou 部分（E3-M10、res_yan 用 d_changli 兜底）本轮没做。
6. 新增全局变量 `hd_j16_weichen_dai_fb_log`，需按 08 约定登记。
7. 设计文档 02 §2.0「称号节点不造头衔」需要回填 E2-T10 授 k_suozhou 这个例外。

## 实测项
- **304 开局，玩到 338.6.16 之后**
  - 搜 `HD_J16 e2_t10 FIRE suozhou_granted`，或 `WAIT suozhou_held`、`WAIT suozhou_not_indep`。
  - 看 k_suozhou 是否由什翼犍持有、显示为「代」、称王；原来叫「代」的郡是否恢复原名；英文界面年号是否显示 Jianguo。
- **304 或 346 开局，玩到 370 年之后**
  - 看什翼犍卡能否补发。
  - 374 年后搜 `HD_J16 e4_t10`，应出现 `FIRE gate_opened`，必要时先出现 `FIRE dai_fallback`。
  - 看导演 S7「代」是否不再一直挂起。
- **404 开局，京口之战约 5 天后的覆舟山**
  - 搜 `HD_J16 e5_j51 FIRE duchy_taken_d_piling`、`_d_wuxing`、`_d_kuaiji`、`WARN duchy_kept_`、`WARN fealty_tier_`、`FIRE fuzhoushan`。
  - 看五郡是否都归刘裕、三名郡守是否成了刘裕的县级封臣、error.log 里有没有 change_liege 报错。
- **190 等非 j16 开局**
  - 看苻坚、刘裕两卡在持郡后能否照旧补发。
- **英文界面**
  - 看 370 书签页的文字和人物是否有英文。
  - 看 370 线三组迁入节点出兵时，部队名是否显示英文。