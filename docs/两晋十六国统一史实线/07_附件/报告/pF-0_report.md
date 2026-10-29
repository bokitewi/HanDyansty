# pF-0 最终报告（修正后合并版）

一共 6 条审查意见，都已处理。major 那条已在暂存区修好。5 条 minor 里改了 1 处文案（第 5 条），其余 4 条写进本报告。本轮只改了暂存区的 2 个文件，暂存区仍是 21 个文件，没有新增 stage。

复跑闸门的结果和修正前一样：相对基线新增 error 1、warn 2，另有 14 条相对基线已消失。这几条都能解释，见后文第六节。

## 零、审查意见逐条处理

1. **major（司徒节点大概率永不触发）：已修。** 改在 common/scripted_effects/zz_hd_j16_e1_304_effects.txt。
   - **空缺条件放宽。** 原条件是「司徒无人持有，或由天子代持」，现改为下面两条同时成立：
     - 现任不是温羡：`NOT = { title:e_minister_chancellor.holder ?= scope:hd_j16_st_wen }`；
     - 且以下三种之一：无人持有；天子代持；由 AI 他人持有（`holder ?= { OR = { this = scope:hd_j16_st_emp  is_ai = yes } }`）。
     - 现任是玩家（且不是天子）时不夺他的官，节点继续等，窗口过后跳过。这一层是我自拟的保护，审查意见没有提。
     - 是否替换现任由 got_minister_position_effect 的 appointment 处理。
   - **补显示名。** 执行体在 got_minister_position_effect 之后补了一行 `title:e_minister_chancellor = { set_title_name = hd_han_situ_title }`，写法与 3-C 开局相同。这样即使头衔曾被销毁再新建，「司徒府」显示名也不会丢。
   - 节点头部注释同步改了，写明了新条件，以及「王戎不在卒年表时只能靠自然死亡」。
   - **卒年表不在我的文件范围内，没有改。** 仍需汇总人补一行（见第四节第 4 条）。不补的话，王戎（生于 234 年）只能在 307.1.1 之前自然死亡，节点才会触发。本项已列为必测。
2. **minor（越卡回退方法）：只写进报告。** 回退三步见第三节第 3 条。
3. **minor（吐谷浑连带影响漏列）：只写进报告。** 已核实，补进第四节第 6 条：
   - zz_hd_asp3_triggers.txt 第 713 行 hd_asp_syj_jianguo_b3_trigger、第 746 行 hd_asp_syj_nankui_b2_trigger 判定配偶属 dynasty:murong（第 716、749 行）；
   - 另外补一处：第 580–582 行 hd_asp_mrc_yanyuan_main_trigger 判定君主本人属 dynasty:murong，现在吐谷浑王也能满足。
4. **minor（敦煌两郡 liege 改挂）：保留，等汇总人确认。** 回退方法写在第三节第 1 条。
5. **minor（英文口吻）：已修。** zz_hd_english_completion_nbc_l_english.yml 第 160 行 hd_nbc.0150.desc_yishui 改为第二人称：urge you / You look at / await your order: will you cross the Yi?。这样与原英文 desc 一致。中文仍是第一人称，与中文原 desc 的口吻相同。BOM 和 LF 都保留了。
6. **minor（hbirth 模板、gen370）：只写进报告，需要汇总人执行。** 见第四节第 1、2 条。附带说明：新键 Maozhi_8302_4E4B 原本已被 s2、OE 人物和 hbirth 模板 fanyang_zu_025b 引用，但一直没有定义，本次一并补上了。

---

# pF-0「收尾数据批」报告（合并修正后）

7 项都已在暂存区完成，共改 21 个文件，没有一项因已做过而跳过。

- 没有直接写 mod，没有跑生成器，没有开游戏，没有提交。
- 所有文件都是在动笔前一刻才 stage edit 的。复核时 21 个文件的 base_sha256 与 mod 现有文件全部一致，期间没有并发改动。
- 保留了原有的 BOM 和换行：nbc 中文 yml 原本是 CRLF，照旧 CRLF；其余都是 LF。

## 一、暂存任务名与文件清单
暂存任务 pF-0，暂存区在 D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\pF-0\files\ 下。

