# p4-A 最终报告（修正后合并版）

#  p4-A 前秦导演、边境 CB：修正报告（第 4 期第一轮）

审查意见共 7 条（主要 1 条，次要 6 条），全部处理完，只改了暂存区。闸门复跑结果与上轮相同：相对基线新增 error 8、warn 10，都能解释。

## 〇、审查意见逐条处理

### 1.【major】S3、S6 用运行时法理取 k_uuii_*（已修，按方案②）
- **新宏**：在 dir_effects 里新增 `hd_j16_dir_dr = { R = <区域> }`。它用 `every_county_in_region` 遍历汉代静态区域 `uuii_han_<州>_region` 的每个县，取县的 `duchy` 去重后加进目标表。
  - 280.1.1 只改郡挂在哪个州，郡下的县不动，所以县 → duchy 得到的就是汉代原郡。
  - 旧宏 `hd_j16_dir_dk` 已删除，grep 确认没有残留引用。
- **S3**：改为取静态冀州、幽州、青州三个区域（冀州 21 郡 135 县，幽州 14 郡 90 县，青州 12 郡 82 县），已用脚本按 01_landed_titles 核过。
  - 原先漏掉的魏郡 d_weijun、朝歌 d_weijun_sili、阳平 d_yangping_yanzhou 现在都在冀州区域内。
  - 平州 8 郡本来就在幽州区域内，原有的逐郡列出保留，作去重兜底。
  - d_henan 等 7 郡照旧逐郡列出。
- **S6**：改为取静态凉州区域（18 郡 86 县，正是 03 写的「86 县」），西平 d_xiping、洮西 d_taoxi1 已纳入，陇西、金城仍逐郡列出作兜底。
  - 另外新增小宏 `hd_j16_dir_dx`，用来把 S2 的六郡从 S6 目标里去掉（见第三节第 8 条）。去掉后 S6 目标为 62 县。
  - 原因：check 的控制率是「秦一系持有的县 ÷ 全部目标县 ≥ 70%」。S2 六郡共 24 县，S2 阶段已经收下；留在分母里，判完成时前凉最多还能剩约 25 县，去掉后只能剩约 18 县。
  - 实施报告里「西平按 03 原表不纳入」一句作废。
- **370 开局前凉实际还挂着的 4 郡不列为 S6 目标**：
  - d_longyou 在静态里属 k_tuyuhun；
  - d_puchang、d_kara_khoja、d_loulan 属西域，不在汉凉州范围内，也不在 01_landed_titles 的汉凉州下。
  - 这 4 郡不在控制率的分母里，所以不影响判定。前凉亡后它们归谁，由 E4-Q30 善后或 AI 自行处理。

### 2.【minor】边境 CB 不调用 hd_nbc_war_result_kind_effect（不改代码，需汇总人确认）
- 偏差保留，理由见第三节第 1 条，已写入第五节第 3、6 条。
- 交接要求：4-C、6-A 的边境战节点在结局时必须自己 remove `hd_nbc_<KIND>_active`，并按 `global_var:hd_j16_border_<KIND>_target` 的 top_liege 自判胜负。

### 3.【minor】S4 的 node_done 可能误亮「仇池平定」（已修）
- 判完成的条件现在是三者同时成立：
  - `hd_j16_qiuchi_done` 已设；
  - 仇池闸门已开；
  - `title:d_wudou.title_capital_county.holder ?= { top_liege = scope:hd_j16_dir_actor }`，与 04 E4-Q10 的善后条件相同。武都授给杨统、杨统作秦封臣时，这一条同样成立。
- 闸门已开但武都没有归秦（例如善后窗口 374.1.1 超时跳过）时，只设 `s4_skip` 并进入下一阶段，日志为 `SKIP node_done_not_taken`，不亮面板。
- 闸门没开时仍记 `SKIP voided`。

### 4.【minor】border 宣战工具没有清 `scope:hd_nbc_war_$KIND$`（已修）
- 在 `hd_j16_border_start_war_effect` 开头加了一行：`hd_j16_dir_clear_scope_effect = { S = hd_nbc_war_$KIND$ }`。

### 5.【minor】东征失败、hd_370_yanfall_done 因超时被设上（不改代码，已写入偏差）
- 03 原文就写的是「到 M90 done（或 372.1.1）暂停」，所以照字面读 done。
- 结果：东征失败、M90 在 372.1.1 超时跳过后，暂停解除，S3 门打开，「不打慕容」的排除也随之解除。导演会用 S3 去打仍然完整的前燕，作为兜底。此时节点已经停了，不会两边同时推进。见第三节第 14 条。

