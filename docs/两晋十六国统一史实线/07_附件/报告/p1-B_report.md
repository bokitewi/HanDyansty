## p1-B「旧入口转发与删过渡桥」实施报告

暂存任务名为 p1-B，8 个文件都用 stage.py edit 登记。暂存区在 D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p1-B\files\。
- 原文件都是 UTF-8 带 BOM、LF 换行，改后保持不变；8 个文件的花括号都平衡。
- 没有跑生成器，没有开游戏，没有提交。
- 补丁脚本在 D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\p1b_work\。

### 一、做了什么

**1. 旧入口（01 §1.4）**
- `zz_hd_304_history_on_actions.txt` 与 `zz_hd_nbc_history_on_actions.txt`：
  - 删掉 `on_game_start_after_lobby` 列表。
  - `hd_304_history_start`、`hd_nbc_history_start` 保留定义，trigger 首行加 `always = no`。
  - `hd_304_pulse`、`hd_nbc_pulse` 的 trigger 不变；effect 换成转发壳 `hd_j16_bootstrap_effect = yes` 加一行日志，不再续排。写法照 p1-S 的 `hd_370_pulse`。
- 已核：`hd_(304|nbc|370)_pulse_started`、三个旧 `*_pulse_effect`、`on_action = hd_*_pulse` 在旧 on_action 文件之外没有任何读取方或调用方（core 里那处调用就是本次删掉的过渡桥）。

**2. 删 core 里的 370 过渡桥**
- 已从 `hd_j16_pulse_effect` 删除，原处只留一行注释。
- 删桥前逐项核对了去处：

| 旧内容 | 去处 |
|---|---|
| 洛阳出降与结局、东征（含再伐）、燕亡、慕容评归秦、寿春 | p1-A 的 `hd_j16_e3_370_effect` |
| 废立 | p1-A 的 `hd_j16_e4_370_effect` |
| 370 卒年表、结局卒年、袁真 | 卒年文件（本任务第 3 条） |

- 三个旧 `*_pulse_effect` 保留定义，不再被任何心跳调用。

**3. 卒年迁移**
- **手工段**：在 `zz_hd_j16_deaths_effects.txt` 末尾新增一段，首尾都清楚标出「1-B 手工迁入段」，效果名 `hd_j16_deaths_1b_manual_effect`，由 `hd_j16_deaths_effect` 末行调用。
  - 按十年分段，写法与样例段相同，首跳全段扫变量独立。
  - 共 57 行，日期照旧表，DATE10 由脚本算出。
  - 样例段已有的惠帝、刘渊、王浚 3 条没有重复写。
- **N/K 分类**（依 01 §6.1、05 §4.4、03 §7；06 §5.1 没有涉及这些人的更正）：
  - K 共 15 行：张方、司马颖、刘裕（齐王）、刘隆、刘恭、刘和、王弥、苟晞、怀帝、猗卢、刘乂、刘琨、拓跋珪、陈敏，其中刘和带前置、陈敏无凶手（见自拟 1、3）。
  - 其余为 N。
- **`hd_nbc_hist_death_effect`**：定义保留，改为转发到 `hd_j16_death_effect = { ID = $WHO$ DATE = $DATE$ DATE10 = $DATE$ }`。
- **X 类**（`zz_hd_370_history_effects.txt`）：
  - `hd_370_yuanzhen_death_effect` 与 `hd_370_outcome_deaths_effect` 仍是独立效果，人物改经 `hd_j16_resolve_effect` 解析，解析前先 `clear_saved_scope`。
  - 不再经旧 `hd_370_kill_effect`、`hd_370_die_effect`（它们取人用 `character:$WHO$`，定义保留），改用新增的三个本地效果：`hd_370_x_resolve_effect`、`hd_370_x_kill_effect`、`hd_370_x_die_effect`。
  - 玩家袁真改走 `hd_j16_death_effect`（DATE10 = 380.4.10）。
  - 由卒年文件调用：袁真那一行保持 `start_year = 370` 限制；结局卒年放在手工段 370 年代，不分开局（404 局由前标设 done）。前提不成立时只记 SKIP（D11）。

**4. `_active` 清理（01 §5）**
- 核对了所有走 `hd_nbc_start_war_effect` 的场次：
  - 分发表内 8 场由 CB 结算清除。
  - daling、luoyang、feishui 兜底在 p1-A 节点里已经自清，这里不重复。
  - 永嘉、京口用 `start_war`，不设 `_active`。
