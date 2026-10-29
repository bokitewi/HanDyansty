## p1-A「其余旧节点迁入」任务报告

**暂存任务名**：p1-A
**暂存位置**：D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p1-A\files\
- 7 个文件，全部用 `stage edit` 登记；保持 UTF-8 带 BOM、LF。
- mod、core、旧 history 效果、旧 on_action、nbc 事件文件、yml 都没有动。没有新增事件号。

### 一、做了什么（各节点已按 08 §1.1 落位）

**e1_304**（入口按上游→下游排序）
| 节点 | 窗口 | 要点 |
|---|---|---|
| E1-J20 建邺 | 307.9.1–312.1.1 | — |
| E1-H20 石勒归汉 | 307.10.1–309.1.1 | 上游：大陵已开战或已 done |
| E1-H30 刘渊称帝 | 308.11.1–310.8.1 | — |
| E1-H40 刘聪立储 | 310.10.1–311.6.1 | 上游 H30；刘聪已持并州即直接了结，免得拖住 H50；刘和或刘聪已死即跳过 |
| E1-H50 永嘉 | 311.5.1–313.1.1 | 见下 |
| E1-W10 乱世锁 | — | 条件不变 |
| E1-W20 衣冠兜底 | 311.5.1–322.1.1，每年一次 | 日期判断放在最前，346 以后的开局首跳全段扫时不会误开 |

E1-H50 永嘉的具体写法：
- 上游 H40。AI 汉主直接开战，失败下一跳重试；玩家收 hd_304.0140。
- 仍直接对两郡 `start_war`，不走连通筛选（R5）。
- 战后照旧：汉主得洛阳且天子是 AI 时天子被俘，开衣冠南渡，并跑兜底（R5）。
- 新战争体是 `hd_j16_yongjia_war_effect`，hd_304.0140 选项 a 改调它。

**e3_346**：拍平了 nbc 的开局分支，五个节点：
- **E3-R10 冉闵**：加了「石氏持王国级以上头衔」。
- **E3-Q10 苻健**：按 01 加严，截止时降级（见自拟项）。
- **E3-M10 前燕南下**：窗口改为 350.2.1 起；上游写成「冉闵节点已 done，或石虎已死」；`dynasty:murong`。
- **E3-J30 北伐**：加了「天子是河内司马氏」。
- **E3-Q20 苻坚夺位**：上游 Q10。

**e3_370**
- 新增 `hd_j16_get_qin_ruler_effect`：长安之主，苻氏、独立，取不到再试苻坚 ID。
- 新增 `hd_j16_get_yan_ruler_effect`：用旧 S3 的回退方式，取不到慕容暐时取 e_youyan 持有者，并要求 `dynasty:murong`（R6）。
- 慕容筑出降：单独成节点，排在洛阳节点之前。洛阳结局仍由 p1-S 的 `hd_j16_luoyang_result_effect` 判，没有重复。
- **E3-Q70 东征**：R3 的三处都保留——
  - 先白和洛阳之战，加免停战惩罚旗，上党、阳阿、魏郡三郡入连通筛选；
  - 秦败后 180 天、一年内再伐一次；
  - 燕亡条件放宽。
  - 上游写成「洛阳之战已开打或已 done」，不能写成「洛阳 done」，因为东征本来就会白和还在打的洛阳之战。
- **E3-M90 燕亡**、**E3-M91 慕容评归秦**、**E3-J80 寿春**：桓温经解析取得。

**e4_370**
- **E4-J10 废立**：三人都经 `hd_j16_resolve_effect` 解析。
- **E4-Q50 淝水**：
  - 370 开局补上淝水；
  - 秦主按位置解析，存为 `hd_j16_feishui_qin`；
  - `is_at_war` 的收窄没改，留第 5 期。
- **E4-Q51 瓦解**：保留 R2 兜底；新节点的兜底段和结局段读 `hd_j16_feishui_qin`，不再写死 `character:lueyang_fu_020`。

**e5_395**（只做迁入，R7）
- J51、J52、J60 改成等待式。
- J52 删掉死条件 `hd_nbc_restore_wait`。
- J70、J80 共用一个宏节点。
- J90 玩家弹窗加了 60 天门槛 `hd_j16_song_asked`。

