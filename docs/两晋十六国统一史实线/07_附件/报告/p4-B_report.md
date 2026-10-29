# p4-B 最终报告（修正后合并版）

# p4-B 修正报告：346 节点与 346 头衔数据（第 4 期第二轮）

审查意见 8 条全部处理完：blocker 1 条、major 3 条已修，minor 4 条已修或写进偏差。闸门已复跑：p4-B 单跑没有新增真实报错，与 p4-C 合跑时 ref_scripted 归零，两路没有重名。p4-B 仍须与 4-C 同批落盘。

本轮只改暂存区，没有写 mod，没跑生成器，没开游戏，没提交 git。

## 〇、审查意见逐条处理

| # | 级别 | 问题 | 处理结果 |
|---|---|---|---|
| 1 | blocker | e2、e3 暂存副本的换行被整份改成了 CRLF | **已修** |
| 2 | major | Z60 第一跳没等 R20 襄国之战打完 | **已修** |
| 3 | major | korean_buyeo_49 开头没有 name | **不归本路**，已写进第五节第 4 条 |
| 4 | major | 议会授席不分玩家，M75 修正强加给玩家 | **已修** |
| 5 | minor | Z60 第二跳先替玩家魏主拆出刘显 | **已修** |
| 6 | minor | 内战目标定死魏郡，结局恒判负 | **已修** |
| 7 | minor | 四处偏离 03 未报告 | 3 处已补，1288 b 写进偏差 |
| 8 | minor | 报告四处与实际不符 | **已更正** |

**1. 换行（blocker，已修）**
- e2、e3 两个暂存副本已转回 LF，保留 BOM。现在 CR 计数为 0；后面的编辑都按 LF 写回。
- 和 mod 原文件直接 diff，只剩真实改动：e2 共 212 行差异，e3 是 +3699 / −16。
- 第一节的编码描述已更正。

**2. Z60 第一跳等 R20 打完（major，已修）**
- `hd_j16_node_liuxian_coup_effect` 在跳过分支之后加了一层等待：已设 `hd_j16_xiangguo351_started` 且未设 `hd_j16_xiangguo351_done` 时，记一次 `WAIT xiangguo_war_ongoing`。
- R20 打完（魏败）、跳过或根本没开战时才执行弑祗。

**3. korean_buyeo_49 无 name（major，交汇总人）**
- 核对属实：mod 的 `zz_hd_oe_characters.txt:79676` 条目开头没有 name，只在 375.11.1 的死亡块里写了 `name = "Geun_cho_go"`。
- 该文件不在 4-B 写入范围，已写进第五节第 4 条。

**4. 议会授席与 M75（major，已修）**
- 原 `hd_j16_b4_council_effect` 拆成两层：
  - 外层只在 RULER 是 AI 时授席；是玩家时记 `SKIP council_<type> player_ruler`，不动议会。
  - 本体改名 `hd_j16_b4_council_core_effect`，只给玩家在选项里自己选了任用的情形调用。
- Z10：玩家石虎改为弹新事件 **hd_j16.1006**，a 拜张豺为宰相 / b 不用。
- M70：玩家燕主改为弹新事件 **hd_j16.1155**，a 托孤慕容恪 / b 不用。
- M75 新写执行体 `hd_j16_pingzhuan_effect`：燕主加「评专权」、慕容评授宰相席，并设 `_result` 与面板变量。
  - AI 燕主直接执行。
  - 玩家燕主弹新事件 **hd_j16.1156**：a 委政于评（执行同上）/ b 自揽朝政（慕容评对燕主 −20，新好感修正 `hd_j16_ping_slighted_opinion`，设 `_skip`）。
  - 节点在分支前只设 done，`_result` 和面板变量挪进执行体，所以选 b 时面板不显示「评专权」。
- 玩家在选项里自选任用的三处改调本体：
  - 1220 a 王猛入秦（`hd_j16_wangmeng_effect`）；
  - 1151 b 重用慕容垂；
  - 1012 a 石遵举兵（`hd_j16_licheng_effect`）。1012 a 的中英选项文本加上了「以冉闵掌兵」，玩家选它即表示同意冉闵入军事席。

**5. Z60 第二跳不先拆玩家封臣（minor，已修）**
- 魏主是玩家、尚未同意（无 `_go`）时，先弹 1051 询问，刘显这时仍留在玩家国中；选 a 设 `_go` 后，刘显才独立并开战。
- 询问前先判这场仗能不能开：刘显仍是封臣，或已独立且与魏接壤，才问；否则等待 `not_adjacent`。
- 魏主是 AI 时行为不变。

