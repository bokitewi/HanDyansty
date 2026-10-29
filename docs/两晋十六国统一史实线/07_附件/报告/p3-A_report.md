# p3-A 最终报告（修正后合并版，已落盘 10-27）

# p3-A 修正报告（第 1 轮审查）

## 〇、逐条处理结果

| # | 级别 | 问题 | 处理 |
|---|---|---|---|
| 1 | major | B2 关键县与目标不一致 | **已修**。关键县 `hd_j16_yingjia_key` 现在存的是选中的「接壤县」本身，不存郡治。理由：这个县必定是 wct 的可达起点，无论 wct 整郡沿用还是拆县，它都一定在战争目标里。 |
| 2 | major | B2 经 wct 回退会夺天子直辖郡 | **已修**（结构性问题见第五节第 1 条）。新增 `hd_j16_yingjia_pick_target_effect` 自己选目标，B2 节点、0103 a、决议 B 共用。<br>守方一方取现任权臣，没有权臣时取颙，且须在天子 realm 内。在其 sub_realm 里找同时满足以下三条的县：<br>• 持有者是该人本人或其下属；<br>• 与起兵者最高领主的国土直接接壤，判据同 `hd_wct_borders_att_trigger`，不看盟友；<br>• 所在郡是「干净郡」（`hd_j16_yingjia_clean_duchy_trigger`）：郡内凡是天子一方的县都属于权臣一方，这样天子直辖县和他王的县都不会进入 wct 候选。<br>京城郡优先。找不到就 WAIT（`no_border_target`，单独一个日志键），不交给 wct 回退。<br>`hd_nbc_war_cb` 胜利仍会转移目标郡，这条 CB 不归本任务，已上报。 |
| 3 | major | 传檄迎驾在 B2 跳过或拒绝后被隐藏，且结局不结算 | **已修**。<br>• 节点外层 limit 放宽为「未 done」或「已开战且尚无 _won/_lost」，所以决议在节点了结后开的战照样由节点结算，并清 `hd_nbc_yingjia_active`。<br>• 决议 is_shown 去掉 `NOT done`，只留 `NOT started`。`started` 不会被清，所以决议全局只能开一次战。 |
| 4 | major | 02 §1.8 继承人自动罢归没有实现 | **已修**。<br>• `hd_j16_join_court_effect` 末尾：角色有 `hd_j16_was_tributary` 时，在他所持的 6 个原朝贡主头衔上设头衔变量 `hd_j16_fief_was_tributary`。不用 primary_title，因为授太傅后它会变。颙开局装配也走这里。<br>• `hd_j16_return_fief_effect` 清掉这个标记。<br>• `hd_j16_restore_tributary_effect` 开头新增每跳检查，不受 365 天冷却限制，只查 6 个头衔。头衔有标记，且持有者在世、未被囚、不在战争中、是天子的直属封臣、不是权臣，就先 `hd_court_strip_office_effect`，再罢归藩国。<br>• 时段与五家补签相同：312 年前，且永嘉未了结。<br>• 日志：`HD_J16 e1_w30 FIRE heir_return_fief`。 |
| 5 | major | 东郡授予排除了玩家天子直辖的情形 | **已修**。条件改为：持有者是天子本人（玩家也算），或是天子一系的 AI 封臣。天子是 AI 就直接授，否则发 0112。0112 本身没有 is_ai 限制。 |
| 6 | major | 卒年表 5 行 K 类缺 PRE | 不在暂存区，**留给汇总人**，见第五节第 2 条。 |
| 7 | minor | 窗口止日早一天 | **已修**。全部改为「>= 止日次日」：B1 305.3.2、B2 306.6.2、B3 306.12.2、B4 306.3.2、B5 306.6.2、B6 307.6.2、B8 308.4.2、B9b 308.3.2、B11 311.4.24、B12 311.7.2、B13 308.6.2、B14 311.6.2。<br>• B7、B9、B10 原本就对。<br>• B14 第一跳是自拟窗口，代码仍写 `< 310.1.1`，注释已写明。<br>• `hd_j16_bawang_end_effect` 的 311.7.1 不是窗口止日，没改。 |
| 8 | minor | 张方任军事议员缺 `remove_existing_councillor` | **已修**，写法照原版 01_puppet_interactions.txt。 |
| 9 | minor | 传檄迎驾：盟友没先断朝贡；宣战失败仍扣威望、上冷却 | **已修**。<br>• 盟友若是天子的朝贡国，先记 `hd_j16_was_tributary`，再 `end_tributary`，然后 add_attacker。<br>• 没开成战（无目标或宣战失败）就退还 300 威望、撤冷却，日志 `decision_chuanxi_refunded`。<br>• 中英 tooltip 已同步说明。 |
| 10 | minor | 入朝辅政接壤、迎驾还洛正统、收乞活范围三处与 02 不符 | **已修**。<br>• 入朝辅政：第三支改为从京城郡反查，郡内有本人一方的县、或有县与本人一方相邻，都算。reach 的三支一并改用 `target_is_liege_or_above = root`，否则封臣的下属县不算。<br>• 迎驾还洛：加 `add_legitimacy = medium_legitimacy_gain`（原版脚本值，mod 没有遮蔽），威望 +100 保留。<br>• 收乞活：改为「持有任一郡治位于 `uuii_han_bingzhou_region` 或 `uuii_han_jizhou_region` 的郡」。按清单第 33 条，280 年后魏郡的法理已改挂司州，所以不能用 `k_uuii_*` 的法理判断。授邺分支的「持并州」同样改用区域。tooltip 已同步。 |
| 11 | minor | B1 周馥、B11「王衍领越众」没做 | **部分修**。0102 中英文案补了周馥（荀藩原本就有）。「王衍领越众」没有机制落点，省略，列入偏差。 |
| 12 | minor | 宣战失败的 WAIT 日志被 not_ready 吞掉 | **已修**。4 处宣战失败改用独立的键：`yingjia_wsf`、`xuchang_wsf`、`poye_wsf`、`zhuisang_wsf`。 |
| 13 | minor | 0701 AI 天子只有约 67% 准奏 | **已修**。选项 b 加 modifier，好感 ≥20 时 factor 为 0。 |