**旧执行体的处理**
- 旧执行体里写死 `character:ID`、又会在 304/346 局跑的，在新文件里另写了 scope 版。hd_370 事件的 11 处选项改调这些新版本：
  - `hd_j16_zhu_surrender`、`dongzheng_war`、`yan_fall`、`ping_flee`；
  - `shouchun_war`、`huanwen_join` / `joins` / `own`；
  - `feili_proceed`、`feili_yu`、`abdicate`、`refuse_abdication`。
- 新执行体开头都自己重新解析当事人，所以由旧过渡桥弹出的事件也能用。

### 二、自拟项与偏差

**自拟项**
1. **E3-Q10 的加严口径**（R4 原文没找到）：
   - 苻健有地，或其 top_liege 领内有关中五郡、弘农、上洛、新平、安定、北地、河东的县；
   - 京兆的 top_liege 是 shi_2、冉闵王朝 `hd_nbc_ran_dyn`，或公国级以下的割据者。
   - 截止（353.1.1）时基本条件成立、加严不成立：只给 AI 且有地的苻健京兆宣称和 1 万兵，设 `hd_j16_fujian_soft`，不立国。
2. **E3-M90 窗口从 369.12.1 起**：旧节点只在 370 局跑，统一心跳下要防 346 局早年误判。
3. **战争节点改为 AI 直接开战、失败重试，玩家照旧收事件**：yannan、beifa、feishui、nanyan、houqin，以及永嘉、东征、寿春。
4. **永嘉的 2 万事件兵改到开战成功后才给。**
5. **这些节点 AI 仍走事件**（与模板写的「AI 直接执行」不同）：J20、H20、H30、R10、Q10、Q20、J52、J60。原因是执行体依赖事件 root，AI 仍按 ai_chance 100 选史实项。
6. **J70、J80 没加 01 表里的上游**（J45 或 J52）。J45 还没实施，J52 不一定会设 done，现在加会卡住 404 局，违反 R7。上游留给 6-A。
7. **E4-Q51 先设了 `hd_j16_qin_collapse`**，只在秦败或白和那一支设。计数 `_collapse_m` 和 0161 排除入侵当事人归第 5 期。

**与设计文件的冲突**
- **J90 窗口**：01 表写 419.12.1（A6-F16）。我按任务说明「06 的改造归第 6 期」保留旧值 418.12.1；songwang 门、J84/J86/J88 前置也留给 6-A。
- **上游节点还不存在**：01 表的上游 E3-R05、E2-J11、E3-J20、E3-J45/J50、E4-W40 都还没实施，没有接；分别由 4-B 和 5-A 接上。

### 三、需汇总人处理的事项

**1. 1-B 必须保留的旧效果**（已在 mod 里 grep 过、确认仍被引用）
- `hd_304_lock_check_effect`：`zz_hd_history_events_rule_on_actions.txt` 规则关闭时的年度兜底在调。
- 304 事件在调：`hd_304_save_han_ruler_effect`、`hd_304_jianye_effect`、`hd_304_shile_join_effect`、`hd_304_emperor_effect`。
- `hd_304_change_era_effect`：531 在用。
- `hd_370_take_realm_effect`：新节点和 22 剧本在用。
- `hd_370_change_era_effect`：新节点和 e2_304 在用。
- `hd_370_yuan_surrender_effect`：0148 选项 b 在用。
- `hd_370_regency_effect`：在 startup 文件里。
- `hd_nbc_*` 工具：start_war、spawn_army、give_county、become_independent、swear_fealty、seize_realm、fujian_duchy、fuzhoushan、restore、song、vassal_war（89 剧本也在用）。
- `hd_nbc_check_fashu_effect`：p1-S 的 e2_346 直接在调。

**2. 过渡桥断开后可以删的旧效果**
- `hd_370_zhu_surrender`、`dongzheng_war`、`yan_fall`、`ping_flee`；
- `hd_370_shouchun_war`、`huanwen_*`；
- `hd_370_feili_proceed`、`feili_yu`、`abdicate`、`refuse_abdication`；
- `hd_304_yongjia_war_effect`；
- 各个 `*_check_*` 效果，以及 `hd_304_yiguan_fallback_effect`。