| 项 | 文件 |
|---|---|
| 1 | history/titles/zz_hd_370_titles.txt、zz_hd_370_undo.txt |
| 2 | history/titles/zz_hd_404_titles.txt；common/scripted_effects/zz_hd_nbc_startup_effects.txt（只改 404 分支一处） |
| 3 | common/dynasty_houses/zz_hd_oe_houses.txt |
| 4 | history/characters/00_sili.txt、00_xuzhou.txt、01_dishishixing.txt、01_neirenzhubu.txt、01_xunchenbaxing.txt；localization/{simp_chinese,english}/names/zz_hd_j16_names_l_*.yml |
| 5 | zz_hd_asp_effects.txt、zz_hd_asp_triggers.txt、zz_hd_asp_custom_loc.txt、zz_hd_asp3_l_simp_chinese.yml、zz_tr_hd_asp3_l_english.yml |
| 6 | common/scripted_effects/zz_hd_j16_e1_304_effects.txt |
| 7 | events/zz_hd_nbc_events.txt、zz_hd_nbc_l_simp_chinese.yml、zz_hd_english_completion_nbc_l_english.yml |

## 二、逐项做法与证据

**1. 百济换近肖古王**
- 改前 grep：370 titles 第 82 行是 d_baiji，第 524–526 行是三县（c_uuii_p_3353、3887、3904），持有人都是 hd_nbc346_chief_baiji。undo 第 75 行、第 515–517 行同。
- 改法：这 8 行的持有人改为 korean_buyeo_49。只动 chief_baiji 本人的行，lelang、mahan 两支没动。
- undo 的含义是「恢复成 346 的值」，而 346 已由 4-B 换成他，所以 undo 也应改。
- 他生于 300、卒于 375.11.1，370.2.14 开局时在世。他的 name 已由汇总人补过（oe 第 79677 行）。
- 改前 grep 过 common 和 events：没有脚本引用 hd_nbc346_chief_baiji。
- 404 核查：404 titles 第 200 行、第 486–488 行持有人是 hd_nbc404_chief_baiji。近肖古王 375 年已死，按要求不换。

**2. 敦煌主头衔（A4-G1）**
- 404 titles：
  - d_dunhuang_hexi 那一行调到 d_dunhuang（冥泽）之前，现在是第 192 行；
  - 两郡都仍由李暠 longxi_li_005 持有，liege = 0；
  - 冥泽四县仍由 hd_nbc404_gov_dunhuang 持有，挂在 d_dunhuang 下。
- zz_hd_nbc_startup_effects.txt 第 323 行，404 分支：
  - 主头衔从 d_dunhuang 改为 d_dunhuang_hexi；
  - 新加一行 `title:d_dunhuang = { reset_title_name = yes }`，写法照原版 title_events.txt；
  - 设主头衔仍排在 realm_name 之前，所以西凉国号和「凉公」称谓都会落到真敦煌上。
- 该效果只在 346 和 404 开局调用，else 分支就是 404。
- 已核：hd_j16_346d_realm_names_404_effect 只给仇池改名，不碰冥泽。
- 346 和 370 没有同类问题：
  - 两局的冥泽、真敦煌分别由两位郡守持有；
  - realm display 里只有 404 分支提到敦煌；
  - 370 冥泽的持有人 hd_nbc404_gov_dunhuang 生于 350，开局时在世。
- WJ 爵号后缀两郡都有，且 top_liege = no，不影响李暠。

**3. 吐谷浑家族**
- 定义在 zz_hd_oe_houses.txt 第 567 行，`dynasty = 105818` 改为 `dynasty = murong`。
- 纹章：没有家族专属纹章。105818 的固定纹章在 zz_hd_dynasty_fixed_coas.txt，murong 的在 zz_hd_nbc_family_coas.txt，改后自动跟随 murong。
- 本地化：家族名键 dynn_Thogon（吐谷浑）不变。
- 文化：族人的文化是 tuyuhun，不会被 hd_nbc_assign_culture_effect 改成 hd_murong。脚本里没有残留的 105818 引用，只有一处过时注释。
- 受影响的是 zz_hd_oe_characters.txt 里 56 行 `dynasty_house = house_tuyuhun`，共 55 人：
  - 吐延 247347、叶延 247348、碎奚 247349、视连 247350、视罴 247351、乌纥提 247352、树洛干 247353、阿柴 247355、慕璝 247357、慕利延 247358 等；
  - 一直到 247399、1415015、1415990–1415997、1416398。