**另做的自查**
- 查了暂存区里所有用 `k_uuii_*` 法理判断州的地方。B9「冀州任一县」本来就用 `uuii_han_jizhou_region`，其余都是按持有头衔判断，不受影响，已核。
- 14 个暂存文件花括号全部配平，都是 UTF-8 带 BOM、LF。中英本地化各 145 行，键一一对应。
- mod 原文件的 base_sha256 修改前复核过，全部一致，没有被并发改动。

## 一、暂存任务与文件清单

暂存任务名：`p3-A`。没有直接写 mod，没有跑生成器，没有开游戏，没有提交。

**新建 5 个**
- `common/scripted_effects/zz_hd_j16_304_court_effects.txt`：工具效果，3-B、3-C 接着用。内容有：
  - 换权臣、迁京城、入朝（含原朝贡头衔打标和清标）、天朝朝贡、罢归藩国、授郡；
  - 朝贡补签，含继承人罢归；
  - 八王时段收尾；
  - 战争结局自判宏、小宏 `_res`、`_skip`、`_wait`、`_army`；
  - 太弟设定。
- `common/scripted_triggers/zz_hd_j16_304_triggers.txt`：本轮新增 `hd_j16_yingjia_border_county_trigger`、`hd_j16_yingjia_clean_duchy_trigger`。
- `common/modifiers/zz_hd_j16_304_modifiers.txt`
- `common/opinion_modifiers/zz_hd_j16_304_opinion_modifiers.txt`
- `common/decisions/zz_hd_j16_304_decisions.txt`

**改动节内文件 5 个**
- `zz_hd_j16_e1_304_effects.txt`：B 节点追加在文件末尾。本轮新增 `hd_j16_yingjia_pick_target_effect`。
- `zz_hd_j16_startup_304_effects.txt`
- `events/zz_hd_j16_304_events.txt`
- 中英两份本地化，各新增 136 键。

**改动 hd_court 共享文件 4 个**（本轮没有再改）
- `hd_court_regent_effects.txt`
- `hd_court_on_actions.txt`
- `events/hd_court_events.txt`
- `common/decisions/hd_court_decisions.txt`