**6. 内战目标（minor，已修）**
- 新增 `hd_j16_b4_civil_war_go_effect`，Z20 李城、Z40 石鉴两场内战改用它：
  - 首选郡（魏郡）的首府县在守方国内、且与叛方国土接壤 → 照用魏郡，关键县为邺城。
  - 否则取守方国内与叛方接壤、发展度最高的县（`ordered_sub_realm_county` + `order_by = development_level`，原版 01_fp1_wars.txt:766 等有先例），以它所在郡为目标，开战后把 `_key` 改成这个接壤县。wct 规则 2 从接壤县出发，所以它必在战争目标内。
  - 两国完全不接壤时照用魏郡（wct NO_BORDER）。
- 叛方赢了就是拿下接壤县，PRE 随之设上。

**7. 四处偏离 03（minor）**
- **1288 b「清君侧」宣称：不做，写进偏差第 34 条。** 理由：mod 现有的清君侧 CB `hd_dc_ten_qingjunce_cb` 情境 ① 要求攻方身上有 `var:hd_dc_ten_qjc_target`，指名一个现任权臣，且攻方 liege 是天子。天子拒绝授权时朝中并没有权臣可指名，硬塞会造成悬空目标，也不宜为此新建 CB。
- **1210 改为夺位后 60 天：已修。**
  - 用 `trigger_event = { id = hd_j16.1210 days = 60 }`。
  - 卒年表苻法 357.9.15 到期、PRE 一设就执行，等不到 60 天。所以玩家苻坚时，节点先暂扣苻法卒年：设 `hd_nbc_death_lueyang_fu_019_done` 加 `hd_j16_fufa_hold`。
  - 1210 a 撤销暂扣，下一跳由卒年表执行（凶手苟太后）；b 维持暂扣，即赦免。
  - 1210 的 trigger 加了「苻法在世」。
- **M50 段龛入燕宫廷：已修。** 燕胜后调 `hd_j16_b4_join_court_effect`，RULER 取 `global_var:hd_j16_guanggu_att`。只召 AI、已无地的段龛；仍有残地的不动，照样由 PRE 处死。
- **通报：已补 3 个天下通报。**
  - Z25 石冲开战时发 **hd_j16.1016**。
  - Z20 李城内战开战时发 **hd_j16.1013**。
  - Z40 石鉴内战开战时发 **hd_j16.1022**。
  - 03 §2.4 要求冉闵收到 Z20、Z25、Z40 三次通报，现在两条内战分支也都有了。

**8. 报告更正（minor，已改）**
- e2、e3 编码改为「BOM，LF」。
- 朱蕃「库卒 349、到时由其继承人接手」一句已删。是否给他补一行卒年表 N，转汇总人定（第五节第 5 条）。
- 撤销文件：审查已核对，这 23 个键在 zz_hd_404_titles 和 zz_hd_531_titles 里全部有覆盖，370 undo 里的旧值在 404、531 开局都不生效。原「531 指向死人」的担心作废，见第五节第 3 条。
- 闸门数字已按本轮复跑结果更新，见第五节第 10 条。

## 一、暂存任务与文件

暂存任务名 **p4-B**，暂存目录：D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p4-B\files

没有写 mod，没跑生成器，没开游戏，没提交 git。不需要决议文件，所以没建。

**改动 3 个文件（编码沿用原文件）**
- `common/scripted_effects/zz_hd_j16_e2_346_effects.txt`（BOM，LF）
  - 新增 E2-Z90、E2-Z95 两个节点。
  - 入口末尾加 `hd_j16_e2_346c_effect = yes`。
  - E2-J90/J91 没改：03 给它们加的只有「灭蜀后触发刘玄去留 E2-X70」，X70 由 4-C 读 `hd_nbc_fashu_won` 自判。
- `common/scripted_effects/zz_hd_j16_e3_346_effects.txt`（BOM，LF）
  - 新增 E3 节点 39 个，另有本路小工具。
  - 迁入的 5 个节点只补差异，没有重写。
  - 紧接 `hd_j16_node_fujian_effect` 加 `hd_j16_dir_w30_effect = yes`。
  - 入口末尾加 `hd_j16_e3_346c_effect = yes`。
- `history/titles/zz_hd_346_titles.txt`（BOM，LF）
  - 动笔前一刻才 stage edit，只改现有行，共 23 行，没有新增同日行。

**新建 6 个文件（UTF-8 带 BOM，LF）**
- `events/zz_hd_j16_346_events.txt`：`namespace = hd_j16`，66 个事件。
- `localization/simp_chinese/zz_hd_j16_346_l_simp_chinese.yml`、`localization/english/zz_hd_j16_346_l_english.yml`：中英各 265 键，一一对应。
- `common/scripted_triggers/zz_hd_j16_346_triggers.txt`
- `common/modifiers/zz_hd_j16_346_modifiers.txt`：11 个修正。
- `common/opinion_modifiers/zz_hd_j16_346_opinion_modifiers.txt`：11 个好感修正。

## 二、实现概要

