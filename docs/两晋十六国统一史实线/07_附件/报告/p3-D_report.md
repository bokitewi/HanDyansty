# p3-D 最终报告（修正后合并版，已落盘 10-27）

# p3-D「全线志向卡」审查修正报告

审查共 10 条（major 4、minor 6），全部已修，只动了暂存区。没有跑生成器，没有开游戏，没有提交 git。闸门复跑结果与修正前相同，仍是 27 条 `gvar_read_never_set`，全部可以解释。另外顺手补了一处审查没点名的同类问题（见第一节第 11 条）。

## 一、逐条处理结果

1. **【major】张轨「西州之王」主目标：已修**
   - 改为：主头衔带有 `hd_nbc_style` 变量，且值为 wang、tianwang 或 huangdi 之一；或满足 `hd_asp_is_emperor_trigger`。再加独立、不朝贡两条。
   - 「公」不算称王。346 开局给张重华设的就是 gong。
   - 已核实 304 开局不会给 `k_uuii_liangzhou` 预设称谓：`zz_hd_304_startup_effects.txt` 第 161–166 行只给刘渊、李雄、颙、颖、越、腾设了称谓。
   - 中英卡面 `_desc` 与 `pm` 改为「称王（或称天王、称帝），独立且不再向任何人朝贡」。

2. **【major】什翼犍「京城在盛乐」用错县：已修**
   - 判定由 `c_uuii_p_1407`（九原）改为 `c_uuii_p_1324`（沙陵县，成乐/盛乐男爵领 `b_uuii_p_1336` 在其中）。
   - 已核实 370 开局 `hd_370_capital_effect` 把他的京城设在 `c_uuii_p_1333`（云中），所以这一项不会被记作「开局已有」，不用改成达成时判定。
   - 中英卡面改为「你的京城在盛乐（沙陵县）」，`_desc` 与 b1 的 pre、done、todo 都改了。

3. **【major】桓温「雪枋头之耻」：已修**
   - 判定改用 `c_uuii_p_738`（许昌）。
   - 中英卡面去掉「（颍川郡治）」，改为「洛阳与许昌都在晋天子领内」。
   - 这是对 04 §5.5 的偏差：原文写「许昌（d_yinchuan 首府）」，但首府 `c_uuii_p_1611` 实为阳翟。卡名与史实都指许昌，所以按字面取许昌。

4. **【major】两项发卡当天已成立、永不发奖：已修**
   - 谢安 xan_feishui b2（370 开局已授吏部）、司马腾 smteng_beimen b2（304 开局持并州 8 郡），都照其余 11 项的写法改为主目标达成时判定：
     - `hd_asp_complete_effect` 开头各加一个 if 块，设 `hd_asp_b2`；
     - 从 `zz_hd_asp_triggers.txt` 的 bonus2 分派中删去这两段；
     - custom_loc 的 `_2_todo` 改引 `_2_final`；
     - 中英 yml 中 `_2_todo` 键就地换名为 `_2_final`，文字前加「【主要目标达成时判定】」，行号不变；
     - 卡面与 pre、done 文字加「达成之时，」。
   - 已 grep 确认：暂存区和 mod 的 common、gui 下都没有对旧 `_2_todo` 键的残留引用。

5. **【minor】smyong_xidu b3：已修**
   - 四州一律改为 `has_title`：k_yongzhou、k_qinzhou、k_hezhou、k_uuii_sili。
   - 中英卡面改回「达成之时，你仍持雍、秦、河、司隶四州」。
   - 原报告说「河州、司隶的州级头衔在 304 开局无人持有」，这一说法不实：`zz_hd_304_titles.txt` 第 15、21 行这两州都由 si_ma_yong 持有。那条偏差已删去。

6. **【minor】9 项自改的达成时判定：保留，交 boki 拍板**
   - 本轮新增的 2 项一并列入，见第四节第 1 条，不阻断。

7. **【minor】hw_shoushan b1：已修**
   - 口径取「龙亢桓氏全族合计」，判定写成两种情况取其一：一人持 ≥2 个王国级头衔，或至少两名在世族人各持 ≥1 个。两者合起来与「合计 ≥2」等价。
   - 中英卡面改为「龙亢桓氏在世族人合计持有两个以上王国级头衔」。