**查过但没改的 2 个**
- `hd_dc_kit_independence_interactions.txt`：第 39 行已有 `hd_court_is_regent_trigger = no`。
- `hd_court_triggers.txt`

**闸门**（结果在 `stage/p3-A_gate.txt`）：error 5，warn 38，没有未定义引用，没有缺失本地化键。
- error：
  - `hd_j16_jinjian_done` 只读不写：由 3-B 的 E2-J11 设置。
  - `yingjia_won`、`yingjia_lost`、`poye_won`、`zhuisang_won` 只读不写，属误报：它们由 court_effects 里的 `hd_j16_$KIND$_won/_lost` 宏设置，闸门会跳过带参数的变量名。`yingjia_lost` 是这次新出现的，因为节点外层 limit 新读了它。
- warn 38 条都是只写不读：fire 结果、`hd_hev_*`、`_skip`、`_att/_def`、`taidi_ying`、`zhanggui_qinwang`。
- 新增的 `_nb_wlog`、`_wsf_wlog` 键是带参数生成的，`hd_j16_fief_was_tributary` 是头衔变量，所以闸门都不统计。

## 二、实现位置（与上一版相同的部分从略）

**开局装配** `hd_j16_304_bawang_setup_effect`，由 `hd_j16_startup_304_effect` 调用：
- `bawang_active` 带 days=2413；
- 颙先结束朝贡、再改投天子，这一步同时在 k_uuii_sili 等他所持的原朝贡头衔上打标；
- 张方入颙宫廷，任军事议员（这次加了 `remove_existing_councillor`）；
- 颙经 install 装为权臣，加 `hd_court_regent_tenure` 2 年。

**B0–B14**：B0 没改。B1–B14 是 E1-B05～B70 共 15 个节点，照 TEMPLATE 写。

**入口另调三项**
- `hd_j16_restore_tributary_effect`：每跳做继承人罢归检查；每 365 天补签一次朝贡。
- `hd_j16_bawang_end_effect`
- `hd_j16_e1_304_kills_effect`

**hd_court 改动**（(a)–(f) 与上一版相同）
- 交接分支加两道闸：`bawang_active`、`handoff_block`；
- 被阻断时 release 并删掉阻断变量；
- 0002、0010 在八王时段内改走 swap；
- D24 占领对胡人豁免，并保留 `hd_nbc_war_cb` 豁免（R4）；
- 空缺检查两条限制；
- 京城变量同步；
- 僭号称帝对 henei_sima 关闭。
- 以上全部以 j16 为闸，`hd_dong_fixed_regent` 避让原样未动。

## 三、自拟与偏差（合并更新）

1. 开局装配只在史实事件规则开启时做；规则关闭时保持旧行为。闸门变量带 days 作硬兜底。
2. 换权臣效果自己取旧权臣，调用方不必另存。新权臣任期旗标 1 年。
3. 罢归藩国给角色加 `hd_j16_bagui`（10 年），B8 读它。
4. 越为打迎驾之战结束朝贡时也记 `hd_j16_was_tributary`。传檄迎驾邀来的盟友同样处理。
5. **（新）B2 目标选法。** 不再取「京城郡」，改为：守方一方（权臣，无则颙）所持、与起兵者最高领主直接接壤、所在郡是干净郡的县，取其郡，京城郡优先；关键县就是这个接壤县。
   - 02 原写「与越**或盟友**接壤」，现在只认越本人，因为 wct 只看攻方本人的国土，盟友接壤照样会触发回退。
   - 找不到就 WAIT（`no_border_target`）。
6. **（新）传檄迎驾。**
   - 全局只能开一次（`started` 不清）。
   - 节点跳过或玩家拒绝后仍然可用。
   - 没开成战就退还威望、撤冷却。
   - 邀请的盟友是好感 <0 的 AI 独立宗王，直接加入攻方，没有玩家邀请事件。