**节点写法**全部照 TEMPLATE：
- 自保护：`global_var:hd_j16_start_year >= 370` 时设 done。
- 跨开局按 03 §0.2：304、346 走心跳；370、404 自保护（新节点）或前标（迁入节点）。
- 窗口按「止日的次日」判截止，解析前先清 scope，WAIT 日志只记一次。
- `_result` 与面板变量只在节点 fire 或真正执行时设。

**战争节点**
- 宣战：`hd_j16_b4_war_go_effect` → `hd_j16_b1_war_effect`（经 wct；封臣自己开不成时由其最高领主宣战）。内战（Z20、Z40）改走 `hd_j16_b4_civil_war_go_effect`。
- 开战成功才设 `_started`、攻守方、关键县，并给事件兵；失败下一跳重试。
- 结局：用 `hd_j16_304_war_result_effect` 按关键县自判 `_won/_lost`，并自清 `hd_nbc_<KIND>_active`。不进分发表。
- 攻方或其最高领主是玩家时先弹出兵问询：a 设 `_go`，b 跳过；`_asked` 60 天内不重复弹窗。

**被杀者与夺位**
- 卒年表有行的，节点只在史实结果成立时设 PRE，由卒年表执行；玩家走「大限」。
- 战争类 PRE 都在胜负判定之后才设。
- 夺位一律用 `hd_370_take_realm_effect`，不当场杀人。
- 玩家选偏离分支时，用 `hd_j16_b4_spare_effect` 预设 `hd_nbc_death_<ID>_done`。

**玩家议会**：节点不直接改玩家议会（外层包装只对 AI 授席）；玩家经事件选项（1006、1155、1156、1012 a、1151 b、1220 a）自己决定。

**节点清单**

| 线 | 节点 |
|---|---|
| E2（e2_346） | Z90 东宫之变、Z95 石虎称帝 |
| E3-Z / R（后赵、冉魏） | Z10 石世继统、Z20 李城、Z25 石冲、Z40 石鉴弑遵、R05 杀胡令、Z50 石祗称帝、R20 襄国、Z60 两跳（刘显弑祗 / 刘显亡） |
| E3-Q / Y（前秦、姚氏） | 继统保险（自拟）、Q05 三秦王、Q15 苻健称帝、Q18 苻生继统、Q20 后续（苻法之死、苟氏入宫）、Q25 王猛、Q30 张平、Q40 四公、Y10 姚襄附晋、Y20 山桑、Y40 三原 |
| E3-M（前燕） | M10 后续：迁蓟、M20 廉台、M25 克邺、M30 称帝、M40 段龛、M50 广固、M60 迁邺、M65 洛阳、M70 暐继统、M75 评专权、M80 垂奔秦 |
| E3-J（东晋） | J05 褚裒、J10 殷浩、J15 殷浩废、J20 伐秦、J40 哀帝继统、J45 录尚书事、J50 司马奕继统、J60 枋头 |

**迁入节点的补差异**
- R10：删去「冉闵无地」；加上游 `hd_j16_shahu_done`；加「未下狱」。
- M10（风味 #10）：「石虎已死」改为必要条件，用 `hd_j16_dead_trigger` 判；上游加 Z20 或 R10 已了结；迁都蓟另写一个后续块。
- J30：加上游 `hd_j16_huanqin354_done`；洛阳之主是姚氏时设 `hd_j16_beifa_yishui`。
- Q20：加后续节点。
- Q10：不改，「苻健已继承汲郡」已含在 `is_landed` 判断里。

**冉闵、前燕两条玩家线（03 §2.4 逐条落实）**

| 扮演 | 依次遇到 |
|---|---|
| 冉闵 | 通报 1010 / 1013、1016、1025 / 1022 → R05 1030 → R10 hd_nbc.0130 → R20 1040 → Z60 1051 → M20 守方（通报 1111，被擒走大限）→ 储君面对 M25 出降 / 死守 1112 |
| 慕容儁 / 燕主 | M10 hd_nbc.0120 → R20 援赵 1041 → M20 1110 → M25 1113 → M30 1120 → M50 1130 → M60 1135 → 托孤 1155 → M65 1140 → 评专权 1156 → M80 1151 → J60 守方 |
| 石虎 | Z90 1002 三选一 → Z95 1004 → 托孤 1006 |
| 石世、石遵、石鉴、石冲、石祗 | 1011、1012、1020、1021、1015、1045，都有选项 |

- 玩家当事人一律给选项。不直接夺玩家头衔，不直接杀玩家，不直接改玩家议会，不直接拆玩家封臣。

**跨节接口（照汇总人 10-27 定名）**
- E3-J60：KIND=fangtou，产出 `hd_j16_fangtou_done/_won/_lost`，以攻方晋论胜负。
  - 晋败时设全局 `hd_j16_yuanzhen_blamed`。
  - 燕胜时给慕容垂加人物旗标 `hd_j16_fangtou_gong`，加之前先判在世。