- p3-B2 的「亲子不看王朝」放宽可以保留。

**4. 中文 name 字面量**
- 全 history/characters 共有 1026 条中文 name。先按生卒窗口筛出 240 条：生于 421 年及以前、卒于 290 年及以后。
- 再按引用判定：ID 出现在以下任一处的才算本线人物，结果 13 人，已全部改键。
  - zz_hd_j16_*、nbc、304、370、asp、hi 的脚本和事件；
  - 卒年表 tsv；
  - 304、346、370、404 的头衔文件，370 和 304 的 undo；
  - early_spawn.tsv。
- 01_shiliuguozhu、nbc、304、j16 这几个本线专属的人物文件里，中文 name 已是零，说明 2-B 已经清理过。
- 13 人的改法（只新增 1 个键，其余复用库中同值键）：
  - 禄官 tuoba_luguan → bfyznan159
  - 准 hongnong_yang_011 → uuii_book_yang_zhun_name
  - 亮 hongnong_yang_016 → uuii_book_yang_liang_name
  - 佺期 hongnong_yang_017 → uuii_book_yang_quan_qi_name
  - 宪 hedong_pei_029 → hdvm_5BAA
  - 导 langya_wang_020 → Dao_5BFC
  - 舒 langya_wang_035 → hdvm_8212
  - 嘏 langya_wang_094 → uuii_book_wang_gu_name
  - 谧 langya_wang_178 → Mi_8C27
  - 茂之 pengcheng_cao_007 → 新键 Maozhi_8302_4E4B，中英都写进 zz_hd_j16_names。库中原本没有这个键的定义，但已被 s2、OE 人物和 hbirth 模板 fanyang_zu_025b 引用，这次一并补上了。
  - 莫圭 yuwen_mogui → bfyznan461
  - 乞得龟 yuwen_qidegui → bfyznan458
  - 讷 henan_helan_032 → Ne_8BB7
- 每行行尾都加了注释，写明原来的中文字面量。13 个键中英齐全；bfyznan 三个键的中文在 replace 目录。

**5. 越卡 b1 改为达成时判定**
- hd_asp_complete_effect 末尾，在 xan_feishui b2 块之后加了一个 if 块（zz_hd_asp_effects.txt 第 1039–1046 行）：当 `var:hd_asp_aspiration ?= flag:smyue_yingjia` 且 `hd_asp_smyue_yingjia_b1_trigger = yes` 时，设 hd_asp_b1。
- 从 hd_asp_bonus1_trigger 的分派链里删掉了 smyue_yingjia 那一段（原第 2258–2261 行）。删后落到链尾 `trigger_else = { always = no }`，与 smteng_qihuo 的现状一致；写法同 p3-D 先例（smteng_beimen b2、xan_feishui b2）。
- custom_loc 第 5046 行的 `_1_todo` 改为 `_1_final`。
- 中英 yml 的 `_1_todo` 改名为 `_1_final`，加上「【主要目标达成时判定】」；`_pre`、`_done` 一并改成「达成之时，苟晞仍……」。
- 已 grep：全 mod 不再有 smyue_yingjia_1_todo 的引用。

**6. 温羡接司徒（E1-J05，已按审查修正）**
- 入口在 E1-B70 之后（第 23 行）加了一行 `hd_j16_node_situ_effect = yes`。文件末尾新增节点和执行体 hd_j16_situ_effect，照 TEMPLATE 写。
- 自保护：开局年 ≥ 346 时只设 done。
- 窗口：305.7.1 起，到 307.1.1 跳过。温羡已死就跳过（actor_dead）。
- 条件（修正后）：
  - 王戎已死（hd_j16_dead_trigger）；
  - 天子在世；
  - 司徒现任不是温羡，并且是以下之一：无人持有、天子代持、AI 他人持有；
  - 温羡在世、无地、未被囚，不是天子本人。