7. B2 中王浚先结束朝贡、再加入攻方，得 8000 兵；虓是天子封臣，不拉入。
8. B4 中刘乔先改投天子，宣称只给一次，宣战失败逐跳重试。刘琨的 2000 兵记在虓名下。
9. B5「越方占任一司隶县」没有实现，只判「迎驾之战已满 90 天」。
10. B10 缪播没有雇主，条件放宽为在世即可。
11. B11 项县改用陈郡郡治 `c_uuii_p_7092`。「王衍领越众」没有机制落点，省略。
12. B12 只处决王衍、司马毗，「越宫廷内其余宗室」不处决。
13. B14 两跳：第一跳 307.1.1–309.12.31（代码 `< 310.1.1`），第二跳 311.1.1–311.6.1。「受敌」按天子是主防守方判。
14. B6 的太傅只在头衔无人持有时用 granted 授予，是实测项。
15. 冯嵩、刘伯根、北宫纯、祁弘只出现在文案里。
16. 决议 A、B、C、D 的 `ai_check_interval` 都是 0（02 原写 B 为 12）。
17. 出镇还藩的 AI「占领 ≥25%」是近似实现。
18. 皇太弟请立：AI 天子只看好感 ≥20（达到即必准）；「军力 ≥ 一半」一条没有实现。被拒者 5 年内不能再请；落选者的主君也对决定者 −40。
19. 收乞活：「邺无主或属天子」按魏郡郡头衔判。**（新）**「持并州或冀州郡」按汉代州的静态区域判（清单第 33 条）。
20. 空缺检查的「永嘉进行中」改读 `hd_304_yongjia_decided`。
21. **（新）继承人罢归的范围比 02 宽。**
    - 02 只写了「权臣死后的继承人」。现在还覆盖「不经换人就失去权臣位、仍是天子封臣的在世原朝贡王」，例如被政变或 release 拿掉的。理由同 F9：防止宗王越来越多地变成天子封臣。
    - 经换人下台的旧权臣，仍由 swap 第 5 步当场罢归。
22. **（新）打标的已知局限。**
    - 标记只打在 6 个名单头衔上。颙的另外三国（k_hezhou、k_qinzhou、k_yongzhou）没有打标；若发生分割继承，持有这三国的继承人仍是天子封臣。
    - 标记跟着头衔走。原朝贡头衔若转给某个天子封臣，那个人会被误罢归。概率低，没修。
23. **（新）东郡授予**：胜后只判一次（`_after` 先设）。条件不满足就不再重试。
24. **（新）0102 文案补了周馥。**洛阳留台没有做成全体通报。
25. **（新）入朝辅政 reach**：原有的「京城县」「天子所在县」两支也一并改用 `target_is_liege_or_above = root`，否则封臣下属的县不算本人一方。

## 四、本期面板行清单（交 F-1，只列不写）

共 15 行，适用开局全部为 le304，变量都在节点 fire 时设：

| 面板变量 | 节点 |
|---|---|
| `hd_hev_j16_xiqian` | E1-B05 张方挟驾西迁 |
| `hd_hev_j16_yingjia` | E1-B10 东海王传檄迎驾 |
| `hd_hev_j16_gongshi` | E1-B15 公师藩、汲桑起兵 |
| `hd_hev_j16_xuchang` | E1-B20 许昌之战 |
| `hd_hev_j16_zhangfang` | E1-B25 颙杀张方 |
| `hd_hev_j16_huanluo` | E1-B30 迎驾还洛 |
| `hd_hev_j16_yingsi` | E1-B35 颖之死 |
| `hd_hev_j16_huaidi` | E1-B40 怀帝立 |
| `hd_hev_j16_poye` | E1-B45 汲桑破邺 |
| `hd_hev_j16_zhuisang` | E1-B46 苟晞破汲桑 |
| `hd_hev_j16_qingjun` | E1-B50 越清君侧 |
| `hd_hev_j16_chutun` | E1-B55 越出屯项 |
| `hd_hev_j16_ningping` | E1-B60 宁平城 |
| `hd_hev_j16_wangmi` | E1-B65 王弥投汉 |
| `hd_hev_j16_qinwang` | E1-B70 张轨勤王 |

## 五、需要汇总人处理的事项