- E3-J45：fire 时设 `hd_j16_huanwen_regent_result`。
- E3-M80：fire 时设 `hd_j16_chui_benqin_result`；秦主授垂华阴 `c_uuii_p_850`，与 370 开局对齐。

**346 头衔数据（23 行）**

| 项 | 改动 |
|---|---|
| F1 冉闵 | 魏郡斥丘 `c_uuii_p_6918` 授冉闵，liege 为 d_weijun |
| F4 段龛 | d_qiguo 授段龛（作后赵封臣），另授益、临淄、广县三县 |
| #21 百济 | d_baiji 及 3 县换成近肖古王 `korean_buyeo_49` |
| #19 谢尚 | 南豫州、淮南、历阳三郡及世族头衔 c_nf_chenjun_xie 改为直属 h_china |
| #19 交州 | 交趾、九真两郡归朱蕃 `zhu_fan`，直属天子；朱蕃另领龙编县 |
| #19 江州 | k_jiangzhou 与彭泽郡（郡和 5 县）换给桓云 `longkang_huan_018` |

- 引用的人物 ID 都已核对：出现在 `docs/人物审查/合并记录_2026-10-27.csv` 里的都是保留方，没有被删的 ID。
- 例外：korean_buyeo_49 在 mod 里缺开头 name（第五节第 4 条）。

## 三、自拟与偏差

**头衔数据**
1. **冉闵的县**：库里没有「内黄」县，改授魏郡里的非首府县斥丘，邺城不动。
2. **江州换桓云**：依据是谢永 347.1.1 即死。桓云库卒 360；370 开局江州也在桓氏手里，作为旁证。仍属记忆·待核。只给王国头衔、不给县的持有者站不住，所以彭泽郡连同 5 县一起给了他。
3. **交州**：
   - landed_titles 里没有日南郡，只改了交趾、九真。
   - 广州诸郡留卞瞻，k_uuii_jiaozhou 仍归他。
   - 朱蕃不在卒年表里，开局后未来日期的 history 死亡不执行，所以他按引擎自然寿命走（第五节第 5 条）。
4. **附 c 武街没做**（03 标为可选）：武街法理属阴平郡，改归前凉会成为飞地。
5. **段龛的县**：给了 3 县，其余 5 县仍归原郡守，他们成为段龛的封臣。

**夺位、内战与卒年**

6. 03 原写 `hd_nbc_seize_realm_effect`（当场杀人，还会杀玩家），现在一律改为 take_realm 加卒年表 PRE，涉及 Z20、Z40、Z60。
7. Z20 玩家石世拒之：
   - 石遵无地时，把河内郡授给他（03 写的是键待核的「李城所在郡」），前提是郡守是 AI、且在石世国内。
   - 石遵随后独立，得到对赵主主头衔的宣称，开内战 licheng。
   - 石遵胜了才设 PRE。
8. Z40 玩家石遵选 a（谋略检定）：基础 50/50。
   - 自己谋略 ≥15 时成功权重 ×1.5；冉闵谋略 ≥15 时 ×0.5。
   - 成功：冉闵下狱（R05、R10 随之在窗口末跳过），石遵卒年预设 done。
   - 失败：同选 b，由石鉴起兵。
9. Z60 拆成两跳，窗口自拟：
   - 第一跳 351.3.1–351.12.31。R20 战争进行中时等待（审查修正）。刘显不在石祗处时先召入其宫廷。
   - 第二跳 352.1.1–352.6.1。玩家魏主先问后拆（审查修正）。
10. R20 魏胜时，当场调卒年核心 `hd_j16_death_kill_pre_effect`（凶手冉闵，PRE 为 `hd_j16_xiangguo351_won`）处死石祗。与卒年表共用同一个 done，不会死两次。
11. M20 廉台：
    - 03 原写「被俘才杀，否则负伤、30 天后再判」，简化为燕胜即设 PRE，由卒年表在 352.6.1 处死冉闵。
    - 目标郡依次取中山、常山、魏主首府所在郡。
12. **刘群**：燕胜而刘群不在魏主处时，由 M20 预设他的卒年 done。4-C 不必重复。
13. **内战目标（审查后新增）**：Z20、Z40 的内战目标不再定死魏郡，规则见第〇节第 6 条，由 `hd_j16_b4_civil_war_go_effect` 实现。叛方赢的是接壤县，不一定是邺城。

**前燕**

14. M25 玩家魏主出降：除首府一县外，把头衔和封臣交给燕主并称臣（玩家自己选的，不算夺头衔）。选死守则照常开战，不再问。
15. M30「冀幽两州 ≥3 郡」近似为：汉冀州、幽州静态区域内 ≥12 县。
16. M75「评专权」修正加给燕主：国库、封臣好感都是君主一侧的数值。
    - AI 燕主直接加。
    - 玩家燕主经 1156 a 才加；选 b 时慕容评对燕主 −20（审查修正）。