- 玩家处理：
  - 天子是玩家，记 SKIP player_ruler；
  - 温羡是玩家，记 SKIP player_actor；
  - 现任是非天子的玩家，或其他条件未满足，记 WAIT not_ready，只记一次。
- 执行体：
  - 设 hd_j16_situ_result 和 hd_hev_j16_situ；
  - 把天子存为 councillor_liege；
  - 用解析出的 scope，照 hd_nbc_minister_effect 的写法调 got_minister_position_effect，由它的 appointment 替换现任；
  - 之后补设 `title:e_minister_chancellor = { set_title_name = hd_han_situ_title }`。
- 日志写 e1_j05。scope 名 hd_j16_st_wen、hd_j16_st_emp，变量 hd_j16_situ_*，已 grep 全 mod，不重名。

**7. 旧 nbc 事件（没有新增事件号）**
- **a. hd_nbc.0145 选项 a**：在设 hd_hev_346_fujian_coup 之后加了两段。
  - 撤销苻法之死节点的跳过：若已有 hd_j16_fufa_skip、没有 _result，就删去 _skip 和 _done，下一跳由该节点补做。
  - 玩家苻坚的暂扣：苻坚 is_ai = no、苻法在世、hd_j16_fufa_done 和卒年 done 都未设时，设 hd_nbc_death_lueyang_fu_019_done 和 hd_j16_fufa_hold。之后由 1210 的 a 撤销、b 维持。
- **b. hd_nbc.0150**：desc 改成 first_valid 分支。读到 hd_j16_beifa_yishui 时显示 hd_nbc.0150.desc_yishui，文案是战前语气（姚襄据洛阳、兵临伊水）。
  - 中文写进 zz_hd_nbc_l_simp_chinese.yml 第 168 行，第一人称，沿用该文件 `键: "…"` 的写法；
  - 英文写进 zz_hd_english_completion_nbc_l_english.yml 第 160 行，按审查意见改为第二人称，与原英文 desc 一致。
- **c. hd_nbc.0110**：李势 bacong_li_026、周抚 lujiang_zhou_004 两处原本写死。改为先清 scope，再用 hd_j16_resolve_effect 解析成 hd_j16_j91_lishi、hd_j16_j91_zhoufu，全部用 ?= 取用。两人都有 hbirth 指针。
  - 取不到周抚时，照旧把益州交天子；
  - 取不到李势时，成汉之主那一段和 news_b 都跳过。

**新增或改名的键与变量**
- 新增键：hd_nbc.0150.desc_yishui（中英）、Maozhi_8302_4E4B（中英）、hd_asp_pb_smyue_yingjia_1_final（中英，取代 _1_todo）。
- 新增变量：hd_j16_situ_done、_result、_skip、_wlog，以及 hd_hev_j16_situ。

## 三、自拟与偏差
1. **敦煌**
   - 404 头衔里真敦煌那一行调到冥泽之前，让历史加载时就倾向以真敦煌为主头衔。
   - 敦煌宋氏 c_nf_dunhuang_song、晋昌唐氏 c_nf_jinchang_tang 的 liege 从 d_dunhuang 改挂 d_dunhuang_hexi。这一条偏离了「照现状」，但持有人仍是李暠，写法合法，需要汇总人确认。不保留的话，把这两行改回 `liege = d_dunhuang` 即可，主头衔仍由开局效果设定。
   - reset_title_name 是防御性的一行，新开局里冥泽本不会被改名。
2. **名字键**
   - 任务原文写「新键写进 j16_names」，实际 13 个里有 12 个复用了库中同值键，依据是该文件文首「同值键直接复用」的约定。
   - OE 那套键（Luguan_name、Qidegui_srb_name）英文带声调，没有用，同 2-B 处理长民的先例。
   - 「本线人物」按上面的引用标准判定。其余 227 条没有改，主要在 00_xuzhou 113 条、01_xunchenbaxing 56 条、00_sili 35 条，其中 25 条是「氏」「某」这类占位名。这些与设计文档、卒年表都没有交集。完整清单在 D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\f0\remaining.tsv。