**3. nbc 事件文件里写死 ID，304/346/370 局会取不到人**（写入者 1-D→6-A，本期没改，请指定谁改）
- 0150（J30，第 399 行）：`vassal_war WHO=longkang_huan_017`。这是 346 节的节点，304 局里桓温由 hbirth 生成，必坏。
- 0210：多处 `suiyuli_liu_013`。
- 0220 / 0221：`longkang_huan_027`、`si_ma_de_zong`、`si_ma_de_wen`。
- 0240 / 0250：`vassal_war WHO=suiyuli_liu_013`。
- 执行体 `hd_nbc_fuzhoushan_effect`、`hd_nbc_restore_effect` 里同样写死了 ID。

**4. hd_370 事件 portrait 仍写死 ID**（交 5-A）
- 0110、0120：`wang_meng_3`；0130：`lueyang_fu_020`；0140、0160、0170：`longkang_huan_017`；0150：`si_ma_yu_2`。
- 304/346 局玩家收到这些事件时会报错，不影响逻辑。

**5. 前标核对（01 §3.2）**
- 旧变量名全部保留，`hd_j16_mark_before_start_effect` 已覆盖全部迁入节点，没有缺漏。
- 唯一缺口是本期新设的 `hd_j16_qin_collapse`：04 的 E4-W50 写明 404 开局要前标它，并把 `_m` 设为 120。请 1-B 加进 core，或明确留给 5-A。

**6. 告知 5-A**
- 04 §1 第 176 行要求改 nbc 文件 413–503 行的 `character:lueyang_fu_020`。新节点已经改读 `hd_j16_feishui_qin`，桥断后不用再改 nbc 文件。

**7. 告知 1-B / 2-D**
- j16 心跳先跑卒年、再跑节点。刘和卒于 310.10.31，H40 在 310.10.1 开窗。30 天一跳的话，[10.1, 10.30] 里必有一跳，所以不受影响。

### 四、双触发风险（1-B 切断旧入口之前）

- **370 局**：每一跳都是过渡桥先跑旧 S1–S5，同名变量先设上，新节点只接旧逻辑等待或失败的情形。不会双发，只可能同一跳里尝试两次宣战。
- **304、346、404 局**：旧心跳和 j16 心跳同一天起跳，先后不定，靠同名 done、started 去重。
  - 旧的一次性节点一进窗口就设 done，所以 1-B 之前新节点的等待式写法常会被旧逻辑盖住：304 局的 S1–S4、346 局不带加严的旧 `check_fujian`、旧 M10 从 351 年起。
  - 永嘉：旧路径给 AI 发的 0140 现在调新战争体；失败时清掉 started，交回节点重试，不会卡死。
- **玩家重复弹窗**：只有 hd_nbc.0260（宋代晋）可能在过渡期重复弹，因为旧逻辑每跳都发。其余节点都因同名变量先设，不会重复。

### 五、新增变量与事件号

**事件号**：无新增；沿用 hd_304、hd_nbc、hd_370 的旧事件。

**新增全局变量**
- 各节点的 `_skip`、`_wlog`：jianye、shile、emperor、liu_cong_heir、yongjia、ranmin、fujian、yannan、beifa、fujian_coup、zhu、dongzheng、yanfall、shouchun、feili、feishui、fuzhoushan、restore、luxun、nanyan、houqin、song。
- `hd_j16_liu_cong_heir_result`、`hd_j16_yongjia_att/_def`、`hd_j16_fujian_soft`；
- `hd_j16_dongzheng_qin/_yan`、`hd_j16_yanfall_qin`、`hd_j16_ping_returned_result`；
- `hd_j16_feishui_qin`、`hd_j16_qin_collapse`、`hd_j16_song_asked`（60 天）。

**fire 判据**（供 2-D 卒年表 PRE 列和 F-1 使用）
| 节点 | 判据 |
|---|---|
| J20 | `hd_hev_304_jianye` |
| H20 | `hd_hev_304_shile` |
| H30 | `hd_hev_304_emperor` |
| H40 | `hd_j16_liu_cong_heir_result` |
| H50 | `hd_304_yongjia_decided` / `hd_hev_304_yongjia` |
| R10 | `hd_hev_346_ranmin` |
| Q10 | `hd_hev_346_fujian`（降级的是 `hd_j16_fujian_soft`） |
| M10 | `hd_nbc_yannan_active` |
| J30 | `hd_nbc_beifa_active` |
| Q20 | `hd_hev_346_fujian_coup` |
| 筑出降 | `hd_370_zhu_surrendered` |
| Q70 | `hd_370_dongzheng_decided` |
| M90 | `hd_370_yan_fallen` |
| M91 | `hd_j16_ping_returned_result` |
| J80 | `hd_370_shouchun_decided` |
| J10 | `hd_370_feili_enthroned` |
| Q50 | `hd_nbc_feishui_active` |
| Q51 | `hd_nbc_feishui_result_done` 加结果旗 |
| J51 | `hd_nbc_fuzhoushan_west` |
| J52 | `hd_hev_404_restore` |
| J60 | `hd_hev_404_luxun` |
| J70 / J80 | `hd_nbc_nanyan_active` / `hd_nbc_houqin_active` |
| J90 | `hd_hev_404_song` |