17. M80 的华阴县只在持有者是 AI、且属秦一方时才授。玩家燕主选 b 时给垂授军事席（玩家自选，调本体）。
18. M50 燕胜后，段龛只有在 AI、已无地时才召入燕宫廷；仍有残地的不动，由卒年表照常处死。
19. Z10、M70 遇玩家君主时，改发 1006、1155 问是否任用张豺、慕容恪；03 原写直接授席。

**前秦、姚氏**

20. Q05 照 03 实现，但卒年表苻洪仍是 N 350.1.1，与 Q05 窗口同一天，而心跳先跑卒年。表改之前，Q05 实际不会触发（见第五节第 2 条）。
21. **继统保险（全新自拟）**：
    - 库中苻洪有长于苻健的儿子 `lueyang_fu_036`，姚弋仲有长于姚襄的姚益、姚若。不设储君时，地会传给长子，Q10、Q15、Q18 和 Y10、Y20、Y40 整条线都会跳过。
    - 做法：苻洪在 349.10–350.6、姚弋仲在 351.10–352.6，各自为 AI 时用 R-继统设储。
22. **无雇主的当事人**：石宣、石韬、石遵、石鉴、慕容垂的人物数据都没写 employer。他们是 AI、无地、且在人才池里时，Z90、Z20、Z40、M80 在等待分支里先召入主君宫廷（`hd_j16_b4_join_pool_effect`），下一跳再判。已在别国宫廷的人不抢。
23. Q20 后续 1210（审查修正）：
    - 按 03 改为夺位后 60 天弹出，等待期间暂扣苻法卒年（设 `hd_j16_fufa_hold` 和预设 done），a 撤销暂扣、b 维持。
    - 事件没能弹出（苻坚已死等）时，苻法按自然寿命走。
24. Q25 的「不是别国议政大臣」写成 `is_councillor = no`。
25. Q30 张平须是独立君主才开战，否则只做人事。
26. Q40：
    - 四公中 realm_size 最大者为首起兵。
    - 玩家选 b 招抚：四公对苻坚 +30、王猛对苻坚 −20，四人卒年预设 done。

**修正与职位**

27. 杀胡令修正近似为同文化好感 +10、异文化好感 −40：引擎没有按文化名设的好感修正。
28. 「奉晋正朔」改名 `hd_j16_b4_jin_fanchen_modifier`，用于段龛、姚襄、苻洪选 b。原因是 4-C 杨初可能定义 03 的原名 `hd_j16_jin_fanchen_modifier`，两边并行会重名。
29. 张豺、慕容恪、慕容评、王猛授的是宰相席（councillor_chancellor，照 218、253 写法加贤望豁免），不是丞相头衔：丞相 `e_WJ_minister_cheng_xiang` 是天子朝官。
30. 1012 a 的选项文本加了「以冉闵掌兵」：玩家石遵选它即同意冉闵入军事席。
31. J45 没调 `hd_370_regency_effect`（它写死了 `character:longkang_huan_017`，304 局取不到人），另写 `hd_j16_huanwen_regent_effect`，全部改用 scope。

**东晋**

32. J05 的「惭恚」写成压力 +50。J10 的许昌取颍川郡 d_yinchuan，荀羡加入攻方。
33. J15 天子是玩家时，另发 1283（03 没写）。
34. **J45 1288 b 没给「清君侧」宣称修正**：只给桓温 −40 好感。理由见第〇节第 7 条：现有清君侧 CB 要指名一个现任权臣，天子拒绝授权时无人可指，也不宜为此新建 CB。
35. J20 的「王猛扪虱」只在桓温是玩家时弹 1287。
36. J60 只打汲郡，没加邻郡。秦援燕：AI 秦主直接加入守方；玩家秦主弹 1292。

**事件与年号**

37. 03 没写的天下通报，共新增 17 个：1005、1013、1016、1022、1025、1046、1050、1111、1114、1121、1126、1152、1206、1216、1285、1291、1293。其中 1013、1016、1022 是本轮按审查补的。
38. 战争节点的面板变量在开战时设，照 304 先例。
39. 太宁、皇始、元玺三个年号用了新键（见第五节第 2 条）；元玺没复用 `SG_nianhao_yuanxi`，那个键是「元熙」。

## 四、本期面板行清单（交 F-1，只列不写）