8. **【minor】绰号缺 `_desc`：已修**
   - 中英两份都在 `nick_hd_asp_zhaolie_yiyin` 下一行补了 `nick_hd_asp_zhaolie_yiyin_desc`，同一行号。

9. **【minor】两处直接读 `character:`：已修**
   - 新增两个带 `$ID$` 参数、三路读取的触发器：`hd_asp3_tributary_of_root_trigger`、`hd_asp3_not_regent_trigger`。三路依次是 `global_var:wj_hchar_`、`global_var:hd_hb_p_`、`character:`。
   - smying_hebei b1（王浚）与 smyue_yingjia b2（司马颙）改用这两个触发器。

10. **【minor】mrc_fengying b2「龙城」：已修文字**
    - 库里没有龙城或柳城对应的昌黎县。库中的 Liucheng 是男爵领 `b_uuii_p_5247`，在广西融水县 `c_uuii_p_5740` 下，与此无关。
    - 判定不动（`c_uuii_p_3479`），中英卡面改为「昌黎郡治（扶黎）在慕容暐领内」。

11. **补查到的同类问题：已修**
    - asp3 中的 syj_kangqin b1（苻洛）与 hw_fangtou b1（慕容垂）调用了旧的 `hd_asp2_dead_or_my_prisoner_trigger`。它的「被你所俘」一支只读 `character:`，在出场指针生成的局里会漏判。
    - 新增三路读取的 `hd_asp3_dead_or_my_prisoner_trigger`，这两处改用它。旧的 asp2 触发器被旧卡共用，没有改。
    - asp3 里其余对人物的判定，现在都经由三路读取的 hd_asp3_* 或 `hd_asp2_alive/dead/is_char` 触发器。

**自检**
- 4 个改动过的 txt 括号配平：asp3 triggers 369/369，asp triggers 1318/1318，effects 1725/1725，custom_loc 2864/2864。
- asp3 中英 yml 键序逐行一致，按行切分各 724 行（wc 计 723）。asp 中英 yml 本轮未动，仍是 1409/1409。
- 全部保持 UTF-8 带 BOM、LF。