3. **越卡**
   - `_pre`、`_done` 的措辞一并改成「达成之时，……仍……」，照 smying_taidi b2、smyue_sheji b1 的写法。这对应 D56 待拍板清单第 14 项（「开局已有也在达成时给赏」），需要 boki 确认。
   - 如果 boki 否决，回退三步：
     - ① 在 zz_hd_asp_triggers.txt 的 hd_asp_bonus1_trigger 分派链恢复 smyue_yingjia 那 4 行（原第 2258–2261 行，可从 mod 原文件取回）；
     - ② 删除 zz_hd_asp_effects.txt 中 hd_asp_complete_effect 里新加的 smyue_yingjia if 块（第 1039–1046 行）；
     - ③ custom_loc 与中英 yml 的 `_1_final` 改回 `_1_todo`，去掉「【主要目标达成时判定】」，`_pre` 和 `_done` 恢复原文案。
4. **司徒**
   - 本任务不能新增事件，所以天子或温羡是玩家时都直接 SKIP。
   - 按审查意见放宽了任务原文的「无人或空缺」：现任不是温羡，且为无人持有、天子代持或 AI 他人持有时就授官。
   - 现任是非天子的玩家时不夺他的官，这一点是自拟。
   - 执行体补设了「司徒府」显示名。
   - 304 的 yml 在允许范围内，但没有用到，没有新文案。
5. **0145 a 跨节点改状态**
   - 撤销苻法之死节点的 skip 和 done，修的是 4-B 的同跳顺序缺陷：入口第 32、33 行，Q20 发出 0145 后，Q20b 在同一跳里就以 coup_not_fired 跳过。
   - 这个缺陷每次都会出现，不只在玩家晚点选项时。原先玩家苻坚永远收不到 1210，AI 苻坚的苟氏入宫也会丢。
   - 撤销对 AI 和玩家都做，暂扣只对玩家做。
6. **0110**：李势已死时 news_b 不再存。旧写法会存一个死人。
7. **0150 英文口吻**：中文第一人称，英文第二人称，分别与各自语言的原 desc 一致。

## 四、需要汇总人处理的事项
1. **重跑 hbirth 和 popclean**
   - 第 4 项改了 5 个人物文件的 name。
   - hbirth 模板 zz_hd_hbirth_templates.txt 里还是中文字面量：禄官第 79757 行、导 90567、乞得龟 101339、茂之 103619 与 105041、佺期 111365、嘏 117868、谧 117879。不重跑的话，hbirth 出场的这些人仍会报 Missing loc。
   - 第 3 项家族改挂王朝之后，也建议一起重跑核对。
2. **生成器会冲掉改动**：zz_hd_370_undo.txt 文件头写着由 gen370.py 生成。如果重跑 gen370，本次百济的 4 行会被冲掉。要重跑的话，先把百济换人写进生成器数据。
3. **370 undo 与 346 不一致**：两者之间还有 63 处值不同，多为 346 后来改的郡县政体和 liege。其中包括 impl_notes 第 4 期第二轮所列 4-B 的约 23 个键（斥丘、齐国郡及 3 县、淮南、历阳、交趾、九真、江州、彭泽郡及 5 县、c_nf_chenjun_xie 等）。这些不在本任务范围内，没有处理。
4. **王戎卒年（司徒节点能否触发取决于此）**
   - 卒年表里按「王戎」和 wang_rong_2 都查不到。history 里 305.7.11 的死亡在 304 局不会执行。
   - 请补一行：N，wang_rong_2，DATE 305.7.11，DATE10 315.7.11，然后重跑 gen_deaths_effects。
   - 不补的话，E1-J05 只在王戎 307.1.1 前自然死亡时才可能触发。
5. **0110 的调用点**
   - 冻结文件 zz_hd_nbc_history_effects.txt 第 262 行（hd_nbc_check_fashu_effect，E2-J91 调用）写死了 `character:longkang_huan_017`。
   - 桓温生于 312：346 局取得到；304 局他是 hbirth 出场，取不到，0110 发不出。
   - 本项改的是事件体，修这个调用点要另行指派。