- 共 33 行，适用开局都是 **le346**（304 或 346）。都只在 fire、开战或真正执行时设，自保护、跳过时都不设；M75 只在执行时设（1156 b 不设）。
- 变量名一律为 `hd_hev_j16_` 加下面的语义名：
  - 后赵、冉魏：donggong、shihu_di、licheng、shichong、shijian、shahu、shizhi、xiangguo351、liuxian_coup、liuxian
  - 前秦、姚氏：sanqin、jiandi、wangmeng、zhangping、sigong、yaoxiang_fujin、shansang、sanyuan
  - 前燕：liantai、yecheng352、yandi、duankan、guanggu、qianye、luoyang365、pingzhuan、chui_benqin
  - 东晋：chupou、yinhao、yinhao_fei、huanqin354、huanwen_regent、fangtou

## 五、需要汇总人处理的事项

1. **p4-B 必须与 4-C 同批落盘。** 单跑闸门那 2 条 ref_scripted 就是 `hd_j16_e2_346c_effect`、`hd_j16_e3_346c_effect`；与 4-C 合跑时归零。
2. **卒年表与年号**
   - 卒年表 tsv：苻洪 `lueyang_fu_002` 由 N 350.1.1 改为 K 350.3.1，`death_murder`，凶手 `hd_j16_ma_qiu`，不带 PRE（03 §7「非节点 K」）。改完重跑 `gen_deaths_effects.py`。
   - 年号键注册：`SG_nianhao_taining`（太宁）、`SG_nianhao_huangshi`（皇始）、`SG_nianhao_yuanxi_yan`（元玺）。要改 `WJ_tianjia_era_names.txt` 两处，外加中英 WJ_names。注册之前，称帝后的年号显示为空。
3. **370 头衔与撤销文件（不归本路写，交 5-A1）**
   - 本路改的 23 个键，370、404、531 头衔文件都有覆盖（审查已核对），这三个开局都不受影响。
   - `zz_hd_370_undo.txt` 里这些键的恢复值仍是旧的 346 值，只影响「370 撤销后」的状态。建议 5-A1 同步：斥丘、齐国郡与 3 县、百济与 3 县、淮南、历阳、c_nf_chenjun_xie、交趾、九真、龙编、江州、彭泽郡与 5 县。南豫州在 370 是 holder = 0，没有撤销行。
   - 370 的百济（d_baiji 及 3 县）建议也改为 `korean_buyeo_49`（他卒于 375.11）。
4. **korean_buyeo_49 无名**：`history/characters/zz_hd_oe_characters.txt` 约 79676 行的条目开头要补 `name = "Cho_go"`（照原版）。改后重跑 hbirth 生成器。这个文件不在 4-B 写入范围，也不默认归 4-C，请汇总人指派或自行补丁。
5. **朱蕃去留**：要么给卒年表补一行 N（库卒 349），让交州按时传给继承人；要么维持现状，让他按自然寿命走。
6. **1210 时序漏洞（交 6-A）**：hd_nbc.0145 a 若在 357.9.15 之后才 fire，心跳先跑卒年，苻法会在 fufa 节点暂扣之前就被处死，玩家收不到 1210。根治办法是在 0145 a 里给玩家苻坚设暂扣（`hd_j16_fufa_hold` 加 `hd_nbc_death_lueyang_fu_019_done`）。0145 是旧 nbc 事件，本路不能改。
7. **hd_nbc.0150 文案**：「伊水破姚襄」的切换（读 `hd_j16_beifa_yishui`）。旧 nbc 事件和本地化不归本路，交 6-A。
8. **「奉晋正朔」修正**：`hd_j16_b4_jin_fanchen_modifier` 是否与 4-C 的 `hd_j16_jin_fanchen_modifier` 合并，由汇总人定。
9. **告知 4-C**：
   - 刘群「不仕魏则卒年预设 done」已由 M20 做。
   - 魏主、燕主、秦主的解析可以复用本路的 `hd_j16_b4_res_wei/yan/qin_effect`。
   - 授议政席可复用：`hd_j16_b4_council_effect` 只对 AI 君主生效；`hd_j16_b4_council_core_effect` 不判 AI，玩家在选项里自选时用。
10. **闸门结果**
    - p4-B 单跑（--compare baseline.json --only-changed，结果在 D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p4-B_gate.txt）：error 63，warn 57。
    - error 里 ref_scripted 2 条，即第 1 条的 4-C 入口。
    - 另有 gvar_read_never_set 61 条，全部是 `$KIND$` 参数拼接变量名的误报，闸门认不出。来源有四处：`hd_j16_b4_war_go_effect` 设 `_started/_att/_def/_key`；`hd_j16_304_war_result_effect` 设 `_won/_lost`；`hd_j16_b4_reply_go_effect` 设 `_go`；`hd_j16_b4_ask_effect` 设 `_asked`。
    - 比审查时多的 2 条也是同类：`hd_j16_liuxian_go`（Z60 第二跳现在直接读，由 1051 a 的 reply_go 设）和 `hd_j16_guanggu_att`（M50 召段龛入宫时读，由 war_go 设）。
    - warn 57 都是只写不读：PRE（卒年宏按参数读）、`hd_hev_*`（F-1 读）、`_result`、`_skip`、`hd_j16_ranmin_jailed`。比审查时多的 1 条是 `hd_j16_pingzhuan_skip`。
    - p4-B 与 p4-C 合跑（结果在 D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p4-B_fix_combined_gate.txt）：error 76（审查时的 74 加上述 2 条），全部是同类参数误报；ref_scripted 归零。本轮新增的事件号 1006、1013、1016、1022、1155、1156 和新效果名，在 4-C 暂存里都没有重名。
    - 各文件大括号配平；所有改动文件都是 BOM、LF、0 个 CR。