**面板行**：没有新增 hev，全部沿用旧的 hd_hev_304_* / 346_* / 404_*。

### 六、闸门结果

- 命令：`gate.py --overlay p1-A --compare baseline.json --only-changed`。
- 结果：**error 0，warn 24**，全部是 `gvar_set_never_read`，与 p1-S 已接受的 11 条同类：
  - 22 条 `_skip`：模板标配，留给 F-1 面板和人工排查；
  - 2 条 result 类（`liu_cong_heir_result`、`ping_returned_result`）：给 2-D 的 PRE 列；
  - `hd_j16_fujian_soft`：降级标记；
  - `hd_j16_qin_collapse`：给 5-A 的 E4-W50 和入侵改造读。
  - 以上合计 26 个变量，闸门报 24 条，有 2 个变量没有被列出，原因未逐条核对。
- 报告：D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p1-A_gate.txt
- 未开游戏实测。

# FIX
# p1-A 修正报告

## 概况
- 7 条审查意见都已处理：
  - 第 2～5 条改了代码。
  - 第 1 条（major）按审查给的改法，只更正报告并交 5-A。
  - 第 6、7 条只写报告。
- 只改了暂存区的 5 个效果文件。两个旧事件文件这次没动。
- 所有改动都由脚本完成：先断言旧文本存在且唯一，再替换。脚本是 D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\p1a_fix2\fix.py。
- 改前的暂存副本备份在 D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\p1a_fix2\backup_files。
- 7 个文件都还是 UTF-8 带 BOM、LF，没有 CR。manifest 没变，base_sha256 也没变。
- 没有直接写 mod，没跑生成器，没开游戏，没提交。

## 逐条处理

### 1.【major】hd_370.0170 的 trigger 写死了 si_ma_yi_4：更正报告，交 5-A
原实施报告第三节第 4 条更正为：

> hd_370.0150 和 0160 里写死 ID 的只是 portrait，不影响逻辑。0170 不一样，它的 trigger 是 `character:si_ma_yi_4 ?= { has_title = title:h_china }`，这是逻辑问题。

- **影响范围**：只在 304 开局、司马昱是玩家时出现。346 和 370 局里司马奕在史料库中存在，不受影响。
- **触发机制**：304 局里司马奕只有 hbirth 指针，`character:si_ma_yi_4` 取不到人，trigger 恒为假，事件被丢弃。
- **后果**：
  - hd_370_feili_started 已经设上，节点不会重试。
  - hd_370_feili_enthroned 永远设不上。
  - 已查到两处下游会落空：面板行 common/scripted_guis/hd_hev_scripted_guis.txt:1447，以及 04 中桓温野望 hw_yihuo「行伊霍之事」的主目标。
- **为什么不在这里改**：
  - 08 §1.4 规定，1-A 对旧事件文件只能改文本和选项，所以这次没动 trigger。
  - 也没有在效果文件里拿 character:ID 去探测，那样违反 TEMPLATE §5-4。
- **写入者**：5-A。也可以由汇总人放宽 1-A 的范围后再改。
- **改法**：把 trigger 改成按位置写，例如 `title:h_china.holder ?= { NOT = { this = root } }`；或者在事件里调 hd_j16_feili_resolve_effect，再查 scope:hd_j16_fl_yi。

### 2.【minor】玩家不回复时节点没有截止：已修
H50 永嘉（e1_304）、Q70 东征、J80 寿春（e3_370）都加了截止分支。三处都只设 done 和 _skip，日志写 `SKIP player_no_reply`。

