# p5-C 最终报告（修正后合并版）

# p5-C「历史入侵统一改造」修正报告

## 〇、审查意见逐条处理

| # | 级别 | 处理 | 结果 |
|---|---|---|---|
| 1 | major 王冠保护依赖 hd_hi_key，404 并州保护不到 | 已修。**没有用审查者给的 (a)(b) 方案**：那两条会把苻坚（独立帝级）持有的王冠全部保护起来，秦况各家就再也篡夺不了前秦的王冠，审查者自己预期的「西燕从苻坚手里夺雍州」也会落空。<br>改用「首领标记」：<br>- 新效果 `hd_hi_j16_mark_leaders_effect` 只在 j16 下执行，给在世的 11 名 383–421 有王冠首领设人物变量 `hd_hi_j16_leader`。<br>- 其中拓跋珪和凉州四家（乞伏、吕、秃发、沮渠）另给王朝设 `hd_hi_j16_leader_dyn`。王朝变量在首领死后仍在，所以拓跋嗣继位后并州照样受保护。<br>- 慕容、姚、赫连、柔然只设人物变量，避免整族受保护范围过宽。赫连另有一个原因：勃勃 413 年以前的王朝还是匈奴刘氏 liu_2。<br>- 新判定 `hd_hi_j16_is_leader_trigger`：有 hd_hi_key、有 hd_hi_j16_leader、或王朝有 hd_hi_j16_leader_dyn，任一成立即是。<br>- `hd_j16_hi_crown_protected_trigger` 改为：持有者（≠ 本人）或其 top_liege（≠ 本人）满足 is_leader 即受保护。<br>- 删去 root.liege、root.top_liege 两支死代码。<br>- 标记有两个调用点：新年度 on_action `hd_hi_yearly_j16_mark`，以及 `hd_hi_crown_effect` 开头。需要年度标记的理由：首领可能在取冠前就已死去（拓跋珪 409 年），等到取冠时再标就晚了。 | 404 局并州（拓跋遵，上级为拓跋珪或拓跋嗣）受保护，已列入实测项 |
| 2 | major 404 局 shelun_3 闸门永远不开 | 已修，用审查者的方案 (2)：`hd_j16_hi_next_stage_closed_trigger` 里的 shelun_3 一支加了一条：`hd_j16_start_year >= 404` 时视为已开。 | 6-B 不需要再预设这个闸门。另提一条通则，见第五节 |
| 3 | minor 名单标记不看规则和 done | 已修：`hd_hi_j16_reserve_one_effect` 增加 KEY 参数，只在 `hd_hi_<KEY>_on` 开着、且没有 `hd_hi_done_<KEY>` 时才解析并标记。慕容泓、慕容冲都挂在 murongchong 下。 | — |
| 4 | minor tande ID 已失效 | 已修：年度块 `hd_hi_yearly_tande` 回退为逐字原文（已用 cmp 比对，与 mod 现文件一致）。删掉了 `hd_hi_try_start_tande_effect`，原位置改成一句注释。报告里「生成器副作用」那一段也已删除。 | ID 是改指 `korean_go_goguryeo_13` 还是作废，交汇总人或 2-A 决定 |
| 5 | minor 0200.d 不是玩家专用 | 维持现状。事件文件头的注释已改写为「与设计有出入，未改，当前无触发者」。报告第三节也已改写，并在交 6-A 部分写明调用顺序。 | 偏离设计，当前没有触发者 |
| 6 | minor wangmeng_heeded 的七折在主路径上不生效 | 只在报告里说明，见第三节第 17 条。 | 要不要另加实际效果，交汇总人决定 |
| 7 | minor sunen 缺孙泰前提 | 已修：`hd_hi_try_start_sunen_effect` 在 j16 下另加两个条件：孙泰 `langya_sun_003` 已不在世，且日期 ≥ 399.10.1。年度脉冲在年初触发，所以实际最早 400 年才会起兵。非 j16 局不加这两个条件，因为孙泰不按卒年表死，加了可能永远起不了。 | — |
| 8 | minor 404 秦况计数要两个一起设 | 已写进第五节交 5-A、6-B 的部分。 | — |
| 9 | minor 报告措辞 | 已改：loc 键数改为各 37；k_yongzhou 实测项改为篡夺苻坚；交 6-A 部分注明 `hd_j16_hi_mode_trigger`、`hd_hi_try_start_<KEY>_effect` 已由本任务定义。 | — |