- p1-A 的 dongzheng、shouchun 没有清。e3_370 等节点文件归 p1-A，我不能写，所以在 core 新增 `hd_j16_active_cleanup_effect`，放在 pulse 末尾、各时代入口之后：
  - dongzheng、shouchun：对应 done 已设就清。东征再伐会删 done，开战时 `_active` 会重设，下次了结再清。
  - **另加 feili**（新发现，01 §5 没列）：司马奕拒绝逊位时的讨伐战，桓温（经解析）和天子都已不在该场次战争时清。
- 这三个变量没有任何读取方，面板读的是分发表内的场次。

**5. `hd_j16_mark_before_start_effect`**
- p1-A 的报告不在盘上。我按 p1-A 暂存里的注释，并把全部迁入节点的守卫变量与 01 §3.2 逐项对照，前标列表本身没有缺漏。
- 只补了 p1-A 注释交办的一处：346 旧档在切进新心跳之前，已由旧逻辑了结淝水，导致前秦瓦解标记 `hd_j16_qin_collapse` 漏设。
  - 在 mark 末尾单独成段，注明是「旧档补设，不是前标」。
  - 守卫是 `result_done`，加上 `lost` 或 `white` 已设，加上标记未设；命中时设 `hd_j16_qin_collapse`，并把 `_m` 设为 0。
  - 新档与 404 前标都不会命中。

**6. 冻结**：8 个文件中，除 core 和卒年文件外，6 个旧文件（三个 history_effects 和三个 history_on_actions）的首行都加了「【1-B 冻结】已由统一心跳接管……不再改（08 §1.4）」。

### 二、自拟与偏差
1. **4 行暂按 N。** 05 里这 4 人是 K，但凶手还没建档，写成 K 会出现不存在的 ID，而且会一直顺延（苻洪顺延会卡住苻健入关，那个节点读它的 done）。所以先照旧表的 N 写，行尾都注明：
   - 司马颙：凶手 `hd_j16_liang_chen`。
   - 司马腾：凶手 `hd_j16_ji_sang`。
   - 司马模：凶手 `hd_j16_zhao_ran`。
   - 苻洪：03 §7 要改为 K、日期 350.3.1、凶手 `hd_j16_ma_qiu`，并依赖 E3-Q05 节点。
2. **刘和带前置。** 新心跳里卒年先于节点执行，为保证先立储再杀，刘和用 `hd_j16_death_kill_pre_effect`，PRE 填 `hd_304_liu_cong_heir_done`。这是 done 而不是 fire 结果，偏离约定，但立储节点跳过时也会设它，不会白等。
3. **陈敏**：05 写 K、无凶手（部众倒戈），用 `hd_j16_death_die_effect`，死因 `death_execution`。
4. **05 未列的两人**：张辅（凶手韩稚无 ID）、刘乔（病卒），都按 N。
5. **死因键是自拟**，均在模板列出的原版键内：被斩、赐死、缢杀用 `death_execution`，弑、害、鸩、宴杀用 `death_murder`，苻坚照旧用 `death_murder_known`。
6. **转发壳的 DATE10 直接传 DATE**（宏里做不了日期加法），取不到人就当即设 done，与旧行为一致。
   - 影响面：22、89、531、617 四个剧本的卒年表也调用这个效果，转发后它们也改走 j16 机制。具体是：能取到 hbirth 指针；玩家待答期间不重复弹窗；强撑每人一次（D10，hd_nbc.0100 本来就共用）。
7. **旧档开局限制取消**。原 304 表只在 304 局跑，nbc 表分 346、404 两段，370 表只在 370 局；现在都不分开局，晚开局首跳全段扫时，已死的人当即设 done。
8. **X 类跨开局语义**：在 304、346 局里，如果什翼犍从未据有云中、苻坚从未据有长安，「已失」前提会直接成立，人照样死。这是按任务（不加开局限制）做的，留给 5-A 细化。
9. **与 08 的写入者冲突**，本次按任务说明执行：
   - 08 §1.1 写 core「1-S → 1-A，之后冻结」，本次由 1-B 写 core。
   - 08 §1.3 写卒年文件「≤ 5 条样例」，本次加了手工段。

### 三、需要汇总人处理的事项
1. **落盘顺序**：删桥依赖 p1-A 的节点，p1-B 必须与 p1-A 同批落盘，或者在它之后。本次闸门只叠加了 p1-B，没有和 p1-A 合并验证；p1-B 没有暂存任何 p1-A 的文件。
2. **交 2-D：**
   - 手工段 57 行加样例段 3 行，要并入 `docs/两晋十六国_卒年表.tsv`，之后生成器整文件覆盖。
   - 4 行暂 N（司马颙、司马腾、司马模、苻洪），在 2-C 建人、E3-Q05 写好后改回 K，苻洪日期同时改为 350.3.1。
   - 刘和的 PRE 用的是 done，请保留或改为节点 fire 结果。
   - 生成物必须照样输出两处 X 调用：袁真（限 370 局）和 `hd_370_outcome_deaths_effect`（不限开局）。
   - 桓温的权臣交接阻断前置钩子仍归 2-D 的特殊卒年文件。
   - 建议把拓跋绍 `tuoba_qinghe` 列入早出场名单：早于 404 的开局里他要到 410 年才出场，拓跋珪这条 K 会顺延约一年。