**修改工具与备份**
- 修改脚本：`scratchpad\p3d_fix\fix.py`、`fix2.py`，文案数据在 `locdata.py`。
- 修正前的暂存副本备份在 `D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\p3d_fix\backup_files\`。
- **注意**：`scratchpad\p3d\` 下的 `data_p3d.py`、`gen_p3d.py` 已与暂存物不同步，不能拿来重新生成，否则本轮修正全部丢失。

## 二、仍未解决项
- 9+2 项达成时判定待 boki 拍板（第四节第 1 条）。
- 3-B、4-C、5-A、6-A 的节点变量待各节点实施后核对（第六节）。
- mid_issue 在岁首脉冲中 root 可能为空：既有问题，未修（第四节第 5 条）。

## 三、闸门
- 命令：`gate.py --overlay p3-D --compare baseline.json --only-changed`
- 输出：`D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p3-D_gate_fix.txt`
- 结果：error 27，warn 0，全部是 `gvar_read_never_set`。原报告写的「13 条 issued + 14 条节点变量」分类有误，更正为 12 + 15：
  - **12 条 `hd_asp_issued_<卡>`**（sima_teng、sima_yong、sima_ying、sima_yue、wang_jun、li_xiong、zhang_gui、shi_le、liu_xuan、murong_chui、xie_an、shiyijian）：误报。实际由 `hd_asp_pend_effect` 的 `set_global_variable = hd_asp_issued_$CARD$` 设置。
  - **15 条节点变量**：
    - yingjia_started、yingjia_done、yingjia_won、yingjia_lost、gongshi_result、zhanggui_qinwang：p3-A 暂存已设，p3-A 落盘后应消失；
    - jicheng_done、jicheng_won、lixiong_emperor_result、shile_emperor_result、zhangbin_result：待 3-B；
    - chui_escort、xinting_calm、xiebeifa_won：待 5-A；
    - liuyu_regent_result：待 6-A。
- 闸门统计行里的 `resolved_vs_baseline: 1` 没有在输出中逐条列出，我没能确认是哪一条，只能确定它不是新增错误。
- 本轮新增的三个辅助触发器都带参数，没有引入新的 `gvar_read_never_set`。

---

（以下各节为实施报告合并更新后的完整版）

## 一、任务名与文件
- 暂存任务名：**p3-D**。
- 暂存根目录：`D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p3-D\files\`
- 共 13 个文件：新建 7 个，改 6 个。
- **新建**（UTF-8 带 BOM、LF）：
  - `common/scripted_triggers/zz_hd_asp3_triggers.txt`
  - `common/modifiers/zz_hd_asp3_modifiers.txt`
  - `common/story_cycles/zz_hd_asp3_benji_story_cycles.txt`
  - `common/scripted_effects/zz_hd_asp3_effects.txt`
  - `common/nicknames/zz_hd_asp3_nicknames.txt`
  - `localization/simp_chinese/zz_hd_asp3_l_simp_chinese.yml`
  - `localization/english/zz_tr_hd_asp3_l_english.yml`
- **改动**（保持原 BOM 与 LF）：
  - `common/scripted_effects/zz_hd_asp_effects.txt`
  - `common/scripted_triggers/zz_hd_asp_triggers.txt`
  - `common/customizable_localization/zz_hd_asp_custom_loc.txt`
  - `events/zz_hd_asp_events.txt`
  - zh、en 两份 `zz_hd_asp` yml
- 本轮修正动了其中 6 个：asp3 triggers、asp triggers、asp effects、custom_loc、asp3 中英 yml。

## 三、自拟与偏差（更新后）
1. **13 项额外目标改为主目标达成时判定**（照 cc_zhengxi 写法）。逐项列表见第四节第 1 条，**待 boki 拍板**。
2. **口径与替代**
   - 「持」一律写 `has_title`；「入你掌中」用 D26 口径；州界按 280 年后的晋代法理。
   - smyong_xidu b3 已按设计改回「仍持四州」（`has_title`）。原「两州放宽为一郡」的偏差撤销。
   - 李雄 lxiong_chengdi：「C1 结果为称帝」放宽为「C1 已 fire，或本人满足 `hd_asp_is_emperor_trigger`」。
   - zgui_baoxi b1「学馆类修正」改为「学识 ≥14」。
   - zgui_qinlong b1「曾击败汉/前赵」改为「刘曜已死或无地」。
   - **zgui_xizhou「称王」**：读主头衔 `hd_nbc_style` ∈ {wang, tianwang, huangdi}，或已登帝位；gong 不算。
   - xan_menhu b1「年满 66」改为 `age >= 65` 且人在建康省。
   - lxuan b3「益州过半」写死为 ≥51 县（晋代法理下益州 16 郡共 101 县）。
   - syj_jianguo b2「议会全满」写作 `any_councillor = { count >= 5 }`。
   - 人群口径：
     - 「刘渊一系」= 顶头君主属 `house:xiongnu_liu`；
     - 「秦主」= 长安之主，且属 `dynasty:fu_1`；
     - 「晋天子」= 霸权持有者，且属 `dynasty:sima`。
   - **hw_shoushan b1**：取「全族合计 ≥2 个王国级头衔」，即一人持 ≥2 个，或两人各持 ≥1 个。
   - 涉及人物的判定全部走三路读取（`wj_hchar_`、`hd_hb_p_`、`character:`）。辅助触发器为：
     - 首轮已有的 `hd_asp3_*`；
     - 本轮新增的 `hd_asp3_tributary_of_root_trigger`、`hd_asp3_not_regent_trigger`、`hd_asp3_dead_or_my_prisoner_trigger`；
     - 原有的 `hd_asp2_alive/dead/is_char_trigger`。
3. **对 04 地名的三条偏差**
   - **盛乐**：取 `c_uuii_p_1324` 沙陵（成乐男爵领 `b_uuii_p_1336` 在此）。04 写的是「d_tuoba 首府」，那个县实为九原 `c_uuii_p_1407`。
   - **枋头**：取许昌 `c_uuii_p_738`。04 写的「d_yinchuan 首府」是阳翟 `c_uuii_p_1611`。
   - **龙城**：库里没有对应的昌黎县，判定仍取 d_changli 首府 `c_uuii_p_3479`，卡面改为「昌黎郡治（扶黎）」。
4. **专属修正名与数值均为自拟**。不设档位的野望一律定档：桓温三条、刘玄均为 large。
5. **称号**：按卡面「改称号」新建 nicknames 文件。`_desc` 已补，中英都有。
6. **刘玄「接卡附送」的「汉室余胤」修正尚未定义**，归 4-C。0317 选项 a 里留了一行注释代码。
7. **smyong_guanzhong b1「持京兆」**：颙开局即持京兆，会记为开局已有、不发奖。这与设计字面一致，未改。

## 四、需要汇总人处理的事项（更新后）
1. **D56 拍板（待 boki，不阻断）**
   - 共 13 项额外目标改为「主目标达成时判定」，先例是 cc_zhengxi。效果是开局已成立也能在达成时得赏，与 D56「开局已有不发奖」方向相反，需要确认。
   - **设计原文明写「达成时」的 2 项**：
     - smteng_qihuo b1（仍持并州郡）
     - smyong_xidu b3（仍持四州）
   - **首轮自改的 9 项**：
     - smyong_xidu b2（张方在世）
     - smying_taidi b2（卢志在麾下）
     - smying_yexia b1（公师藩在世）
     - smyue_sheji b1（司马毗在世）
     - lxiong_chuanzi b1（李越死或无地）
     - mrc_yanyuan b1（农、宝、德）
     - xan_feishui b3（新亭或桓冲好感）
     - syj_jianguo b3（慕容氏配偶）
     - syj_nankui b2（慕容氏配偶）
   - **本轮审查新增的 2 项**：
     - smteng_beimen b2（并州 ≥4 郡）
     - xan_feishui b2（尚书令）
   - **若要回退某项**：
     - 删去 `hd_asp_complete_effect` 开头对应的 if 块；
     - 在 `zz_hd_asp_triggers.txt` 的 bonusN 分派里恢复该段；
     - custom_loc 与中英 yml 中的 `_N_final` 改回 `_N_todo`，文字去掉「【主要目标达成时判定】」与「达成之时，」。
2. **3-B 采用四个拟名**：jicheng、lixiong_emperor、shile_emperor、zhangbin。不采用就通知 3-D 改卡。
3. **4-C 刘玄卡相关**：「举汉帜」决议须设头衔变量 `hd_j16_lxuan_han`；建好 `hd_j16_hanshi_yuyin_modifier` 后，由指定人取消 0317 a 选项里的注释行。
4. **5-A 待办**：修 `hd_370_feili_enthroned` 与 `hd_nbc_feishui_white`，并确认 370 废立后桓温被装为 hd_court 权臣。
5. **既有问题，未修**：mid_issue 跑在全局岁首脉冲里，root 可能为空。liu_yuan、liu_kun 两张卡的他局补发可能永不成立。本批新写的入场条件都不读 root。
6. **他人文件问题，只报告不改**：`zz_hd_370_startup_effects.txt` 第 125 行把什翼犍京城设在 `c_uuii_p_1333`，注释写「云中（盛乐）」，与 landed_titles 不符：成乐（盛乐）男爵领在沙陵 `c_uuii_p_1324`。如果要让 370 开局京城就在盛乐，需改那一行；但改了之后，syj_jianguo b1 会变成「开局已有」。
7. **首测要点**
   - p3-A 落盘后开 304 局，第 2 天核对「独立且不朝贡」类主目标是否已成立。
   - 370 局三卡与桓温 0321 是否正常弹出。
   - error.log 搜 `hd_asp3`、`hd_asp.03`、`hd_story_`。
8. **生成器不同步**：`scratchpad\p3d\data_p3d.py`、`gen_p3d.py` 已与暂存物不同步，禁止重新生成。

## 五、本期面板行清单（交 F-1）
无。志向卡只显示在本纪野望栏，不出 hev 面板行。

## 六、新增事件号与变量
- **事件**：hd_asp.0317、0318、0319、0320、0321、0330~0337。0322–0329 未占用。
- **新全局变量**：`hd_asp_issued_<卡>`，共 12 张卡：sima_teng、sima_yong、sima_ying、sima_yue、wang_jun、li_xiong、zhang_gui、shi_le、liu_xuan、murong_chui、xie_an、shiyijian。由 `hd_asp_pend_effect` 以 `hd_asp_issued_$CARD$` 设置。
- **新人物变量**：`hd_asp_lxuan_declined`。
- **卡键与野望前缀**：smteng_、smyong_、smying_、smyue_、wjun_、lxiong_、zgui_、sle_、lxuan_、mrc_、xan_、syj_，另有 hw_yihuo、hw_shoushan、hw_fangtou。
- **本轮新增触发器**：`hd_asp3_tributary_of_root_trigger`、`hd_asp3_not_regent_trigger`、`hd_asp3_dead_or_my_prisoner_trigger`。
- **本轮新增本地化键**：`nick_hd_asp_zhaolie_yiyin_desc`。
- **本轮换名键**：`hd_asp_pb_smteng_beimen_2_todo` 改为 `_2_final`，`hd_asp_pb_xan_feishui_2_todo` 改为 `_2_final`。
- **本轮新读取的已有变量**：主头衔变量 `hd_nbc_style`（由 `hd_nbc_found_realm_effect` / `hd_nbc_style_effect` 设置）。
- **旧编号式名 → 语义名**（卡里读的名字）：

  | 原写法 | 现用名 |
  |---|---|
  | B2 `hd_j16_yingjia_result = defender_won` | `hd_j16_yingjia_lost` |
  | B2「颙方胜或白和」 | `_started` + `_done` + NOT `_won` |
  | B3 | `hd_j16_gongshi_result` |
  | Z4 `hd_j16_z04_done` | `hd_j16_jicheng_done` / `_won` |
  | C1 `hd_j16_c01_done` | `hd_j16_lixiong_emperor_result` |
  | Z10 | `hd_j16_shile_emperor_result` |
  | Z2 | `hd_j16_zhangbin_result` |
  | B14 | `hd_j16_zhanggui_qinwang` |
  | 决议 E | 人物旗标 `hd_j16_qihuo_used` |
  | J45 `hd_j16_liuyu_regent_done` | `hd_j16_liuyu_regent_result` |
  | `hd_j16_jingkou_fired`（不存在） | `hd_j16_jingkou_started` |
  | E4-J60 `hd_j16_beifu_done` | 改为直接判「谢玄持广陵」，不读节点变量 |
  | L4 凉王 | 主头衔 `var:hd_nbc_style`，不另设节点变量 |

- **卒年表 PRE**：本任务不设任何 PRE 变量，只读不写。

## 七、待节点实施后核对

| 变量 | 所在卡 / 目标 | 预期设置者 | 状态 |
|---|---|---|---|
| hd_j16_yingjia_started / _done / _won / _lost | smyong_xidu b1；smyong_zhangfang 主 | 3-A，E1-B10 | 已对齐 p3-A |
| hd_j16_gongshi_result | smying_yexia b2 | 3-A，E1-B15 | 已对齐 p3-A |
| hd_j16_zhanggui_qinwang（全局） | zgui_baoxi 主 | 3-A，E1-B70 | 已对齐 p3-A |
| hd_j16_qihuo_used（人物旗标） | smteng_qihuo b2 | 3-A 决议 E | 已对齐 p3-A |
| hd_j16_jicheng_done / _won | wjun_pingfan b1 | 3-B，E1-Z30 | 拟名，待 3-B 采用 |
| hd_j16_lixiong_emperor_result | lxiong_chengdi 主 | 3-B，E1-C10 | 同上 |
| hd_j16_shile_emperor_result | sle_tianwang 主 | 3-B，E2-Z30 | 同上 |
| hd_j16_zhangbin_result | sle_junzi b1 | 3-B，E1-Z10 | 同上 |
| 主头衔 hd_nbc_style = wang/tianwang/huangdi | zgui_xizhou 主 | L4 张骏假凉王，须调用 `hd_nbc_found_realm_effect` | 请 L4 实施者确认 STYLE 传 wang |
| 头衔变量 hd_j16_lxuan_han | lxuan_xinghan 主 | 4-C 决议「举汉帜」 | 不设则卡永不可成 |
| hd_j16_chui_escort（全局或人物变量均认） | mrc_baoqin b1 | 5-A，E4-M20 a | — |
| hd_j16_xinting_calm | xan_feishui b3 | 5-A，E4-J20 a | — |
| hd_j16_xiebeifa_won | xan_huandu b2 | 5-A，E4-J80 | — |
| hd_370_feili_enthroned | hw_yihuo 主 | 5-A，E4-J10 | p1-A 报告指出可能永远设不上 |
| hd_nbc_feishui_white | xan_feishui 主 | 5-A | 全 mod 只读不写 |
| hd_j16_liuyu_regent_result | 刘裕补发 | 6-A，E5-J45 | 按 TEMPLATE §5-15 用 `_result` |