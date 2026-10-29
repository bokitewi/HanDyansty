# p5-A1 最终报告（修正后合并版）

# p5-A1「370 节北方节点」审查修正报告

两条 major 已修好。11 条中有 9 条改了代码；另外 2 条（百济换人、面板重叠）没有改代码，在报告里写明后交汇总人。全部改动只在暂存区，没有新增 stage 登记。修完复跑闸门：error 9（与上次同为 9 条，类别不变），warn 从 51 降到 46。

## 〇、审查意见逐条处理

### major-1 燕凤使秦让导演永久作废代阶段 —— 已修
- `hd_j16_weichen_yanfeng_effect` 撤闸门时，同时 `remove_global_variable = hd_j16_weichen_done`。
- 缓兵期满重开的那一段，在同一个效果里重设 `hd_j16_weichen_done` 和 `hd_j16_dir_qin_gate_dai`（后者仍在未灭代、未称藩时才设）。
- T10 节点外层 limit 加了 `NOT hd_j16_weichen_yanfeng`、`NOT hd_j16_weichen_reopen`，缓兵期内 AI 分支不会重新开闸。
- 已核导演一侧（只读，没改）。`zz_hd_j16_dir_data_effects.txt` 的 S7 段在 gate_dai 不在时设 `hd_j16_dir_gated`。`zz_hd_j16_dir_effects.txt:404-420` 的 tick 遇到 gated 只记 WAIT，不计空转，也不判完成。transition 的 S7 作废支要求 done 已设，缓兵期 done 不在，所以不会作废。因此缓兵这一年导演只是挂在 S7 等闸门，修复成立，不需要改 4-A 的文件。

### major-2 M25 在玩家慕容垂回复 4150 前就记 SKIP deviated —— 已修
- deviated 判据改为：`hd_j16_hujia_skip` 已设，或者「`hd_j16_hujia_result` 已设且没有 `hd_j16_chui_askhebei`」。
- `hujia_result` 只由 a/b/c 三个执行体设，所以玩家待答期间 M25 会等待，到 384.6.2 窗口关闭为止。

### minor-3 5-D 转交的两条
- **第 6 条（百济持有者换 korean_buyeo_49）：未做，交汇总人。** 查到的情况：
  - 这个人物在 `history/characters/zz_hd_oe_characters.txt:79676`。
  - 他同时由出场生成器管理（有 `hd_hb_s_korean_buyeo_49_effect`、模板 `hd_hb_t_korean_buyeo_49`）。直接写进 370 头衔 holder，会不会造成重复生成或指针错位，要在生成器一侧确认。
  - 王朝 `korean_buyeo` 在 `common/dynasties/` 下全 mod 都 grep 不到定义；纹章只在 `zz_dm_bce_generated_family_coas.txt:70530`。王朝定义和固定纹章可能要补，再重跑 `gen_dynasty_fixed_coas.py`，本路不能跑生成器。
  - 346 那份需同步改。
  - 待改的 8 行：titles `:82`、`:524`、`:525`、`:526`；undo `:75`、`:515`、`:516`、`:517`。两个文件本路都没有 stage edit。
- **第 7 条（司马奕廷臣去向）：已做（自拟）。** 在 `hd_j16_abdicate_effect` 里转头衔之前，把司马奕的廷臣 add_courtier 给新帝。条件：成年、未被囚、非人质、不是新帝本人、不是司马奕近亲或配偶，且 `NOT employer ?= 新帝`（5-D 已放好的人不受影响）。临时 scope 为 `hd_j16_fl_mv`。所有开局都生效；被搬的人原有宫廷职位会丢失。

### minor-4 面板行与 p4-A 的 s6/s7 重叠 —— 写进报告，交汇总人二选一
本路的 `hd_hev_j16_mieliang`、`hd_hev_j16_miedai` 和 p4-A 的 `hd_hev_j16_dir_qin_s6`、`_s7` 是同一件事，见第三节。

### minor-5 吕光西征：玩家秦主的史实选项必然失败 —— 已修
- 玩家秦主本人持有敦煌首府县时，`hd_j16_lvxizheng_start_effect` 在授郡前设临时全局 `hd_j16_n370_grant_player_ok`，用后即删。
- `hd_j16_n370_grant_duchy_effect` 的 FROM 条件改为 `OR = { is_ai = yes  has_global_variable = hd_j16_n370_grant_player_ok }`。玩家在 4130 选 a，视为同意授郡。
- ② 的判定改为「吕光在世、未被囚」，不再要求有地。这是对 04 原文的简化，列入自拟与偏差。