| 节点 | 截止条件 | 补充 |
|---|---|---|
| 永嘉 | started 已设、decided 未设，且日期 ≥ 313.4.1（截止日加 90 天） | 和 window_closed 一样，再调 hd_j16_yiguan_fallback_check_effect |
| 东征（首次出兵） | started 已设、decided 和 done 都未设、没有 retry_started，且日期 ≥ 371.9.1 | 设 done 和 _skip |
| 东征（再伐） | 同上，但 retry_started 已设、hd_370_dongzheng_retry_window（365 天）已过期 | 只设 done，不设 _skip，因为第一场已经打过 |
| 寿春 | started 已设、decided 和 done 都未设，且日期 ≥ 371.9.1 | 顺带兜住原有的另一种卡死：玩家选 b 交给桓温，桓温也开不出战 |

东征的再伐会删掉 done 和 decided、但保留 started，而且可能晚于 371.9.1 才发出。只看日期的话，再伐事件刚发出，下一跳就会被截掉，所以再伐另看窗口。

**新增：迟到回复的守卫（审查没提，是截止改法直接带出来的）。**
- 问题：截止已经设了 done，玩家这时才点 a，仍会开战、设 decided。但节点外层要求 NOT done，这场战争永远不会结算，_active 也不会清。
- 改法：四个执行体改成「外壳 + 正文」，外壳在 done 已设时只记一次 `SKIP player_late_reply`，不再开战。外壳名和原来一样，调用方不用改。

| 外壳（原名，调用方照旧） | 正文（新名） |
|---|---|
| hd_j16_yongjia_war_effect | hd_j16_yongjia_war_body_effect |
| hd_j16_dongzheng_war_effect | hd_j16_dongzheng_war_body_effect |
| hd_j16_shouchun_war_effect | hd_j16_shouchun_war_body_effect |
| hd_j16_huanwen_own_shouchun_effect | hd_j16_huanwen_own_shouchun_body_effect |

- 东征再伐是先删 done 再调执行体，不受守卫影响。
- AI 走的路径里 done 还没设，也不受影响。
- `player_no_reply` 和 `player_late_reply` 都不在 TEMPLATE §4 的原因清单里，请汇总人补进模板。

### 3.【minor】上游没有显式写出：已修（e5_395）
- **J70**：hd_j16_liuyu_campaign_effect 加了参数 UP，只用在就绪判断里，不挡截止跳过。J70 传 hd_nbc_restore_done，注释写明「J45 实施后改为 J45 或 J52」。
- **原自拟项 6 的理由不成立，更正**：J52 已经改成等待式，405.6.1 截止时一定会设 done，早于 J70 409.4.1 开窗，不会卡住 404 局。
- **J80（审查没提，顺手补上）**：按 01 表的上游传 UP = hd_nbc_nanyan_done。J70 最晚 413.1.1 一定会设 done，早于 J80 416.9.1 开窗，不会卡住。
- **全 mod 和全暂存区已核**：hd_j16_liuyu_campaign_effect 只有 J70、J80 两处调用，都传了 UP，不会留下原样的 `$UP$`。
- **J51**：就绪判断里加读 hd_j16_jingkou_done。请汇总人注意：
  - 加上之后 J51 实际上不会再触发。J50 只在截止跳过、当事人已死这两种情况下设 done 而不设 hd_nbc_fuzhoushan_done，而这两种情况 J51 自己也会以同样理由跳过。J50 开战时又会预设 fuzhoushan_done。
  - 所以 J51 只剩形式上的兜底。404 局不受影响。
  - 请汇总人决定：接受这个结果，还是改 J51 的上游语义。
- **J90**：就绪判断里加读 hd_nbc_houqin_done（01 表上游 E5-J80）。
  - houqin 最晚 419.1.1 设 done，所以受禅最多推迟一个月，比 418.12.1 晚一个月左右。
  - 08 §10 R7 已经把「各前置」列为允许的改动。
  - J84、J86、J88 照旧交 6-A。

### 4.【minor】判断已死时还读卒年 done 变量：已修（e3_346）
- R10 冉闵、Q10 苻健两处，共 3 处 `OR = { hd_j16_dead_trigger ... has_global_variable = hd_nbc_death_*_done }`：连同 OR 外壳一起删掉，只留 hd_j16_dead_trigger。
- M10 前燕南下：只删卒年那一行，保留 `hd_nbc_ranmin_done`。
- 文件头注释改为「只用 hd_j16_dead_trigger，不读卒年 done」。
- 文件里已经没有 `hd_nbc_death_` 的引用。