6. **吐谷浑并入 murong 的副作用和残留**
   - house_changli_doulu（豆卢）也挂在 105818 下，是否一起改挂请定。
   - zz_hd_j16_304b_effects.txt 第 11 行关于 105818 的注释已经过时。
   - zz_hd_j16_dir_triggers.txt 第 76 行：370 年燕灭以前，导演层不会把吐谷浑当作目标。
   - zz_hd_asp3_triggers.txt 有四处 dynasty:murong 判定，现在吐谷浑也能满足，请定是否加 `NOT = { house ?= house:house_tuyuhun }`：
     - 第 181 行「慕容王国级君主」：吐谷浑王也能满足；
     - 第 580–582 行 hd_asp_mrc_yanyuan_main_trigger：吐谷浑君主占冀州也能满足（审查后补列）；
     - 第 713/716 行 hd_asp_syj_jianguo_b3_trigger、第 746/749 行 hd_asp_syj_nankui_b2_trigger：以「配偶属 dynasty:murong」判定，娶吐谷浑王族女子也能达成（审查补列）。
   - 吐谷浑现在是部落政体，不会触发天朝命名；如果改成天朝政体，会沿用 346 给 murong 设的固定国号「燕」。
7. **面板行**：hd_hev_j16_situ（温羡接司徒）交 F-1。F-1 在并行跑，可能需要补做。
8. **敦煌两郡 liege 改挂**（第三节第 1 条）请确认是否保留。
9. **越卡 b1 改为达成时判定**要等 D56 第 14 项由 boki 拍板，回退步骤见第三节第 3 条。

## 五、实测项
- **404 开局**：李暠主头衔是真敦煌，显示「西凉」和公爵称谓；冥泽显示原名；敦煌宋氏、晋昌唐氏是李暠的封臣。
- **370 开局**：百济之主是近肖古王，375.11 以后正常继承。
- **346 局玩家苻坚**：
  - 选 0145 a 后，日志依次出现 `e3_q20b WAIT reopened_by_0145a` 和 `fufa_death_held_for_player`；
  - 下一跳出现 `e3_q20b FIRE fufa`；
  - 60 天后弹出 1210；选 a 之后，苻法按卒年表死去。
- **346 局玩家桓温**：洛阳在姚襄手里时，0150 显示伊水文案；中英文都检查（英文是第二人称）。
- **304 局（必测）**：日志搜 `HD_J16 e1_j05`。
  - 王戎死后，司徒不论是空缺、天子代持还是由他的继承人或 AI 任命者持有，都应出现 FIRE situ_wenxian；
  - 之后温羡任司徒，显示名仍是「司徒府」；
  - 如果一直是 WAIT 直到 window_closed，先查王戎是否死了（卒年表是否已补）。
- **越卡**：开局时第 1 项显示「主要目标达成时判定」；达成时苟晞在麾下，就给 b1 的赏。
- **吐谷浑王族**：显示为慕容王朝下的吐谷浑家族，纹章正常。
- **error.log**：上述 13 人不再报 Missing loc（hbirth 出场者要等重跑之后）。

## 六、闸门结果（审查修正后复跑）
复跑命令：`python -I gate.py --overlay pF-0 --compare baseline.json --only-changed --out ...\stage\pF-0_gate`。读到 21 个 overlay 文件；相对基线新增 error 1、warn 2，另有 14 条相对基线已消失。结果与修正前相同。
- **error（误报）**：events/zz_hd_nbc_events.txt:390 报 hd_j16_fufa_skip「只读不写」。它实际由 hd_j16_304_skip_effect 以 `hd_j16_$KEY$_skip`（KEY = fufa）设置，闸门跳过了带参数的变量名，所以认不出。
- **warn（正常）**：
  - zz_hd_j16_e1_304_effects.txt:3440 的 hd_j16_situ_result 是 fire 结果变量；
  - :3441 的 hd_hev_j16_situ 留给 F-1 的面板行。
- 本轮改动的两个文件都保留了 UTF-8 BOM 和 LF，没有 CR。

报告文件：D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\pF-0_gate.txt