### minor-6 苻丕本人已是前秦主时口径不一 —— 已修
在 `hd_j16_node_fupi_effect` 里加一支：`scope:hd_j16_q70_cur` 就是苻丕时，设 `hd_j16_fupi_result`、威望 +300，记 `FIRE fupi_already_ruler`。与 Q80 的口径一致。

### minor-7 M05 先于玩家的金刀计决定执行 —— 已修
- M85 新增 `hd_j16_jindao_settled`，表示金刀计整条走完。秦主宽宥（垂选 a 或 b）时设，慕容令识破留秦时也设。
- M05 的上游判据改为以下任一：开局年 ≥ 370；或 `jindao_settled` 已设；或慕容令已死而 M85 从未行计（`jindao_result` 未设）。
- 开局年 < 370 时，以下情况 M05 记 SKIP deviated：王猛不行计（`_declined`）；或 M85 跳过时慕容令仍在世，即计未行。

### minor-8 慕容令卒年 370.1.1 与 M85 窗口冲突 —— 交汇总人，见第四节第 5 条
不改 tsv。

### minor-9 君川新闻回退到天子 —— 已修
谢玄取不到时回退为刘牢之 `congtingli_liu_043`。两人都取不到就不发新闻。

### minor-10 新建文件头注释归属写错 —— 已修
事件、触发器、修正、好感修正四个文件改为「写入者：第 5 期 5-A1（三路分文件，5-A2 用 370b、5-D 用 370c）」。

### minor-11 接壤判定的性能浪费 —— 已修
- T10：把「刘卫辰为 AI 且已到 376.6.1」或「刘卫辰为玩家且无 `_asked`」放在 `hd_j16_n370_borders_realm_trigger` 之前。
- Q30：把 `NOT hd_j16_liang_asked` 放在接壤判定之前。

**自检：** 全部 9 个文件都是 UTF-8 带 BOM、LF，括号配平。新增 trigger `is_close_family_of`、`is_consort_of`、`is_hostage` 在原版里都有用例。