### 5.【minor】Q51 只设了 hd_j16_qin_collapse：已修，过渡期部分移交（e4_370）
- 结局段在 `set_global_variable = hd_j16_qin_collapse` 后面紧跟着加了 `set_global_variable = { name = hd_j16_qin_collapse_m value = 0 }`，对应 04 E4-Q51 ①。累加由 5-A 的 E4-W50 负责。
- **未在本期处理**：346 局过渡期，旧 nbc 淝水可能先设 result_done 并发出 0161，这时 Q51 的结局段被跳过，标记会漏设。
  - 交 1-B：切断旧 nbc 淝水入口时一并处理；或者由 E4-W50 的 (b)(c) 补设。
  - 已写进节点头注释。
  - 没有在 Q51 里自己补设，原因是和 404 开局「collapse 预设、计数直接设 120」的写入顺序可能冲突。

### 6.【minor】nbc 事件写死人物 ID：只写报告，交 6-A
原报告第三节第 3 条补充后果如下：

- hd_nbc.0210 的 trigger 要求 `character:suiyuli_liu_013 ?= {...}`，在非 404 局恒为假。
- J50 或 J51 在发事件前已经设了 hd_nbc_fuzhoushan_done，所以 hd_nbc_fuzhoushan_west 永远设不上，J52 到期跳过。
- 结果：非 404 局整条 H 线实际上失效。
- 0150 的玩家北伐，以及 0220、0221、0240、0250 的 WHO=，在非 404 局里同样不可用。
- 这不是 R7 退化，404 局不受影响。

建议在 07 实施记录里注明这句原文：

> 非 404 局（304、346、370）的 H 线（E5-J51～J90）与 E3-J30 的 hd_nbc.0150 玩家北伐暂时不可用，原因是 nbc 事件和 hd_nbc_fuzhoushan_effect、hd_nbc_restore_effect 写死人物 ID；待 6-A 改为按位置解析或经 hd_j16_resolve_effect 解析。

写入者：events/zz_hd_nbc_events.txt 按 08 §1.4 由 1-D 交给 6-A，请汇总人在 6-A 的任务里点名。

### 7.【minor】和 R7 字面的张力：代码不改，请汇总人确认
- 原自拟项 3 补注与 08 §10 R7 的关系：前置部分（本次新加的 J70、J80、J90 上游）在 R7「除 06 写明的改动（…各前置）」的范围内。
- 真正需要确认的只有两项：
  - J51、J52、J60 改成等待到截止日；
  - J70、J80、M10、J30、Q50 的 AI 改为直接宣战、失败下一跳重试。

  这两项在 404 局里会让开战成功率和触发时点与旧行为（发一次事件，开不出就作罢）不同。
- 请汇总人确认 R7 的「条件不变」是否包括这两项，并记入 07。

## 未解决项（需汇总人指派或决定）
1. 0170 的 trigger：交 5-A，或放宽 1-A 的范围。
2. nbc 事件写死 ID，非 404 局 H 线失效：交 6-A，并在 07 里注明。
3. 346 局过渡期 hd_j16_qin_collapse 可能漏设：交 1-B，或由 W50 兜底。
4. J51 加了上游后实际上不再触发：接受，还是改语义。
5. R7 是否允许「等待式」和「失败重试」。
6. TEMPLATE §4 是否补上 `player_no_reply`、`player_late_reply` 两个日志原因。

## 闸门复跑
- 命令：`gate.py --overlay p1-A --compare baseline.json --only-changed`
- 结果：error 0，warn 25，全部是 gvar_set_never_read。
- 比上次的 24 条只多了 `hd_j16_qin_collapse_m`（e4_370:405）。它是共用接口变量，由 5-A 的 E4-W50 读取，按同类保留。其余 24 条和上次一样，审查已认可保留。
- `has_global_variable = $UP$` 这类带参数的读取闸门看不到。它读的 hd_nbc_restore_done、hd_nbc_nanyan_done 在别处都有写入，没有产生新的 warn。
- 新增的四个 *_body_effect 都没有报未定义。
- 报告：D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p1-A_gate.txt

## 文件
本次改了以下 5 个暂存效果文件：
- zz_hd_j16_e1_304_effects.txt
- zz_hd_j16_e3_346_effects.txt
- zz_hd_j16_e3_370_effects.txt
- zz_hd_j16_e4_370_effects.txt
- zz_hd_j16_e5_395_effects.txt

两个暂存事件文件 zz_hd_304_events.txt、zz_hd_370_events.txt 这次没改。绝对路径见 files。