3. **交 5-A：** dongzheng、shouchun、feili 的 `_active` 清理可以挪进节点结局段，届时删掉 core 里的 `hd_j16_active_cleanup_effect`；X 类前提的跨开局细化也归 5-A（见自拟 8）。
4. 落盘后这 6 个旧文件冻结。

### 四、新增变量、效果与事件号
- **事件号**：无。**面板行**：无。
- **全局变量**：`hd_j16_dm300_swept`、`_dm310_`、`_dm340_`、`_dm350_`、`_dm370_`、`_dm380_`、`_dm400_`、`_dm410_swept`。另外在旧档补设里会写 `hd_j16_qin_collapse` 和 `hd_j16_qin_collapse_m`，这两个变量是 p1-A 新增的。
- **效果**：
  - core：`hd_j16_active_cleanup_effect`。
  - 卒年文件：`hd_j16_deaths_1b_manual_effect`。
  - `zz_hd_370_history_effects.txt`：`hd_370_x_resolve_effect`、`hd_370_x_kill_effect`、`hd_370_x_die_effect`。
- **scope**：`hd_j16_xyz_zhen`、`hd_j16_xyz_jin`、`hd_j16_xd_v`、`hd_j16_xd_k`、`hd_j16_ac_huan`。
- **日志**：`HD_J16 death_<ID> FIRE/SKIP …`、`e3_q70/e3_j80/e4_j10 FIRE active_cleared`、`e4_q51 FIRE oldsave_qin_collapse`、`boot FIRE hd_304_pulse_shell` / `hd_nbc_pulse_shell`。

### 五、闸门结果
命令照给定参数运行，结果在 D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p1-B_gate.txt。新增 error 3 条、warn 1 条，都可以保留：
- **error 3 条**（gvar_read_never_set）：`hd_nbc_dongzheng_active`、`hd_nbc_shouchun_active`、`hd_nbc_feili_active`。这是拼接名误报：它们由 `hd_nbc_start_war_effect` 以 `hd_nbc_$KIND$_active` 设置（TEMPLATE §5.14）。
- **warn 1 条**（gvar_set_never_read）：`hd_j16_qin_collapse_m`，由第 5 期 E4-W50 读取（p1-A 已有同样的 warn）。

# FIX
## p1-B 修正报告

7 条审查意见已全部处理：1 条 major 已修；minor 中 2 条改了代码、1 条改了报告内容、3 条只交接不改代码。改动全部在暂存区，mod 没动。两个暂存文件仍是 UTF-8 带 BOM、LF 换行，花括号平衡（deaths 文件 121/121，370 文件 572/572）。

### 逐条处理

**1.【major】结局卒年在 304、346 局会误杀 —— 已修，选方案 (a)**
- 在 `zz_hd_j16_deaths_effects.txt` 的 370 年代手工段，给 `hd_370_outcome_deaths_effect = yes` 外面包了一层 `if = { limit = { global_var:hd_j16_start_year = 370 } ... }`，写法与袁真一样。
- 这样执行范围就回到删桥前过渡桥的范围：只在 370 局执行；404 局本来就由开局前标记设 done；304、346 局不再执行。
- 同步改了三处注释：
  - deaths 文件第 69 行交 2-D 的说明，改为「X 类两行连同各自的 start_year = 370 开局限制照样调用」，防止 2-D 整文件覆盖时把限制丢掉。
  - 调用处说明。
  - 370 文件结局卒年块头注，原来写的「不分开局」已改。
- **交 5-A 清单（新增）**：给结局卒年补上「曾据有」前提后，再去掉这层开局限制。
  - 苻坚：加 `has_global_variable = hd_j16_qin_collapse`，或者看 `hd_nbc_feishui_lost` / `hd_nbc_feishui_white` 之一。
  - 什翼犍：要求他本人 is_landed 且是代王（拓跋王朝的独立统治者），或者导演对代的战争已发生、E4-T20 的标记已设。
  - 慕容暐：前提不是空真，不受影响。