**仍未解决：**
1. tande 的 ID 归属待定。
2. 七折是否另加实际效果待定。
3. 0200.d 偏离设计（当前没有触发者）。
4. 本任务必须与 5-A 同批落盘。

## 一、暂存任务名与文件清单

暂存任务名：**p5-C**。暂存目录：`D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p5-C\files\`

**新建 4 个**（UTF-8 带 BOM，LF）：
- `common/scripted_triggers/zz_hd_hi_j16_triggers.txt`：入侵侧读取的全部 j16 判定，包括新增的 `hd_hi_j16_is_leader_trigger`。
- `common/scripted_effects/zz_hd_hi_j16_effects.txt`：try_start 抽取、秦况排程、名单标记、首领标记（新增 `hd_hi_j16_mark_leaders_effect`、`hd_hi_j16_mark_one_effect`），以及西燕起兵附加。
- `localization/simp_chinese/zz_hd_j16_hi_l_simp_chinese.yml`、`localization/english/zz_hd_j16_hi_l_english.yml`：各 37 键（规则 15、事件 12、国号 10），中英一一对应。

**改动 5 个**（UTF-8 带 BOM、LF 不变，无 CR，花括号平衡）：
- `common/scripted_effects/zz_hd_hi_effects.txt`
- `common/scripted_effects/zz_hd_hi_data_effects.txt`
- `common/on_action/zz_hd_hi_on_actions.txt`
- `events/zz_hd_hi_events.txt`
- `common/game_rules/zz_hd_hi_rules.txt`

修正后复核：5 个改动文件的 base_sha256 仍与 mod 现文件一致；新名字在 mod 和其他暂存区里都没有同名定义。没有跑生成器，没有开游戏，没有提交 git。

**闸门**（复跑，输出 `D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p5-C_gate.txt`）：
- 相对基线新增 error 19（全部是 gvar_read_never_set）、warn 1，与修正前相同。
- resolved_vs_baseline = 1：闸门只给计数、不列明细，没有逐条追查。
- 带 effect 的 on_action 总数 6721。本任务共新增 4 个：murongchong、murongde、sunen、j16_mark。上一版报的总数是 6718，这次只多了 1 个，另外 2 个的差值应是别的会话改了 mod，不是本任务所致。离 1 万上限很远。

## 二、做了什么

1. **判定**（triggers 新文件）：
   - `hd_j16_hi_mode_trigger`：判 `hd_j16_pulse_started`。
   - `hd_j16_hi_qin_mode_trigger`：pulse_started 成立，且 existed 或 collapse 二者有其一。
   - `hd_hi_qin_started_trigger`、`hd_hi_qin_m_trigger = { M MW }`（weak 时用 MW，即 M 加 12）、`hd_hi_qin_end_trigger`（M≥120 或已到 421.1.1）。
   - `hd_j16_hi_env_ok_trigger`、`hd_j16_hi_next_stage_closed_trigger`（shelun_3 在 404 开局视为已开）。
   - `hd_j16_hi_crown_protected_trigger`、`hd_hi_j16_is_leader_trigger`。
2. **try_start 抽取**：
   - 共用体 `hd_hi_try_start_effect = { KEY ID }`：依次查规则和 done，用 `hd_j16_resolve_effect` 解析本人，`hd_hi_leader_ready_trigger` 成立才调 `hd_hi_begin_effect`。
   - 包装共 **12 个**：`hd_hi_try_start_<KEY>_effect`，KEY 为 tuobagui、murongchui、murongchong、yaochang、qifuguoren、lvguang、tufawugu、juqumengxun、helianbobo、shelun、murongde、sunen。tande 没有包装。
   - 姚苌的旧前提（姚弋仲已不在世）、孙恩的 j16 前提都写在各自的包装里。
3. **秦况排程**：
   - 入口 **`hd_hi_qin_schedule_effect`**：秦况模式下先调名单标记，再依次调 `hd_hi_qin_sched_<KEY>_effect`（murongchui、murongchong、yaochang、qifuguoren、lvguang、tuobagui）。
   - 每档先调 `hd_hi_qin_close_effect`：本人已死、M≥120 或到 421.1.1 时设 done。
   - 各档开始条件（正式瓦解 / 只有 weak）：

     | 档 | 条件 |
     |---|---|
     | ① 慕容垂 | `hd_j16_chui_north` 即开始；被拒时 M≥6/18；否则 M≥2/14 |
     | ② 慕容冲 | M≥3/15 |
     | ③ 姚苌 | 西燕已开始（`hd_hi_started_murongchong`），或 M≥4/16 |
     | ④ 乞伏国仁 | M≥12/24；正式瓦解时苻坚已死也算 |
     | ⑤ 吕光 | 已设 `hd_j16_xiyu_won` 时 M≥1/13；否则 M≥18/30 |
     | ⑥ 拓跋珪 | 386.1.1 以后，且刘库仁已死或 M≥24/36 |

4. **年度 on_action**：
   - ①～⑥ 和 murongchong：秦况模式下改调排程；j16 局在 383.7.1 前只等待；其余情况照旧逻辑，只是人物改经解析、调 try_start。
   - 四个开闸 KEY（tufawugu、juqumengxun、helianbobo、murongde）：j16 下不抽签，已开闸时每年补试一次。
   - shelun、sunen：改为调 try_start。
   - tande：逐字照旧。
   - 新增 4 个年度 on_action，追加进 `yearly_global_pulse`：`hd_hi_yearly_murongchong`、`hd_hi_yearly_murongde`、`hd_hi_yearly_sunen`、`hd_hi_yearly_j16_mark`。最后一个的 trigger 是 j16 模式、383 ≤ 年份、日期 < 421.1.1。
5. **环境短路**：只改了 `hd_hi_eval_env_effect` 开头一处，env_ok 成立时直接设 `flag:ok`，原评估放进 else。三个蛰伏入口没有改。
6. **阶段闸门**：`hd_hi_load_next_stage_effect`、`hd_hi_stage_check_effect` 在闸门未开时停在「本阶段已完成」，不推进阶段、不宣战，等待日志只记一次。闸门对象：tuobagui_2、tuobagui_3、helianbobo_3、shelun_3。
7. **王冠不篡夺**：
   - `hd_hi_crown_effect` 开头先调 `hd_hi_j16_mark_leaders_effect`。
   - 篡夺分支加 `NOT = { hd_j16_hi_crown_protected_trigger = yes }`。
   - 受保护时只改国号：本人主头衔为郡级及以上才改，同时照常记到王朝 `hd_fixed_realm_name`。
   - 第一阶段取王冠只做一次（story 变量 `hd_hi_crowned`）。
8. **数据**：
   - 新增 murongchong、sunen、murongde 三个数据效果。
   - 吕光：home 和第 1 阶段改为 `d_dunhuang_hexi`；沮渠蒙逊：第 2 阶段删去冥泽。
   - A6-F10 国号：西秦、后凉、南凉、北凉。另提供 `dynn_title_xiliang` 供 E5-X38 使用。
   - 慕容垂、姚苌：已设 `hd_j16_wangmeng_heeded` 时 army_est 打七折。
9. **名单标记**：`hd_hi_j16_reserve_effect` 给在世的慕容垂、慕容泓、慕容冲、姚苌、乞伏国仁、吕光设 `hd_j16_hi_reserved`，只在对应规则开着且该条目未了结时设。
10. **规则**：新增 `hd_hi_rule_murongchong`、`hd_hi_rule_murongde`、`hd_hi_rule_sunen`，中英 loc 齐全。
11. **事件**：0200、0300、1001、1002 加三个新 KEY 的标题与正文分支，不新增事件号。

## 三、自拟与偏差

1. 新判定、新效果放在新文件 `zz_hd_hi_j16_*` 里；loc 也是新建的 `zz_hd_j16_hi_l_*.yml`。
2. 秦况模式条件写成「existed 或 collapse」。
3. j16 局在 383.7.1 前，年度抽签只等待。
4. 秦况模式下，年度 on_action 逐条补跑排程。原因：E4-W50 的窗口止于 394.12.31，之后靠年度补跑。
5. 秦况开始一律要求 collapse 或 weak 二者有其一；「苻坚已死」只在正式瓦解时算。
6. 自拟变量名：`hd_j16_chui_north_denied`、`hd_j16_hi_go_<KEY>_late`、`hd_hi_started_<KEY>`、`hd_hi_j16_leader`（人物）、`hd_hi_j16_leader_dyn`（王朝）。
7. **王冠保护的依据（已重写）**：
   - A6-F5 原文是「持有者是 hd_hi 首领或首领的上级」。实现改为：持有者或其 top_liege 是「首领」。首领的认法有三种：起过兵（hd_hi_key）、年度标记过的在世首领（hd_hi_j16_leader）、拓跋氏与凉州四家的王朝成员（hd_hi_j16_leader_dyn）。
   - 第三种是为 06 §4.3 并州例加的：404 局拓跋珪从没起兵，409 年后又由拓跋嗣继位。
   - 前秦苻氏、东晋不在名单里，所以秦况各家照旧从苻坚手里篡夺王冠。
   - 没有采用审查者的「top_liege 是王级以上独立君主即保护」：那样连苻坚的王冠也保护了。
   - 「第一阶段取王冠只做一次」（`hd_hi_crowned`）用于防止闸门停留期间反复取冠，非 j16 局行为不变。
8. **0200 选项 d（已改写）**：偏离设计，当前没有触发者。04 §2.4 要求 d 玩家专用；现有 d 没有 trigger，王级以上的电脑首领也会选它，随即 abandon，这场入侵永久消失。已核：370、404 的秦况首领和开闸首领目前都只到郡级。所以开闸节点须先 try_start 再升王级（交 6-A）。没有改，以免影响非 j16 局。
9. **解析改造的范围**：只改了 383–421 年间的 12 个条目。tande 已回退为逐字照旧。liuyu、qiaozong、luxun，以及 383 年以前、520 年以后的条目都没有改。
10. sunen 数据：一个阶段（会稽、吴郡、吴兴），celestial 政体，步兵，规模 2、8000；非 j16 窗口 399–402，概率 40/60/100。
11. murongchong：非 j16 窗口 384–390，概率 40/60/100，王冠 `k_yongzhou`。慕容泓在世、无地、是 AI 时入慕容冲的宫廷；没做「领一部分事件兵」。
12. murongde：home 有地时取本人都城所在省，否则取魏郡（不是「d_weijun 优先」）；tribal 政体，骑兵；非 j16 窗口 397–405，概率 15/40/100。
13. 孙恩起事时设 `hd_hev_j16_sunen`，所有开局都设。
14. **没有用 j16 判定包裹的改动**（逐条说明为什么不算退化）：
    - 解析改为先查 `character:` 再查指针。
    - A6-F10 国号：只影响显示。
    - 冥泽改真敦煌：修正错郡。
    - 三个新条目在非 j16 局按年度抽签。
    - 慕容泓入宫廷。
    - `hd_hev_j16_sunen`、`hd_hi_crowned`、`hd_hi_started_<KEY>`。

    其余新逻辑一律以 **`hd_j16_hi_mode_trigger`**（即 `hd_j16_pulse_started`）或 `hd_j16_hi_qin_mode_trigger` 包裹，没有用 `hd_j16_start_trigger`。理由：规则关闭的 j16 开局应走旧逻辑。首领标记、sunen 的 j16 前提也用这个判定包裹。
15. `hd_j16_strong_qin_trigger` 属于设置侧，本任务没有定义。
16. 新键只补了中文、英文，日文、韩文下新规则会显示原始键名。
17. **（新）`hd_j16_wangmeng_heeded` 的七折在主路径上不起作用**：army_est 只在环境评估里用到，而正式瓦解时 murongchui、yaochang 的环境判定被短路了。七折只在 weak 路线或慕容垂被拒时生效。是否另加实际效果（例如事件兵规模也乘 0.7），交汇总人决定。
18. **（新）sunen 的 j16 前提**：只在 j16 下要求孙泰已死、日期 ≥ 399.10.1，实际最早 400 年起兵；非 j16 局不加。
19. **（新）shelun_3 在 404 开局视为已开**：E5-X50 在 404 是前标，不会设闸门。

## 四、R7 回归

- 404 开局 `hd_hi_done_liuyu`（在 `hd_j16_startup_404_effect`）、juqumengxun 和 tande（在 `zz_hd_nbc_startup_effects.txt` 的 `hd_nbc_hi_done_effect`）三个预设所在文件都没有动。
- 谯纵年度块、tande 年度块、hd_hi 公共流程逐字未改。
- 404 局 shelun 能推进到第 3 阶段（本次修正），sunen、murongchong 在第一次年度脉冲即设 done。
- 190、218 等局：除第三节第 14 条以外没有改动。

## 五、需要汇总人处理的事项

**阻塞项：p5-C 必须和 5-A 同批落盘、同批实测。** 否则 E4-Q51 设了 collapse 而 E4-W50 不累加计数，①～⑤ 永远不会起兵，要拖到 421 年才了结。

**交 5-A：**
1. E4-W50 每跳的顺序：先设或更新 `hd_j16_qin_existed`、`hd_j16_qin_size_383`、`hd_j16_qin_collapse`、`hd_j16_qin_collapse_m`、`hd_j16_qin_weak`，再调用 **`hd_hi_qin_schedule_effect = yes`**。建议 M 在 394.12.31 之后继续累加到 120。
2. 定义 `hd_j16_strong_qin_trigger`。
3. E4-Q51 在 `trigger_event = hd_nbc.0161` 之前调用一次 **`hd_hi_j16_reserve_effect = yes`**。
4. 设下列变量：
   - E4-M25 a 设 `hd_j16_chui_north`，b 设 **`hd_j16_chui_north_denied`**；
   - E4-Q45 设 `hd_j16_xiyu_won`；
   - E4-Q25 a 设 `hd_j16_wangmeng_heeded`。
5. E4-M20 选 b 时直接调用 `hd_hi_try_start_murongchui_effect = yes`。
6. **404 开局：`hd_j16_qin_collapse` 与 `hd_j16_qin_collapse_m = 120` 要么同时设，要么都不设。** 只设 collapse 时，404 局会进入秦况模式而 M 一直是 0，拓跋珪会在 404 局假起兵一次。

**另交汇总人指定写入者：** `events/zz_hd_nbc_events.txt` 中 `hd_nbc.0161` 的 `every_vassal` limit 加 `NOT = { has_variable = hd_j16_hi_reserved }`（归 1-D→6-A）。

**交 6-A：**
1. `hd_j16_hi_mode_trigger` 和全部 `hd_hi_try_start_<KEY>_effect`（12 个，没有 tande）已由 p5-C 定义。6-A 只调用，不要重复定义。
2. 开闸节点 X14、X18、X58、M30：先设 `hd_j16_hi_go_<KEY>`（tufawugu、juqumengxun、helianbobo、murongde），再调 try_start。窗口末兜底时另设 **`hd_j16_hi_go_<KEY>_late`**。**必须先 try_start，再做任何会让首领升到王级的操作**（如 X14 称西平王），否则电脑首领会在 0200 选 d 自弃。
3. 阶段闸门：
   - `hd_j16_hi_gate_tuobagui_2`：E5-M10 或 T10 设；
   - `_tuobagui_3`：T10 设；
   - `_helianbobo_3`：J80 或 X86 设；
   - `_shelun_3`：X50 设（404 开局已在触发器里视为已开）。
4. **通则**：凡是设闸门的节点被前标或自保护跳过时，也必须把闸门设上，或在触发器里像 shelun_3 那样按开局年份视为已开。
5. E5-X38 用国号键 `dynn_title_xiliang`。
6. 6-A 落盘前的过渡状态属于设计内：tuobagui、helianbobo、shelun 会停在闸门前；四个开闸 KEY 只按年份上限了结。

**交 6-B：** 404 的 done 预设已齐，shelun_3 不需要预设。404 秦况计数照交 5-A 第 6 条：要么同时设，要么都不设。

**交汇总人或 2-A：** tande 条目的 ID `hd_nbc_gjl_gao_tan_de` 在库中已不存在（05 G1 合并为 `korean_go_goguryeo_13`，404 头衔也指向它），旧年度块从未真正触发。改指新 ID 还是作废，请决定；本任务保持逐字照旧。

**生成器：** 不需要重跑。

**实测项：**
1. 370 局西燕从苻坚手里篡夺 `k_yongzhou`。
2. 404 局勃勃第 1 阶段完成后，对并州（拓跋遵）不篡夺、只改国号。
3. 不篡夺时国号改在主头衔上，名字会留在该头衔上。
4. `add_courtier` 在冒险者营地上是否成功（慕容泓入宫廷）。
5. 凉州四家之间不互夺王冠。

## 六、本期面板行清单（交 F-1，只列不写）

- `hd_hev_j16_sunen`：「孙恩起事」。组 `hd_hev_grp_j16_e5j`，范围 le370，由 `hd_hi_rise_effect` 在 sunen 起兵时设。

## 七、新增事件号、变量名

**事件号：** 无新增。只改了 hd_hi 0200、0300、1001、1002 的分支，0200 只改了文件头注释。

**本任务设置的变量：**
- 全局：`hd_hi_started_<KEY>`、`hd_hi_done_murongchong`、`hd_hi_done_murongde`、`hd_hi_done_sunen`、`hd_hev_j16_sunen`。
- 人物：`hd_j16_hi_reserved`、`hd_hi_j16_leader`。
- 王朝：`hd_hi_j16_leader_dyn`。
- story：`hd_hi_crowned`、`hd_hi_gate_wlog`。

**只读、由他人设置的变量：** `hd_j16_pulse_started`、`hd_j16_start_year`、`hd_j16_qin_existed`、`hd_j16_qin_collapse`、`hd_j16_qin_collapse_m`、`hd_j16_qin_weak`、`hd_j16_chui_north`、`hd_j16_chui_north_denied`、`hd_j16_xiyu_won`、`hd_j16_wangmeng_heeded`、`hd_j16_hi_go_<KEY>`、`hd_j16_hi_go_<KEY>_late`、`hd_j16_hi_gate_<KEY>_<N>`。

**新定义的名字：**
- 触发器：`hd_j16_hi_mode_trigger`、`hd_j16_hi_qin_mode_trigger`、`hd_hi_qin_started_trigger`、`hd_hi_qin_m_trigger`、`hd_hi_qin_end_trigger`、`hd_j16_hi_env_ok_trigger`、`hd_j16_hi_next_stage_closed_trigger`、`hd_j16_hi_crown_protected_trigger`、`hd_hi_j16_is_leader_trigger`。
- 效果：
  - `hd_hi_try_start_effect` 与 12 个 `hd_hi_try_start_<KEY>_effect`；
  - `hd_hi_qin_schedule_effect`、`hd_hi_qin_close_effect`、`hd_hi_qin_sched_<KEY>_effect`（6 个）；
  - `hd_hi_j16_reserve_effect`、`hd_hi_j16_reserve_one_effect`；
  - `hd_hi_j16_mark_leaders_effect`、`hd_hi_j16_mark_one_effect`；
  - `hd_hi_murongchong_rise_effect`；
  - `hd_hi_data_murongchong_effect`、`hd_hi_data_sunen_effect`、`hd_hi_data_murongde_effect`。
- on_action：`hd_hi_yearly_murongchong`、`hd_hi_yearly_murongde`、`hd_hi_yearly_sunen`、`hd_hi_yearly_j16_mark`。

**闸门 19 条 error 的解释：**
- 18 条是交 5-A、6-A 设置的只读接口变量。
- `hd_hi_started_murongchong` 在 begin 里以 `$KEY$` 参数形式设置，闸门跳过了参数名，属误报。
- warn 1 条是面板变量 `hd_hev_j16_sunen`，由 F-1 来读。

**新游戏规则：** `hd_hi_rule_murongchong`、`hd_hi_rule_murongde`、`hd_hi_rule_sunen`。

**新国号键：** `dynn_title_xiqin`、`dynn_title_houliang`、`dynn_title_nanliang`、`dynn_title_beiliang`、`dynn_title_xiliang`（均含 `_adj`）。