11. **实测项**：
    - take_realm 用在「廷臣或封臣夺主」；
    - 脚本 start_war 加 add_defender 援军；
    - 1020 的 imprison；
    - 1112 出降的头衔转移；
    - set_realm_capital；
    - 召入宫廷后 `top_liege`、`employer` 的判定；
    - 继统保险的 set_designated_heir；
    - J45 自写权臣效果在 304 局能否装上；
    - 冉闵开局有地后，hd_nbc.0130 的独立与称帝；
    - 段龛持齐国郡后，M40、M50 能否跑通；
    - 内战接壤县目标与关键县改写（Z20、Z40）；
    - 1210 的 60 天延迟、暂扣与撤销。
12. **生成器**：本路不需要重跑，没改人物数据。第 4 条若改人物，要重跑 hbirth。

## 六、新增事件号与变量

**事件（66 个，namespace hd_j16）**
- 1001–1006：东宫之变、石虎称帝、张豺托孤（1006 本轮新增）
- 1010–1013：李城举兵（1013 李城内战通报，本轮新增）
- 1015、1016：石冲（1016 通报，本轮新增）
- 1020–1022、1025：石鉴弑遵（1022 石鉴起兵通报，本轮新增）
- 1030、1031：杀胡令
- 1040、1041：襄国之战
- 1045、1046：石祗称帝
- 1050、1051：刘显
- 1110–1114：廉台、克邺
- 1120、1121：慕容儁称帝
- 1125、1126：段龛据齐
- 1130：广固
- 1135：迁邺
- 1140：洛阳
- 1150–1152：慕容垂奔秦
- 1155、1156：慕容恪托孤、评专权（本轮新增）
- 1205、1206：三秦王
- 1210：苻法之死
- 1215、1216：苻健称帝
- 1220：王猛
- 1225：张平
- 1230：四公
- 1250、1251、1255：姚襄
- 1280：褚裒
- 1282–1285：殷浩
- 1286、1287：伐秦、扪虱
- 1288–1291：录尚书事
- 1292、1293：枋头
- 1294：继统提示

本节号段（1000–1299）其余号码未占用。

**节点变量**：`hd_j16_<语义>_done/_result/_skip/_wlog`；战争节点另有 `_started/_won/_lost/_att/_def/_key/_go/_asked/_wsf_wlog`。
- 语义名：donggong、shihu_di、shihu_heir、licheng、shichong、shijian、shahu、shizhi、xiangguo351、liuxian_coup、liuxian、sanqin、jiandi、fusheng_heir、fufa、wangmeng、zhangping、sigong、yaoxiang_fujin、shansang、sanyuan、yannan_ji、liantai、yecheng352、yandi、duankan、guanggu、qianye、luoyang365、yanheir、pingzhuan、chui_benqin、chupou、yinhao、yinhao_fei、huanqin354、aidi_heir、huanwen_regent、feidi_heir、fangtou。
- 其他全局变量：hd_j16_donggong_alt、hd_j16_licheng_go、hd_j16_shichong_rose、hd_j16_shijian_go、hd_j16_ranmin_jailed、hd_j16_liuxian_rose、hd_j16_liuxian_fall_result、hd_j16_sigong_rose / _leader、hd_j16_yecheng352_wait（30 天）/ _hold / _def_asked、hd_j16_beifa_yishui、hd_j16_yuanzhen_blamed、hd_j16_fufa_hold（本轮新增）、hd_j16_pingzhuan_skip（1156 b 设）。
- 人物旗标：hd_j16_fangtou_gong。

**新 KIND（都由节点自判，不进分发表）**：licheng、shichong、shijian、xiangguo351、liuxian、liantai、yecheng352、guanggu、luoyang365、zhangping、sigong、sanyuan、chupou、yinhao、huanqin354、fangtou。

**新工具与触发器**
- 效果：
  - 解析：hd_j16_b4_res_zhao/wei/yan/qin/jin_effect。
  - 议政席：hd_j16_b4_council_effect（只对 AI 君主）、hd_j16_b4_council_core_effect（本轮新增）。
  - 召入宫廷：hd_j16_b4_join_court_effect、hd_j16_b4_join_pool_effect。
  - 开战：hd_j16_b4_war_go_effect、hd_j16_b4_civil_war_go_effect（本轮新增）、hd_j16_b4_war_decide_effect。
  - 问询与回复：hd_j16_b4_ask_effect、hd_j16_b4_reply_go/no_effect。
  - 其他：hd_j16_b4_spare_effect、hd_j16_pingzhuan_effect（本轮新增）。