1. **【结构性，请定夺】B2 迎驾之战（A2-F12）**
   - 越在徐州，颙在关中、司隶，两人多半不接壤。B2 现在只打与越直接接壤的权臣领地，所以 AI 局里很可能一直等到窗口关闭（日志 `HD_J16 e1_b10 WAIT no_border_target`）。读 `hd_j16_yingjia_started` 的 B4、B5 会跟着沉睡；B6 仍能靠「颙已死或失权臣」「长安在越一方」触发。
   - 即使 B2 开打，`hd_nbc_war_cb` 的 on_victory 仍会无条件 `conquest_cb_title_transfer` 目标郡，「胜方只换权臣不夺地」做不到。
   - 这已满足 A2-F12 写明的改用方案 B 的条件。请二选一：
     - (a) 改方案 B：开战前先让颙罢归藩国，使颙成为主防守方，wct 回退就只会落在颙的领地上；
     - (b) 由 `zz_hd_nbc_war_cb.txt` 的所有者对 `KIND=yingjia` 免除领地转移。
   - 这两个文件都不在本任务授权范围内，我没有动。
2. **卒年表 5 行 K 类缺 PRE（行为问题）。** 请在第 8 列补 PRE，再重跑 `gen_deaths_effects.py`；DATE10 与 B 段处决块一致，不需要另改：

   | 人物 | 日期 | 请填的 PRE |
   |---|---|---|
   | 张方 `hd_304_zhang_fang` | 306.1.20 | `hd_j16_zhangfang_result` |
   | 颖 `si_ma_ying` | 306.11.19 | `hd_j16_yingsi_result` |
   | 颙 `si_ma_yong` | 307.1.20 | `hd_j16_yong_kill_result` |
   | 腾 `si_ma_teng` | 307.6.1 | `hd_j16_poye_won` |
   | 王衍 `langya_wang_083` | 311.5.15 | `hd_j16_ningping_result` |

3. **B 段链条可能整段沉睡（设计缺口，请定夺）。**
   - 开局时魏郡在颖手里，没有任何节点把邺转出。B3 要求颖已失邺，B9 要求腾持魏郡或冀州的县，决议 E 授魏郡要求邺无主或属天子，三处互相卡住。
   - B11 依赖苟晞有地，而他的东郡只从 B9b 来，也会跟着不触发。
   - 可选的补法：给 B3 补一个「颖失邺」的软摆位，或者放宽 B9。
4. **交给 3-B**
   - 在 `hd_j16_e2_304_effect` 里加一行 `hd_j16_restore_tributary_effect = yes`（凉州补签续到 345）。继承人罢归检查自带 312 截止，在 E2 里调用不会多做事。
   - S4 若读 `hd_j16_b12_done`，改读 `hd_j16_ningping_done`。
   - J1 调 `hd_j16_set_court_capital_effect = { COUNTY = title:c_uuii_p_867 }`，J3b 用 `c_uuii_p_4389`。
   - 由 E2-J11 设置 `hd_j16_jinjian_done`。
5. **交给 3-D**：张轨卡读 `hd_j16_zhanggui_qinwang`；颖卡可读 `hd_j16_taidi_ying`。
6. **交给 5-A**：`hd_j16_handoff_block` 已在 repair 里用后即删，E4-J40 首跳的删除只是冗余兜底。
7. **实测项**
   - 刘乔与虓同为天子封臣能否宣战；
   - 王浚和传檄盟友结束朝贡后加入攻方是否正常；
   - 太傅 granted 能否授上；
   - 第二次换人时丞相能否重建（看日志 `HD218 CHENG_XIANG GRANT_FAILED`）；
   - 原版朝贡是否随继承延续；
   - 张方任议员是否成功；
   - 继承人罢归是否正常触发（看日志 `heir_return_fief`）；
   - `add_legitimacy` 对非天子权臣是否生效。
8. 本期没有生成器需要重跑。

## 六、新增事件号（本轮没有变化）

- B 段：`hd_j16.0101`–`0108`、`0110`–`0114`、`0116`–`0118`。0109、0115 空号。
- 决议附属：`0700` 定储、`0701` 请立、`0702` 授魏郡。

## 七、变量

**旧名 → 新名**

| 02 原写 | 实际用名 |
|---|---|
| `hd_j16_b01_done` | `hd_j16_xiqian_done` |
| `hd_j16_b02_done` | `hd_j16_yingjia_done` |
| `hd_j16_b06_done` | `hd_j16_huanluo_done` |
| `hd_j16_b12_done` | `hd_j16_ningping_done` |