## 一、暂存任务名与文件
- 任务名 **p5-A1**。暂存区：`D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p5-A1\files\`
- 改动 3 个：
  - `common/scripted_effects/zz_hd_j16_e3_370_effects.txt`
  - `common/scripted_effects/zz_hd_j16_e4_370_effects.txt`
  - `events/zz_hd_370_events.txt`（旧 370 事件文件）
- 新建 6 个：
  - `events/zz_hd_j16_370_events.txt`
  - `common/scripted_triggers/zz_hd_j16_370_triggers.txt`
  - `common/modifiers/zz_hd_j16_370_modifiers.txt`
  - `common/opinion_modifiers/zz_hd_j16_370_opinion_modifiers.txt`
  - `localization/simp_chinese/zz_hd_j16_370_l_simp_chinese.yml`
  - `localization/english/zz_hd_j16_370_l_english.yml`
- yml 中英各 111 键，一一对应。
- `history/titles/zz_hd_370_titles.txt` 和 `zz_hd_370_undo.txt` 都没有 stage edit。原因：本路节点不需要改 370 开局头衔数据；百济 8 行交汇总人；什翼犍京城注释按决定不改京城，可选的注释修正为免并发冲突也没做。
- 没有直接写 mod，没有跑生成器，没有开游戏，没有提交 git。

## 二、自拟与偏差（合并更新）
1. **T10 开闸窗口：** 从 376.9.1 延到导演下线。Q10、Q30、T20 拆成两层：done 跟随攻取，善后受窗口限制。依据是 04 §1.1「闸门不设截止」，以及导演对 done 的解读（`zz_hd_j16_dir_effects.txt:456-525`）。
2. **燕凤使秦（4061 c）：** 撤闸的同时撤 `weichen_done`，缓兵期满重设两者。缓兵期内导演在 S7 按 gated 挂起。
3. **袁真据寿春前置节点（D16）：** 授 1 郡，同一政权内。袁真 X 特例在 304/346 局的放开，用 e3 的转发调用 `hd_j16_node_yuanzhen_x_effect` 实现。二者择一：汇总人若改 tsv 的「开局限制」列，让生成物直接放开，就删掉这个转发。
4. **旧 370 事件文件超出「只改文本与选项」：** 0170 的 trigger 改成按位置判断；0110–0170 加了 immediate 解析和 portrait 条件。依据是 impl_notes「移交 5-A」。
5. **Q70、Q80 的吞并写法：** 用 `hd_370_take_realm_effect`（不杀旧主），不用 04 写的 `hd_nbc_seize_realm_effect`（会杀旧主）。另外，苻丕本人已是前秦主时按 fire 处理（`fupi_already_ruler`）。
6. **苻融阵亡：** 由 Q51 节点在秦败时处理，只杀 AI，凶手谢玄，走卒年核心 `hd_j16_death_violent_effect`；不进 tsv。
7. **吕光西征改名：** 整组改为 `hd_j16_lvxizheng_*`，避开 304 节已用的 xizheng 变量。
8. **M85 的威望与「束身待罪」：** 宽宥时的威望 +100 给秦主（04 原文主语不明）。垂选「束身待罪」同样宽宥，另给垂威望 +50。
9. **未实现：** 04 §6 的「慕容垂随苻丕攻襄阳（参战）」没有补。原因是 `hd_nbc_add_attacker_effect` 写死了 `character:$WHO$`。
10. **朱序「阵后一呼」：** 统一放在 Q50 节点里给，不改 6-A 的 0160。
11. **M10 与 M20 b：** M10 b 诛垂时直接设 `hd_hi_done_murongchui`。M20 b 先调 `hd_hi_try_start_murongchui_effect`；入侵没有开始时，退回「独立 + 5000 事件兵」。
12. **【新】Q45 ② 的判定：** 简化为「吕光在世、未被囚」。04 原文是「事件兵仍在或兵力 ≥ 5000」。
13. **【新】Q45 玩家秦主授郡：** 玩家秦主本人持有敦煌首府县时，用临时旗标 `hd_j16_n370_grant_player_ok` 放行授郡（玩家选 a 视为同意），用后即删。
14. **【新】M05 的上游判据：** 改读 `hd_j16_jindao_settled`。王猛不行计，或 M85 跳过时慕容令仍在世，M05 记 SKIP deviated。
15. **【新】M25 的 deviated 判据：** 改读 `hujia_skip`，或「`hujia_result` 已设且无 `askhebei`」。
16. **【新】君川新闻：** 回退为刘牢之，两人都取不到就不发。
17. **【新】废立时搬司马奕廷臣：** 规则见第〇节 minor-3 第 7 条。所有开局生效，被搬者原有宫廷职位会丢失。

## 三、本期面板行清单（交 F-1，只列不写）
| 行 | 变量 | 设置处 | 适用 |
|---|---|---|---|
| 370 组 06 灭凉 | `hd_hev_j16_mieliang` | E4-Q30：姑臧归秦一系即设，不受善后窗口限制 | le370 |
| 370 组 07 灭代 | `hd_hev_j16_miedai` | E4-T20：云中归秦一系即设 | le370 |
| 370 组 08 襄阳 | `hd_hev_j16_xiangyang` | E4-Q40：秦胜时 | le370 |
| 09 桓温卒、10 北府兵 | — | 归 5-A2 或卒年特殊段 | — |

- **与 p4-A 重叠：**
  - 06 灭凉与 p4-A 的 `hd_hev_j16_dir_qin_s6`（前凉平定）是同一件事；07 灭代与 `hd_hev_j16_dir_qin_s7`（代地平定）也是。
  - F-1 两份都照做会出现重复行，由汇总人二选一。
  - 若保留导演行，删掉本路 e4 里的 `set_global_variable = hd_hev_j16_mieliang` 和 `set_global_variable = hd_hev_j16_miedai` 两行（各有行尾注释「面板（04 §1.5 第 06/07 行）」）。
- 淝水、前秦瓦解两行按 04 §1.5 不另加。

## 四、需要汇总人处理的事项
1. **必须与 5-A2 同批落盘：** 本路入口调用 `hd_j16_e4_370b_effect`，E4-X10 读 `hd_j16_beifu_done`。p5-A2 暂存里两者都已定义、已设置。
2. **4-B（346 第二轮）必须按约定接口名设置：** `hd_j16_fangtou_done`、`hd_j16_yuanzhen_blamed`、`hd_j16_huanwen_regent_result`。本路已经读它们。
3. **袁真 X 特例的放开二选一：** 保留本路的转发调用，或者改 tsv 和生成器后删掉转发。
4. **卒年 X 行（苻坚、慕容暐、什翼犍）限定 `start_year = 370`：** 304/346 局里苻坚不会按 X 卒年死去，Q70、Q80 和 (b) 条瓦解判定在这两局只能等长安失守。是否放开，由汇总人或 2-D 决定。
5. **【新】慕容令卒年冲突：** 慕容令 `changli_murong_039` 卒年 370.1.1，没有 PRE。M85 要求洛阳之战已开，304/346 局实际可行计的时间只有约一个月。建议给慕容令卒年加 PRE `hd_j16_jindao_ling_fled`（逃燕后才死），或把卒年推到 370.3 前后。不改的话列为实测项。
6. **【新】370 开局百济持有者换 `korean_buyeo_49`：** 未做，交汇总人。理由和 8 个行号见第〇节 minor-3 第 6 条。
7. **【新】面板 06、07 与 p4-A s6、s7 二选一：** 见第三节。
8. **风险：** core 的 E4 粗筛止于 400.1.1。collapse 来得晚时，月计数到不了 120，入侵条目收不了尾。请考虑在 core 里按 `hd_j16_qin_collapse_m < 120` 延续 E4 粗筛（core 已冻结）。
9. **6-B 不必再设 404 局秦况：** W50 在 404 首跳已同时设 collapse 与 M = 120，并已摘导演旗标。
10. **不需要重跑生成器：** 本路没有新建人物，也没有改 tsv。百济那条若实施，需要重跑。
11. **实测项：**
    - 304 局 0170 能否弹出、`hd_370_feili_enthroned` 能否设上；game.log 应有 `e4_j10 FIRE regent_ok`。废立后司马奕的廷臣是否已在新帝宫廷。
    - 346 局获咎后袁真受寿春，370.4.10 袁瑾独立，J80 开打。
    - 导演跨过原窗口后补打仇池、前凉时，done 与阶段完成的衔接。玩家什翼犍选燕凤使秦，一年后导演是否重新打代。
    - 370 局淝水能开（入口已收窄 is_at_war）。
    - 玩家慕容垂在 4150 选 c 后，M25 能否弹 4160。

## 五、新增事件号与变量名
- **事件：** hd_j16.4000–4002、4010、4020、4030、4040、4041、4050、4060、4061、4080、4100、4110、4130–4132、4140、4150、4160、4170、4180。
- **效果和触发器前缀：**
  - 工具：`hd_j16_n370_*`。
  - 节点：`hd_j16_node_jindao`、`jindao_after`、`qingzhu`、`qiuchi`、`liangyi`、`yiyan`、`weichen`、`miedai`、`mieliang`、`zhuxu`、`xiangyang`、`junchuan`、`fupi_ye`、`lvxizheng`、`dir_off`、`hujia`、`hebei`、`qinkuang`、`fupi`、`fudeng`、`yuanzhen_shouchun`、`yuanzhen_x` 各 `_effect`。
  - 触发器：`hd_j16_liangyi_ready_trigger`、`hd_j16_xiangyang_ready_trigger`、`hd_j16_lvxizheng_ready_trigger`、`hd_j16_strong_qin_trigger` 等。
- **全局变量**（各节点另有 `_done`、`_skip`、`_wlog`、`_result`，下面只列其余）：
  - M85：`hd_j16_jindao_ling_fled`、`_ling_stayed`、`_declined`、**`hd_j16_jindao_settled`（新）**
  - M05：人物变量 `hd_j16_chui_resent`
  - M10：`hd_j16_chui_spared`
  - 导演接口：闸门 `hd_j16_dir_qin_gate_qiuchi`、`_liang`、`_dai`；下线 `hd_j16_dir_qin_off`；节点 done `hd_j16_qiuchi_done`、`hd_j16_liang_done`、`hd_j16_weichen_done`、`hd_j16_dai_done`
  - Q10/Q30：`_asked`、`_army`、`_vassal`
  - T10：`hd_j16_weichen_delay`、`_delay_done`、`_yanfeng`、`_yanfeng_used`、`_reopen`
  - 战争场次 `hd_j16_liangyi_*` 与 `hd_j16_xiangyang_*`：各含 `_started`、`_won`、`_lost`、`_att`、`_def`、`_go`、`_wait`、`_asked`、`_wsf_wlog`
  - Q40：`hd_j16_zhuxu_in_qin`
  - Q45：`hd_j16_lvxizheng_*`（`_started`、`_t1`、`_t2`、`_step2`、`_failed`、`_asked`）、`hd_j16_xiyu_won`；**临时旗标 `hd_j16_n370_grant_player_ok`（新，用后即删）**
  - Q25：`hd_j16_wm_qinchen`、`hd_j16_wangmeng_heeded`
  - 淝水：`hd_j16_feishui_qin`、`_end`、`_zhenhou`、`_skip`、`_wlog`
  - M20/M25：`hd_j16_chui_escort`（全局，并在垂身上设同名人物变量）、`hd_j16_chui_askhebei`、`hd_j16_hujia_betray`、`hd_j16_chui_north`、`hd_j16_chui_north_denied`
  - 秦况：`hd_j16_qin_existed`、`_existed_checked`、`_size_383`、`_size_half`、`_collapse`、`_collapse_m`、`_weak`、`_m_tick`、`hd_j16_qin_title`、`hd_j16_qinkuang_404`
  - 袁真前置：`hd_j16_yzsc_done`、`_result`、`_skip`、`_wlog`
  - 新增临时 scope：`hd_j16_fl_mv`
- **04 编号式旧名 → 语义名：**
  - `hd_j16_liangyi_qin_won` → `hd_j16_liangyi_won`
  - `hd_j16_zhuxu_set` → `hd_j16_zhuxu_result`
  - 吕光西征一组 → `hd_j16_lvxizheng_*`
  - E4-W50 → `hd_j16_node_qinkuang_effect`
- **p3-D 待办核实：**
  - `hd_nbc_feishui_white` 会真被设上：CB 白和时调 `hd_nbc_war_result_effect = { RESULT = white }`，分发表含 feishui，按参数设 `hd_nbc_feishui_<RESULT>`。兜底分支只给 won/lost。
  - E4-M20 a 设 `hd_j16_chui_escort`。
  - 370 废立后桓温经 `hd_j16_feili_regency_effect` 装为 hd_court 权臣（满足 `hd_asp_is_regent_trigger`）。

## 六、卒年表 PRE 设置处
- tsv 第 8 列里归本路节点的 PRE 只有一个：`hd_nbc_feishui_lost`（梁成）。设置处有两处：
  - CB 结局分发表 `hd_nbc_war_result_kind_effect`（按参数）；
  - E4-Q51 兜底分支 `hd_j16_node_feishui_result_effect`。
- 慕容令、王猛、苻丕、苻登、刘库仁、拓跋寔君、彭超都没有 PRE，本路不设。慕容令的建议 PRE 见第四节第 5 条。
- 苻融不进 tsv，由 Q51 处理。袁真是 X 特例。
- 没有发现 tsv 的 PRE 名与 TEMPLATE §5-15 不符的情况。

## 七、闸门（复跑，相对基线只列新增）
- 结果：**error 9，warn 46**。输出在 `D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p5-A1_gate.txt`
- 9 条 error 都能解释，与修正前同为 9 条：

| 类别 | 条数 | 变量 |
|---|---|---|
| 4-B 未落盘 | 3 | `hd_j16_yuanzhen_blamed`、`hd_j16_fangtou_done`、`hd_j16_huanwen_regent_result` |
| 与 5-A2 同批落盘 | 2 | `hd_j16_beifu_done`；`hd_j16_e4_370b_effect` 未定义 |
| 带参数变量名的误报 | 4 | `hd_nbc_liangyi_active`、`hd_nbc_xiangyang_active`、`hd_hi_started_murongchui`、`hd_nbc_death_lueyang_fu_021_done` |

- 46 条 warn 都是「只写不读」：各节点的记录变量（`_skip`、`_result`、`_go`、`_vassal` 等），以及等 F-1 来读的面板变量。比上次少 5 条，原因是 `jindao_settled` 等新变量都有读处。