- 触发器：hd_j16_b4_shi/ran/yan/qin_lord_trigger、hd_j16_b4_adjacent_trigger、hd_j16_b4_under_trigger、hd_j16_b4_jin_vassal_trigger。
- 好感修正：本轮新增 hd_j16_ping_slighted_opinion（见疏，−20，5 年）。

**03 旧写法 → 语义名**
- `hd_nbc_yinhao_lost` → `hd_j16_yinhao_lost`（J10 自判，J15 读它）。
- 「石虎已死（hd_nbc_death_shangdang_shi_010_done）」→ `hd_j16_dead_trigger`。
- A2 Z13（337 立石宣）→ `hd_j16_shisui_done`。本路没有读它：局面条件已经包含「石宣在世、石虎是赵主」。
- E3-J60「燕胜」→ `hd_j16_fangtou_lost`（以攻方晋论）。
- 03 的 `hd_j16_jin_fanchen_modifier` → 本路的 `hd_j16_b4_jin_fanchen_modifier`。
- 刘太后用库中 `xiongnu_liu_047`（与 tsv 一致），不是 03 的 `hd_j16_liu_shi_shihu`。

## 七、卒年表 PRE 的设置位置

gen_deaths.py 读 mod、不读暂存，以下行号按本轮修改后 grep 暂存副本重新核对。

| PRE | 设置位置 | 对应卒年 |
|---|---|---|
| hd_j16_donggong_result | e2_346:277；346 事件 :47（1002 c）、:73（1003 a） | 石韬、石宣 |
| hd_j16_licheng_result | e3_346:645（内战胜）、:750（夺位执行体） | 张豺、石世、刘太后 |
| hd_j16_shichong_result | e3_346:810（石冲败） | 石冲 |
| hd_j16_shijian_result | e3_346:900（内战胜）、:1006（夺位执行体） | 石遵 |
| hd_j16_shahu_result | e3_346:1096 | 孙伏都 |
| hd_j16_liuxian_coup_result | e3_346:1362 | 石祗 |
| hd_j16_liuxian_fall_result | e3_346:1417 | 刘显 |
| hd_j16_sigong_result | e3_346:1945 | 四公 |
| hd_j16_sanyuan_result | e3_346:2241 | 姚襄 |
| hd_j16_liantai_result | e3_346:2381 | 冉闵、刘群 |
| hd_j16_guanggu_result | e3_346:2681 | 段龛 |

- 另有 R20 魏胜时在 e3_346:1230 当场调卒年核心处死石祗，PRE 为 `hd_j16_xiangguo351_won`，与卒年表共用同一个 done。
- 苻法（PRE `hd_hev_346_fujian_coup`）：玩家苻坚时，由 fufa 节点暂扣，1210 a 撤销、b 维持。
- `hd_hev_346_ranmin`（石鉴、李农）和 `hd_hev_346_fujian_coup`（苻生、苻法）由现有 `events/zz_hd_nbc_events.txt` 的 0130 a、0145 a 设，本路没动。
- tsv 里 346–370 段剩下的 6 个 PRE 归 4-C：zhangzuo、zhangguan、songhun、tianxi、liangshiwang、yangjun。

## 八、03 写明交 A4/370 节、本路未做的项

- E3-M85 金刀计、E3-Q60 洛阳、Q70 东征、M90 燕亡、M91 慕容评归秦、E3-J80 寿春、E4-J10 废立（含读 J45 权臣状态、J60 袁真获咎）。
- 桓温卒年（373）、王猛卒年。
- 姚苌后续、杨安取成都、伐仇池、代亡后分地。
- 370 节新建人物（梁熙、苟苌、梁成、燕凤、朱肜等）。
- 导演 S1–S7（4-A 已做）。
- 张重华、杨初、刘群、刘玄的节点，四人宫廷安置，startup_346（都归 4-C）。

## 仍未解决项

| 事项 | 归属 |
|---|---|
| korean_buyeo_49 补 name 并重跑 hbirth | 汇总人 |
| 1210 时序漏洞，根治须改 hd_nbc.0145 a | 6-A |
| 1288 b 的清君侧不做 | 已写进偏差第 34 条 |
| 朱蕃卒年 | 汇总人定 |
| 苻洪卒年表改 K、年号键注册 | 汇总人 |
| 370 undo 同步 | 5-A1 |
| 「奉晋正朔」修正是否合并 | 汇总人定 |
| 第五节第 11 条实测项 | 实测 |