**节点变量**：都是 `hd_j16_<语义>_done/_result/_skip/_wlog`，语义名为 xiqian、yingjia、gongshi、xuchang、zhangfang、huanluo、yingsi、huaidi、poye、zhuisang、qingjun、chutun、ningping、wangmi、qinwang。
- 战争节点（yingjia、xuchang、poye、zhuisang）另有 `_started/_won/_lost/_att/_def/_go/_asked`；本轮新增 `*_wsf_wlog`（宣战失败日志）。
- yingjia 另有：
  - `_key`：本轮起改存接壤县；
  - `_young`；
  - 本轮新增 `hd_j16_yingjia_nb_wlog`（无接壤目标日志）。
- 其他节点专用：xuchang `_prep`；poye、zhuisang `_after`；`hd_j16_poye_qihuo_given`；`hd_j16_qinwang_first_done/_second_done`。

**其他全局变量**：`hd_j16_bawang_active`、`hd_j16_tribute_cd`、`hd_j16_yong_kill_result`、`hd_j16_tan_kill_result`、`hd_j16_taidi_used`、`hd_j16_taidi_ying`、`hd_j16_zhanggui_qinwang`。

**头衔变量（本轮新增）**：`hd_j16_fief_was_tributary`，挂在 6 个原朝贡主头衔上。

**人物变量与旗标**：`hd_j16_was_tributary`、`hd_j16_bagui`、`hd_j16_zhangfang_general`；旗标 `hd_j16_chuzhen_cd`、`hd_j16_chuanxi_cd`、`hd_j16_qihuo_used`、`hd_j16_taidi_asked`。

**新增 scope**：`hd_j16_yj_key`、`hd_j16_yj_reg`、`hd_j16_yj_atop`。

**沿用 hd_court 的变量**：`hd_court_capital_county`、`hd_court_regent_tenure`、`hd_court_qinwang_edict`、`hd_j16_handoff_block`。

## 八、卒年表 PRE 变量的设置处（本轮没有变化）

- tsv 里归本期 B 节点设置的 PRE 现在没有：相关 5 行的 PRE 列都是空的，见第五节第 2 条。
- 节点结果变量只在 fire 时设，跳过、作废、开局前标都不设。
- 处决块 `hd_j16_e1_304_kills_effect` 共调用 11 次 K 类宏 `hd_j16_death_kill_pre_effect`，每次都包在「结果变量已设」之内。与卒年表同一人时共用 `hd_nbc_death_<ID>_done`，不会死两次。

| 人物 | PRE | DATE | DATE10 | 凶手 |
|---|---|---|---|---|
| 张方 `hd_304_zhang_fang` | `zhangfang_result` | 306.1.1 | 316.1.20 | 颙 |
| 公师藩 `hd_j16_gongshi_fan` | `gongshi_result` | 306.9.15 | 316.9.15 | 苟晞 |
| 颖 `si_ma_ying` | `yingsi_result` | 306.9.1 | 316.11.19 | 刘舆 |
| 颙 `si_ma_yong` | `yong_kill_result` | 307.1.20 | 317.1.20 | 梁臣 |
| 覃 `henei_sima_047` | `tan_kill_result` | 308.3.24 | 318.3.24 | 越 |
| 腾 `si_ma_teng` | `poye_won` | 307.3.1 | 317.6.1 | 汲桑 |
| 汲桑 `hd_j16_ji_sang` | `zhuisang_won` | 307.7.1 | 317.12.15 | 田甄 |
| 缪播 `hd_j16_miu_bo` | `qingjun_result` | 309.3.1 | 319.3.15 | 越 |
| 缪胤 `hd_j16_miu_yin` | `qingjun_result` | 309.3.1 | 319.3.15 | 越 |
| 王衍 `langya_wang_083` | `ningping_result` | 311.4.23 | 321.5.15 | 石勒 |
| 司马毗 `henei_sima_432` | `ningping_result` | 311.4.23 | 321.5.5 | 石勒 |

（PRE 列省略了前缀 `hd_j16_`。）

- 覃、毗、汲桑、公师藩、缪播、缪胤六人不在卒年表里，本块是他们唯一的死亡途径。
- 日后若把这六人补进 tsv，必须带上同样的 PRE，否则会变成无条件处决。