**2.【minor】刘和的 PRE 用了 done —— 已修**
- 改成 `PRE = hd_j16_liu_cong_heir_result`，行尾注改为「前置取 E1-H40 的 fire 结果（08 §1.3：节点跳过视为前提不成立，D15 顺延到 DATE10 改按 N）」。
- **交 p1-A 或汇总人**：p1-A 中 E1-H40 的 already_ruler 分支（刘聪已经持有并州）只设 `_skip`，不设 `_result`。走这个分支时，刘和会顺延到 320.10.31，再按 N 类病逝，不会被刘聪所杀。要不要让这个分支同时设 `_result`，需要 p1-A 或汇总人拍板，p1-B 不能改 p1-A 的文件。
- 346、370、404 局里，刘和这一行在首跳全段扫时已经过了 DATE10，会直接改按 N 或设 done，不会误杀。

**3.【minor】刘裕、刘隆行尾注 —— 已修**
- 删掉自拟的「刘聪遣兵斩之」。两行行尾注都改成：「凶手照 05 §4.4.4 写刘聪【待核】：mod history 01_shiliuguozhu.txt 记刘和 xiongnu_liu_021，交 05 与 2-D 对照通鉴卷 87 核定」。
- KILLER 仍按 05 写 xiongnu_liu_023。如果以后核定凶手是刘和，这两行仍早于刘和本人的卒日 310.10.31，先后顺序不受影响。

**4.【minor】交 2-D 第 6 条「拓跋绍 410 年才出场」—— 原说法撤回，改为已核**
- 我自己 grep 核过：`hd_hb_s_tuoba_qinghe_effect` 在 `zz_hd_hbirth_generated_effects.txt` 的 `hd_hb_c394_effect` 桶里（第 340874 行，这个桶范围是 340836–340876）。也就是说拓跋绍 394 年出场，不需要列入早出场名单。拓跋珪这条 K 不会顺延，与 E5-T60 的窗口也不冲突。
- 交 2-D 清单里这一条改为「已核：394 出场，无需早出场」。

**5.【minor】_active 清理放在 core —— 维持现状，交 5-A**
- 交 5-A：把 dongzheng、shouchun、feili 三个 `_active` 的清理挪进各节点的结局段，然后删掉 core 里的 `hd_j16_active_cleanup_effect`。
- 挪的时候，feili 判断战争是否已结束，要改为看存下的攻守方或战争变量，不要再看 `title:h_china.holder`。
- 目前没有任何地方读这三个变量，所以无害。

**6.【minor】22、89、531、617 的卒年行为随转发壳改变 —— 代码不改，交汇总人**
- 请加进实测清单：「22、89、531、617 卒年表：AI 到日病逝；玩家病笃只弹一次；强撑一次」。

**7.【minor】旧档补设只在 bootstrap 执行一次 —— 不阻断，交 5-A**
- 写进 5-A（E4-W50）的交接清单：
  - 旧档里 `hd_j16_qin_collapse_m` 是从切换日（bootstrap 那天）开始算，不是从实际瓦解那天，月计数会偏晚。
  - (b)(c) 两种兜底仍需保留。
  - p1-S 落盘后、旧 nbc 心跳了结的淝水，这段补设不会再执行。p1-S 没有实玩过，影响可以忽略。

### 闸门结果

**只叠 p1-B**（`--overlay p1-B --compare baseline.json --only-changed`）：error 3、warn 1，与上一轮相同，没有新增问题。结果文件：D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p1-B_gate.txt
- 3 个 error 都是拼接名误报，保留：`hd_nbc_dongzheng_active`、`hd_nbc_shouchun_active`、`hd_nbc_feili_active` 报「只读不写」，实际由 `hd_nbc_start_war_effect` 用 `hd_nbc_$KIND$_active` 设置。
- 1 个 warn 是预期内：`hd_j16_qin_collapse_m` 报「只写不读」，要到第 5 期 E4-W50 才读。

**叠 p1-A + p1-B**：error 3、warn 24，与上轮审查结果相同。结果文件：D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p1-B_fix_gate_AB.txt
- `hd_j16_liu_cong_heir_result` 仍报「只写不读」。这是闸门的局限：它现在通过宏参 `PRE = hd_j16_liu_cong_heir_result` 传进去，再由 `has_global_variable = $PRE$` 读取，闸门看不到这种读取。属于误报，保留。

### 未解决项和落盘条件
- **刘和 / already_ruler 分支**：是否也设 `_result`，等 p1-A 或汇总人决定。
- **刘裕、刘隆的凶手**：等 05 与 2-D 对照通鉴卷 87 核定。
- **交 5-A 三项**：结局卒年补「曾据有」前提后放开开局限制；_active 清理挪进各节点结局段；旧档 qin_collapse_m 起算日。
- **落盘条件不变**：p1-B 删了 370 过渡桥并停掉了旧心跳，必须与 p1-A 同批落盘，或在 p1-A 之后落盘。
- 没跑生成器，没开游戏，没提交。