### 6.【minor】停止续期后，瓦解时没有地方摘旗标（已修，需 5-A 加一行调用）
- dir_effects 新增 `hd_j16_dir_release_member_effect`（任意 scope 可用）：如果 `global_var:hd_j16_dir_qin_actor` 在世且带 `hd_j16_dir_member`，就摘掉旗标，日志为 `dir_s0 FIRE member_released`。
- 需要 5-A 在设 `hd_j16_qin_collapse` 的地方紧接着加一行调用，见第五节第 2 条。这一行加上之前，旗标最多残留 730 天后自行到期，不会卡死。

### 7.【minor】策略触发器多加了一行注释（已修）
- 注释已并为行尾注释：`has_character_flag = hd_j16_dir_member # 两晋十六国 j16 前秦导演托管的秦主（hd_j16_dir，03 §1.3）`。
- 与 mod 原文件 diff，只多这一行；CRLF 共 145 处，等于 LF 总数，BOM 保留。

### 仍未解决
没有需要我这边继续改的项。以下几项只能由别人处理：
- 第 2 条的偏差需要汇总人确认；
- 第 6 条需要 5-A 加调用行；
- 首测项需要实际进游戏测（第五节第 5 条）。

## 一、暂存任务名与文件清单

暂存任务名：**p4-A**。暂存区：D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p4-A\files\

新建 8 个文件，均为 UTF-8 带 BOM、LF：
- **common/scripted_effects/zz_hd_j16_dir_effects.txt**：
  - E3-W30 `hd_j16_dir_w30_effect`；
  - bootstrap、pulse、stop、tick、build、transition；
  - check、collect、declare；
  - 宏 `hd_j16_dir_dr`、`hd_j16_dir_dd`、`hd_j16_dir_dx`，以及阶段分派小工具；
  - `hd_j16_dir_release_member_effect`；
  - 边境宣战工具 `hd_j16_border_start_war_effect`、`hd_j16_border_truce_effect`。
- **common/scripted_effects/zz_hd_j16_dir_data_effects.txt**：`hd_j16_dir_data_effect = { KEY }`、`hd_j16_dir_data_qin_effect`，即 S1–S7 阶段表（S5 空号）。
- **common/scripted_triggers/zz_hd_j16_dir_triggers.txt**：actor_ready、war_slot、qin_under_jin_attack、target_ok、county_front、duchy_has_front、stop、paused、stage_has、stage_war_ongoing、border_county_ok。
- **common/on_action/zz_hd_j16_dir_on_actions.txt**：只有 hd_j16_dir_bootstrap、hd_j16_dir_pulse 两个，61 天自续期。
- **common/casus_belli_types/zz_hd_j16_border_cb.txt**：hd_j16_border_cb。
- **events/zz_hd_j16_dir_events.txt**：namespace = hd_j16，只有 hd_j16.1420。
- **localization/simp_chinese/zz_hd_j16_dir_l_simp_chinese.yml** 与 **localization/english/zz_hd_j16_dir_l_english.yml**：各 20 键，中英一一对应。

改动 2 个共用文件：
- **common/scripted_effects/zz_hd_rise_effects.txt**（BOM、LF）：在掷骰开战的 limit 里，紧跟 `NOT = { game_start_date = 190.1.1 }` 之后加 `NOT = { has_character_flag = hd_j16_dir_member }`。只多这一行。
- **common/scripted_triggers/hd_strategic_ai_triggers.txt**（BOM、CRLF）：在 `hd_strat_historical_managed_trigger` 的 OR 里、`has_character_flag = hd184r_director_member` 之后加一行，带行尾注释。只多这一行。

以下文件本轮都没有写：e2_346、e3_346、346 的事件、loc、触发器、修正，startup_346、startup_404，history/titles/*，以及 190 导演的任何文件。

## 二、实现要点（有效部分，未变）
1. **E3-W30 启动节点**（日志前缀 e3_w30）：
   - 自保护：开局年 ≥ 404 时直接设 done。
   - 窗口：351.1.1 到 382.6.1。
   - 启动条件：规则已开、`hd_nbc_fujian_done` 已设、按位置能解析出秦主。三者首次同时满足时，在 title:h_china 上排 `hd_j16_dir_bootstrap`。
2. **状态与每跳处理**：
   - 状态全部放在全局变量里。
   - 秦主每跳按位置重新解析：长安 c_uuii_p_867 的 top_liege，且为苻氏（dynasty:fu_1）、独立。
   - 每跳开头 clear_saved_scope。
   - 宣战前复核（照 10-23 的写法）。
3. **名额**：同时进行的战争少于 3 场，节点战争也计入；每跳最多新开 1 场。
4. **暂停、不开新战与停止续期**：
   - 369.12.1 起到 `hd_370_yanfall_done`（或 372.1.1）整段暂停；
   - 秦主正被晋攻时，本跳不开新战；
   - 382.6.1 起不再开新战；
   - 以下任一成立即停止续期：383.1.1、淝水 done、collapse、dir_qin_off；
   - 370 开局把 stage 直接置为 3。
5. **宣战流程**：先走 hd_tb_arm，再经 hd_wct 连通筛选，用 hd_dc_tunbing_cb（historical）开战。开战后在战争上设 `hd_j16_dir_war = flag:<阶段名>`，阶段名为 guanzhong、longyou、yancan、qiuchi、liang、dai 之一。
6. **阶段收尾**：完成时设 s<N>_done 和对应的 hev 面板变量；作废时设 s<N>_skip；阶段全部走完设 qin_done。
7. **边境 CB**：
   - 参数：wargoal 0.8，守方战斗分上限 50、占领分上限 150；
   - 胜：只转目标县；
   - 三种结局都订 3 年双向停战。
8. **旗标 `hd_j16_dir_member`**：
   - 只给在世的 AI 秦主，每跳先 remove 再加 75 天；
   - 停止续期时：已瓦解或淝水已 done 就直接摘掉，否则改为 730 天；
   - 瓦解如果发生在停止续期之后，由 5-A 调 release 摘掉。
9. **on_action**：本轮只新增 2 个，全 mod 共 6717 个，低于 1 万上限。

## 三、自拟与偏差（合并更新）
1. **边境 CB 三处结局都不调 `hd_nbc_war_result_kind_effect`**，依据是 00 §6「新 KIND 由节点自判、不进分发表」。
   - 那个效果只接受字面写死的 KIND。本 CB 要供 maqiu、maqiu2、longli、chaibi 等多个场次共用，调它就得在 CB 里写一张场次清单。
   - 现在三处结局只做通用结算，外加 debug_log。
   - **需汇总人确认。**
2. **新增宣战工具 `hd_j16_border_start_war_effect`，不走 hd_wct**：wct 在不连通时会扩大到守方所有接壤郡，与「只争一县」不符。
   - 选县规则：县 → 同郡内的县 → 都不行就不宣战。
   - 开头会清 `scope:hd_nbc_war_$KIND$`（本轮新增）。
3. **collect 的写法**：直接从目标表里筛「有前线县」的郡，不先扫全境前线。结果与 190 相同，开销更小。
4. **空转计数**：本阶段的导演战争还在打时，不计空转。
5. **旗标时长**：每跳 75 天，停止续期时改为 730 天。另外新增 release 效果，供 collapse 时摘旗（本轮新增）。
6. **S3「gated 满 1 年」的计时起点**：从仇池闸门开启后才开始计，满 6 跳跳过 S3，日志 `SKIP gated_1y`。
7. **作废与完成**：
   - S4：done、开闸、武都归秦三者同时成立才判完成；开闸但武都未归秦 → skip（`node_done_not_taken`，本轮新增）；没开闸 → skip（voided）。
   - S6、S7：节点 done 而闸门未开 → 作废。
8. **阶段表取郡方式（本轮重写）**：
   - S3、S6 用汉代静态区域 `uuii_han_<州>_region` 取郡（宏 hd_j16_dir_dr），不用运行时法理（报错清单「汉代州归属」一条）。
   - S3 因此补进了魏郡、朝歌、阳平。平州 8 郡与 d_henan 等 7 郡仍逐郡列出。
   - S6 从 86 县里去掉 S2 六郡（天水、南安、广魏、陇山、陇东、襄武，共 24 县），剩 62 县，免得 70% 控制率被已收的县撑松；03 写的是「整州 86 县」，这里有偏差。
   - S6 含西平、洮西、陇西、金城。
   - d_longyou、d_puchang、d_kara_khoja、d_loulan 不作目标（理由见第〇节第 1 条）。
9. **W30 不要求秦主是 AI**：秦主是玩家时导演只空转，不托管。
10. **W30 的实际启动窗口**：W30 只在 E3 段里被调用，所以实际能启动的时间是 351 到 374 年。
11. **边境 CB 胜利时，攻方加小威望**（03 没有写这一条）。
12. **日志格式按 08 §5 写**：`HD_J16 dir_s<N> FIRE|WAIT|SKIP <原因>`。
13. **tunbing 胜利时会调 `hd_historical_world_war_victory_effect`**：该效果在 j16 开局里不起作用，已核实，可以接受。
14. **yanfall 兜底（本轮写明）**：`hd_370_yanfall_done` 照字面当作 done 读，这个变量在 M90 超时跳过时也会被设上。东征失败、到 372.1.1 后，暂停解除，S3 门打开，「不打慕容」的排除也解除，导演 S3 会去打仍然完整的前燕作为兜底；这时 M90 节点已停，不会两边同时推进。如果不想要这个兜底，可以把 S3 门和慕容排除改为读 `hd_370_yan_fallen`。
15. **策略触发器那一行的注释改成了行尾注释**（本轮修改）。

## 四、本期面板行清单（交 F-1，只列不写）
| hev 变量 | 含义 | 适用开局 |
|---|---|---|
| hd_hev_j16_dir_qin_start | 前秦导演启动（秦军出关） | le370 |
| hd_hev_j16_dir_qin_s1 | 关中收尾完成 | le346 |
| hd_hev_j16_dir_qin_s2 | 陇右、秦州收复 | le346 |
| hd_hev_j16_dir_qin_s3 | 燕地余烬收尽 | le370 |
| hd_hev_j16_dir_qin_s4 | 仇池平定（必须武都归秦才亮） | le370 |
| hd_hev_j16_dir_qin_s6 | 前凉平定 | le370 |
| hd_hev_j16_dir_qin_s7 | 代地平定 | le370 |
| hd_hev_j16_dir_qin_done | 导演阶段表走完 | le370 |

## 五、需要汇总人处理的事项
1. **交 4-B**：在 `common/scripted_effects/zz_hd_j16_e3_346_effects.txt` 的 `hd_j16_e3_346_effect` 里，紧接 `hd_j16_node_fujian_effect = yes     # E3-Q10 苻健入关` 之后加一行：
   `	hd_j16_dir_w30_effect = yes     # E3-W30 前秦导演启动`
2. **交 5-A**：
   - 设以下 8 个变量（导演只读不写）：
     - 闸门 `hd_j16_dir_qin_gate_qiuchi`、`hd_j16_dir_qin_gate_liang`、`hd_j16_dir_qin_gate_dai`；
     - 下线变量 `hd_j16_dir_qin_off`；
     - 节点 done：`hd_j16_qiuchi_done`、`hd_j16_liang_done`、`hd_j16_weichen_done`、`hd_j16_dai_done`。称藩或节点跳过时也要设 done。
   - **新增一项**：在设 `hd_j16_qin_collapse` 的地方紧接着加一行 `hd_j16_dir_release_member_effect = yes`。
   - 找导演战争的写法：秦主作攻方，`any_character_war = { var:hd_j16_dir_war ?= flag:qiuchi }`。
   - E4-W40 写在 E4 段里。
   - 导演读 `hd_370_yanfall_done` 作为前燕门。
3. **交 4-C（E2-L90/L91、E3-L08 等）、6-A（柴壁 E5-T50）**：
   - 调用：`hd_j16_border_start_war_effect = { ATTACKER = scope:x DEFENDER = scope:y TARGET = title:<县或郡> KIND = <场次> }`。
   - 成功判据：`exists = scope:hd_nbc_war_<KIND>`。
   - **结局时必须**：在攻守双方都已没有 `var:hd_nbc_war_kind ?= flag:<KIND>` 的战争后，按 `global_var:hd_j16_border_<KIND>_target` 的 top_liege 自判胜负，并自行 remove `hd_nbc_<KIND>_active`。
   - 工具没有「封臣宣战失败就改由宗主宣战」的回退。需要时由节点改用宗主再调一次。
   - 不要用 `hd_nbc_start_war_effect` 开边境战。
4. **R4 / D24**：不需要 hd_court 豁免，`hd_court_on_actions.txt` 未改。
5. **首测项**：
   - 脚本 `start_war` 能否绕过边境 CB 的 `valid_to_start = { always = no }`；
   - `add_character_flag` 带 days 时先 remove 再加，时长是否正确；
   - `is_defender` 与 `any_war_attacker` 的组合写法；
   - 1420 的标题和描述是否按阶段切换；
   - `add_truce_both_ways` 同时写 years、war、result 是否正常；
   - **新增**：`every_county_in_region` 遍历静态区域再取 `duchy`，S3、S6 实际取到的郡数（日志里没有直接输出，可以看导演宣战的目标郡）；
   - 370 局：首跳启动 → stage 3 → 暂停到燕亡；
   - 346 局：约 351 年启动，S1 → S2 → S3 被门挡住。
6. **汇总人确认**：边境 CB 不调 result_kind（第三节第 1 条），以及 S6 去掉 S2 六郡、与 03「86 县」字面不同（第三节第 8 条）。

## 六、新增事件号与变量名
- **事件**：只用了 hd_j16.1420（前秦兴兵天下通报），1421–1429 未占用。
- **本地化键**：
  - 事件：`hd_j16.1420.t`、`.desc`、`.t_s1/2/3/4/6/7`、`.desc_s1/2/3/4/6/7`；
  - CB：`hd_j16_border_cb`、`hd_j16_border_cb_desc`、`HD_J16_BORDER_WAR_NAME`、`hd_j16_border_victory_desc`、`hd_j16_border_white_peace_desc`、`hd_j16_border_defeat_desc`。
- **脚本效果**：
  - 本轮新增 `hd_j16_dir_dr`、`hd_j16_dir_dx`、`hd_j16_dir_release_member_effect`；
  - 本轮删除 `hd_j16_dir_dk`；
  - 其余见第一节。
- **全局变量**：
  - W30：`hd_j16_dir_w30_done`、`_result`、`_skip`、`_wlog`；
  - 运行状态：`hd_j16_dir_qin_active`、`_stopped`、`_done`、`_stage`、`_idle`、`_gated_n`、`_actor`；
  - 其他：`hd_j16_dir_gated`、`hd_j16_dir_rebuild`、`hd_j16_dir_pause_wlog`、`hd_j16_dir_noactor_wlog`；
  - 临时（check 结束即删）：`hd_j16_dir_tot`、`_own`、`_need`；
  - 各阶段：`hd_j16_dir_qin_s<N>_done`、`_skip`、`_noticed`，等待日志 `_gated_wlog`、`_idle_wlog`、`_late_wlog`、`_jin_wlog`、`_fail_wlog`、`_stale_wlog`、`_notready_wlog`；
  - 面板：`hd_hev_j16_dir_qin_start`、`_s<N>`、`_done`；
  - 边境战：`hd_j16_border_<KIND>_target`、`hd_nbc_<KIND>_active`；
  - 列表：`hd_j16_dir_qin_targets`、`hd_j16_dir_qin_cand`。
- **新增日志原因**：`node_done_not_taken`、`member_released`。
- **人物旗标**：`hd_j16_dir_member`（限时）、`hd_j16_dir_restore_sworn_peace`（1 天）。
- **战争变量**：`hd_j16_dir_war`、`hd_nbc_war_kind`。
- **保存作用域**：
  - 导演：`hd_j16_dir_actor`、`_tgt`、`_def`、`_newwar`；
  - W30：`hd_j16_w30_qin`；
  - 边境：`hd_j16_bd_me`、`_att`、`_def`、`_tgt`、`hd_j16_border_def_top`；
  - 数值：`hd_j16_dir_news_stage`。
- **on_action**：`hd_j16_dir_bootstrap`、`hd_j16_dir_pulse`。

## 七、闸门结果
修正后复跑：`gate.py --overlay p4-A --compare baseline.json --only-changed`，输出在 D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p4-A_gate.txt。

结果：overlay 10 个文件，相对基线新增 error 8、warn 10，已解决 0，与修正前相同，没有新的类别。
- **8 条 error**（gvar_read_never_set）：都是第五节第 2 条里等 5-A 设的变量。
- **10 条 warn**（gvar_set_never_read）：8 个 hev 面板变量由 F-1 读；另外是 w30 的 `_result`、`_skip` 两个。

格式核对：修改过的 dir_effects、data_effects 括号配平，BOM 加 LF；strategic 文件 BOM 加 CRLF（145 对 145）；rise 文件 BOM 加 LF。两个共用文件与 mod 原文件 diff，各只多一行。