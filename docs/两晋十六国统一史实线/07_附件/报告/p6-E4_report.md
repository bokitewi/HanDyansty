# p6-E4 最终报告（修正后合并版）

# p6-E4 修正报告（E4 补遗 386–394）

8 条 minor 已逐条处理：3 条改了代码或文案，其余 5 条写进本报告，或交汇总人决定。复跑闸门：error 4（都是已知误报），warn 27，比上次少 3。改动只在暂存区 p6-E4：没有直接写 mod，没有跑生成器，没有开游戏，没有提交 git，也没有改 tsv。

## 〇、审查意见逐条处理

**1. M50 变量语义与报告不同步（改报告）**
- M50 fire 时设的是 `hd_j16_yanwei_broken_result`，表示「交恶已 fire」。
- `hd_j16_yanwei_broken` 只作拓跋觚的卒年 PRE，而且只在觚确会进燕廷时才设。
- §三-12、§六 M50 行、「我设给别路的变量」表都已照此改正。

**2. 报告的行号与计数不准（改报告）**
- 本轮又改了代码，行号再次移动。下面全部用现文件的数：
  - PRE 行号：839、966、1311、1797；
  - 闸门 warn：27；
  - loc：中英各 63 键。
- 已补列工具 `hd_j16_e4b_war_key_effect`（效果文件第 90 行）。
- 已补列 M40「西燕之主是玩家」分支会给全体玩家发 5810 的 desc_player 新闻。

**3. X30 与 M40 的玩家分支（改代码，并补自拟）**
- X30：旧主是玩家时记 SKIP player_ruler，偏离 06 §0.1-5 的「逊位／拒之」两项。已补进自拟第 16 条，代码不变。
- M40：已改代码。
  - 新的判定是：慕容永已经是西燕之主，不论 AI 还是玩家，都 fire（不换主）；否则，两人都是 AI 时换主。
  - 「西燕之主是玩家且不是永」仍记 SKIP player_ruler，并发 desc_player 新闻。永已是君主的情形先被前一支截走，所以 desc_player 只会在旧主不是永时出现。
  - 执行体里，东进倾向修正和迁都长子只对 AI 永做；玩家永只得上党宣称。
  - fire 时先设 `_result`，5810 据此选正常文本，不会选到 desc_player。
  - 见自拟第 17 条。

**4. `_go` 只写不读，玩家选「伐」后可能被反复询问（改代码，交汇总人统一）**
- M55、T40、Y40 三个节点的玩家分支，在 `_asked` 判断之前加了一支：已有 `hd_j16_<x>_go` 时直接静默调 `*_war_effect` 重试，不再弹事件。
- 不会重复开战：战争效果自带「已 `_started` 或已 `_done` 即不开战」的判定。开战失败的日志仍只记一次（`_wsf_wlog`）。
- 3 条 `_go` warn 因此消失。
- 5-A1 的 liangyi 也有同样缺口，是否回移由汇总人定，见第五节第 3 条。

**5. core 的 E4 粗筛截止 400.1.1（交汇总人）**
已写成具体改法，见第五节第 4 条。

**6. 5840、5841、5880 文案点名写死（改文案）**
中英各改 6 个键，都只用触发事件时已保存的 scope：

| 键 | 改动 |
|---|---|
| `hd_j16.5840.t` | 进讨长子 → 进讨西燕 |
| `hd_j16.5840.desc` | 用 `[hd_j16_e4b_xy.GetName]`，不再写「慕容永在长子称帝」 |
| `hd_j16.5840.a` | 改为「进讨西燕」 |
| `hd_j16.5841.desc` | 用 `[hd_j16_e4b_yan.GetName]`；「目标直指长子」改为「矛头直指我境」 |
| `hd_j16.5880.desc` | 用 `[hd_j16_e4b_fd.GetName]`；「苻氏余部」改为「前秦余部」 |
| `hd_j16.5881.desc` | 用 `[hd_j16_e4b_hq.GetName]`，不再写「姚氏大军」 |

**7. 自建的两个修正文件，以及全局宣战倾向的副作用（交汇总人确认）**
见第五节第 2 条。

**8. tsv 两行缺 PRE（交汇总人）**
见第五节第 1 条。

## 一、暂存任务名与文件清单

暂存任务名为 **p6-E4**，暂存区在 `D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p6-E4\files\`。

**改动 1 个：**
- `common/scripted_effects/zz_hd_j16_e4_395_effects.txt`
  - 原文件是空入口，现在写入 12 个节点和本路工具。
  - 编码保持 UTF-8 带 BOM、LF。
  - 基线 sha256 与 mod 原文件一致。

**新建 6 个**（全部 UTF-8 带 BOM、LF，括号配平）：
- `events/zz_hd_j16_395e4_events.txt`：文件头写了 `namespace = hd_j16`，号段 5800–5899。
- `localization/simp_chinese/zz_hd_j16_395e4_l_simp_chinese.yml`、`localization/english/zz_hd_j16_395e4_l_english.yml`：中英各 63 键，一一对应。
- `common/scripted_triggers/zz_hd_j16_395e4_triggers.txt`
- `common/modifiers/zz_hd_j16_395e4_modifiers.txt`：本路自建，任务没有分配。
- `common/opinion_modifiers/zz_hd_j16_395e4_opinion_modifiers.txt`：本路自建，任务没有分配。

**命名：**
- 本路所有效果、触发器、scope 都带 `hd_j16_e4b_` 前缀，节点效果写成 `hd_j16_node_e4b_*`。
- 06 §0.2 的 `hd_j16_get_<线>_ruler_effect` 本路一个都没有定义，留给 N1、N2。

**本路工具：**
- `hd_j16_e4b_name_effect`：改国号。
- `hd_j16_e4b_style_effect`：改称谓。
- `hd_j16_e4b_court_effect`：收人入宫廷，并任议席。
- `hd_j16_e4b_war_key_effect`：开战后，把关键县挪进 wct 连通筛选改过之后的实际战争目标。优先用原关键县，其次用守方都城县，再其次用目标内守方一系持有的任一县。
- 按位置解析各方君主的 `hd_j16_e4b_get_*_effect`。

**复用的已落盘工具：**
- `hd_j16_304_res_effect`
- `hd_j16_b1_heir_effect`（立储）
- `hd_370_change_era_effect`（改元）
- `hd_370_take_realm_effect`（换主）
- `hd_nbc_become_independent_effect`
- `hd_nbc_start_war_effect`
- `hd_j16_n370_front_army_effect`（事件兵）
- `hd_j16_n370_to_court_effect`（入宫廷）
- `hd_world_news_send_all_effect`

## 二、节点一览

12 个节点都在入口 `hd_j16_e4_395_effect` 里调用，都用 TEMPLATE 骨架：
- `global_var:hd_j16_start_year >= 404` 时自保护，只设 done；
- 关窗日写成「止日次日」；
- 当事人已死时记 SKIP actor_dead；
- 等待日志只记一次（`_wlog`）。

| 节点 | 窗口 | 要点 |
|---|---|---|
| E4-M30 慕容垂称帝 | 385.12.1–388.1.1 | 条件：垂独立且有地；其一系据有中山县，或本人持冀州王冠。<br>执行：国号 `dynn_title_yan`、称谓 huangdi；独立时改元建兴；持有卢奴县时迁都；AI 立慕容宝为储。<br>玩家：5800 a/b。 |
| E4-M40 西燕易主 | 386.3.1–387.12.1 | 永已是西燕之主（AI 或玩家）→ fire，不换主。<br>永与旧主都是 AI → 永先独立，再经 `hd_370_take_realm_effect` 接收旧主的头衔与封臣。<br>西燕之主是玩家且不是永 → SKIP player_ruler，并以该玩家为 `hd_news_a` 给全体玩家发 5810 desc_player 新闻。<br>永是玩家、旧主是 AI → SKIP player_actor。<br>fire：上党宣称（玩家永也给）；永为 AI 时另给 3 年东进倾向修正，持有长子即迁都，否则在 395 年前每跳检查一次。5810 新闻发给全体玩家。 |
| E4-T30 改称魏王 | 386.1.1–388.1.1 | 执行：国号 `dynn_title_wei`、称谓 wang。<br>燕凤、张衮、长孙嵩、许谦入宫廷；珪是 AI 时依次任丞相、管家、元帅、间谍总管。<br>贺讷对珪好感 +20。<br>玩家：5850 a/b。 |
| E4-M45 燕魏通好 | 386.8.1–388.1.1 | 执行：双方各加 5 年修正（AI 宣战倾向 −0.5），并互相好感 +40。<br>玩家魏主：5820 a/b。 |
| E4-M50 燕魏交恶 | 391.7.1–393.1.1 | 条件：M45 已 fire；M45 了结但没有 fire 时记 SKIP deviated。<br>执行：设 `hd_j16_yanwei_broken_result`，撤去通好修正与好感，拓跋觚入燕主宫廷。<br>觚确会在燕廷时，才设 PRE `hd_j16_yanwei_broken`。 |
| E4-M55 灭西燕（KIND xiyan） | 393.11.1–395.6.1 | 开战：燕主得 1.2 万事件兵。<br>玩家燕主：5840；守方是玩家时收预警 5841。<br>玩家选「伐」后开战未成，会静默重试。 |
| E4-T40 破刘卫辰（KIND tiefu） | 391.7.1–393.1.1 | 开战：魏主得 1 万事件兵。<br>魏胜：设 `_won` 与 `_result`；勃勃入后秦主宫廷，后秦主不存在时入薛干郡持有者宫廷。<br>玩家：5860 进攻，5861 预警；选「伐」后静默重试。 |
| E4-Y30 姚苌称帝 | 386.3.1–388.1.1 | 执行：国号 `dynn_title_qin`、称谓 huangdi；独立时改元建初；持长安县时迁都；AI 立姚兴为储；尹纬任丞相。<br>玩家：5870 a/b。 |
| E4-Y40 废桥灭苻登（KIND feiqiao） | 393.12.1–395.6.1 | 开战：后秦主得 1 万事件兵。<br>玩家：5880 进攻，5881 预警；选「伐」后静默重试。 |
| E4-X30 乾归继立 | 388.3.1–389.6.1 | 执行：AI 之间换主；乾归本人已是君主时只改称谓；旧主是玩家时 SKIP；乾归是玩家时弹 5890。<br>称谓 wang。 |
| E4-X40 吕光称三河王 | 389.1.1–391.1.1 | 执行：称谓 wang、国号 houliang；独立时改元麟嘉；持姑臧县时迁都；AI 立吕绍为储。<br>玩家：5892 a/b。 |
| E4-X45 乾归称秦王 | 394.1.1–395.12.1 | 执行：国号 `dynn_title_xiqin`、称谓 wang。<br>玩家：5894 a/b。 |

三场战争照 5-A1 的 liangyi 写法：
- 开战成功才设 `_started`、保存攻守方与关键县（经 `war_key_effect` 落进实际目标）、生成事件兵；开战失败时 WAIT 一次，下一跳重试；
- 双方都已没有该 KIND 的战争时，关键县归攻方一系即判 `_won`，否则 `_lost`；了结时清掉 `hd_nbc_<KIND>_active`；
- 新 KIND 不进分发表。

## 三、自拟与偏差

1. **换主不杀旧主。** M40、X30 用 `hd_370_take_realm_effect`，不用 06 §0.4 的 `hd_nbc_seize_realm_effect`（偏离 06 §0.4）。
   - X30：乞伏公府是 412 年弑乾归的凶手，不能先死。
   - 先例：5-A1 的 Q70、Q80。
2. **称号节点只改名和称谓。** 不调 `hd_nbc_found_realm_effect`（它会把部落政体强转天朝）。国号键与 hd_hi 数据一致：yan、wei、qin、xiqin、houliang。
3. **T30、Y30、X30、X40、X45 在 06 表里写「无分支」，玩家当事人也给了 a/b 两项**，依据 06 §0.1-5。玩家选 b 时只设 `_skip`。
4. **M40 的两种玩家情形：**
   - 永是玩家、旧主是 AI：SKIP player_actor，不替玩家夺位。
   - 西燕之主是玩家且不是永：SKIP player_ruler，只发 desc_player 新闻。
5. **T40 要求刘卫辰是独立君主**，以免把他的宗主拖进战争。关键县取卫辰都城县，目标取其都城所在郡。
6. **M55 的目标：** 长子在西燕一系时打上党 `d_shangdang`（06 原文），否则打西燕都城所在郡。Y40 打秦余部之主的都城所在郡。三场战争开战后都经 `war_key_effect` 校正关键县。
7. **X40 同时定国号为后凉**（houliang），依据 A6-F10。
8. **尹纬「尚书令」落为丞相议席**（councillor_chancellor）。先例：3-B2 范长生。
9. **T30 的议席分派是自拟的**，只在珪是 AI 时任命。
10. **M45 用修正加好感，不用休战。** 代价：`ai_war_chance −0.5` 对燕魏两国所有对外战争都生效。慕容麟「入魏主营 90 天」没有做。
11. **M30 没有检查「称谓尚非帝」。** 已是帝时照样执行，结果相同。
12. **M45、M50 的变量拆分：**
    - done 名另起：`hd_j16_yanwei_peace_done`、`hd_j16_yanwei_broken_done`。
    - `hd_j16_yanwei_peace`：M45 fire 时设，同时是窟咄的卒年 PRE。
    - M50 fire 的标志是 `hd_j16_yanwei_broken_result`。
    - `hd_j16_yanwei_broken` 只作拓跋觚的卒年 PRE，有条件地设：只在觚已是燕主廷臣，或满足入宫廷的全部前提（AI、在世、无地、非统治者、未被囚、非议员，燕主在世有地）时才设。下游判交恶不要读它。
13. **5810 新闻发送：** M40 fire 时发正常版；「西燕之主是玩家」分支发 desc_player 版。两者都发给全体玩家。
14. **X45 的变量名是自拟的**：`hd_j16_xiqin_wang_*`。
15. **燕主、西燕之主按位置解析，两者必须不是同一人**（都属 `dynasty:murong`）。
16. **X30 旧主是玩家时直接 SKIP player_ruler**，不给 06 §0.1-5 规定的「逊位／拒之」两项。理由同 M40：不夺玩家头衔，乾归在玩家朝中照常做臣子。（审查补列）
17. **M40 永本人是玩家且已是西燕之主时照常 fire。**（本轮修正）
    - 给上党宣称：这是 06 原文给 fire 的内容，属 06 §0.4 允许的软加强（宣称不开战、不给兵）。
    - 不加 AI 东进倾向修正，不替玩家迁都。
18. **玩家选「伐」后静默重试**（本轮修正）：节点玩家分支先判 `_go`，成立就静默调战争效果，不再弹询问事件。与 5-A1 liangyi 现写法不同，见第五节第 3 条。

## 四、本期面板行清单（交 F-1）

本期无面板行：06 §4.4 没有给 E4 补遗分配，本路也没有设置 `hd_hev_*`。如果 F-1 想加，可以考虑以下几行：

| 候选行 | 可读的变量 |
|---|---|
| 燕称帝 | `hd_j16_houyan_di_result` |
| 后秦称帝 | `hd_j16_houqin_di_result` |
| 灭西燕 | `hd_j16_xiyan_won` |
| 废桥之战 | `hd_j16_fudeng_end_won` |
| 燕魏交恶 | `hd_j16_yanwei_broken_result` |

要加的话由汇总人另定。

## 五、需要汇总人处理的事项

1. **tsv 补 PRE**（本路不改 tsv）：
   - 慕容永 `changli_murong_064`：补 `hd_j16_xiyan_won`。
   - 苻登 `linwei_fu_0050`：补 `hd_j16_fudeng_end_won`。
   - 补后需重跑 gen_deaths_effects。不补的话，即使西燕没灭、苻登没败，两人也会按日期被杀。
2. **确认两个自建修正文件**：
   - `common/modifiers/zz_hd_j16_395e4_modifiers.txt`
   - `common/opinion_modifiers/zz_hd_j16_395e4_opinion_modifiers.txt`

   另请确认 `hd_j16_yanwei_peace_modifier`（`ai_war_chance −0.5`）对燕魏所有对外战争都生效这一副作用。
3. **`_go` 写法统一**：本路已改成静默重试（自拟第 18 条）。5-A1 liangyi 有同样的缺口：选项 a 先删 `_asked`，开战失败后会再弹询问。是否回移由汇总人定。
4. **core 的 E4 粗筛截止 400.1.1**：`zz_hd_j16_core_effects.txt` 中 `hd_j16_pulse_effect` 的 E4 粗筛（约 :101-113）在 400 年以后不再执行。
   - 后果：M55、T40、Y40 如果拖过 400 年，结局不再判定，`_done`、`_won` 不设，`hd_nbc_<KIND>_active` 也不清。
   - 建议仿照 E3 的先例（汇总人 10-27 回归 minor-1），在 E4 粗筛的 OR 里补三条：`AND = { has_global_variable = hd_j16_<x>_started NOT = { has_global_variable = hd_j16_<x>_done } }`，x = xiyan、tiefu、fudeng_end。
5. **不需要重跑生成器。** 本路没有新建人物，也没有改 tsv。

## 六、新增事件号与变量名

**事件号：** hd_j16.5800、5810、5820、5840、5841、5850、5860、5861、5870、5880、5881、5890、5892、5894。

**全局变量**（各节点都有 `_done`、`_skip`、`_wlog`，下表列出其余）：

| 节点 | 变量 |
|---|---|
| M30 | `hd_j16_houyan_di_*`，含 `_result` |
| M40 | `hd_j16_xiyan_yong_*`，含 `_result`、`_moved` |
| T30 | `hd_j16_wei_wang_*`，含 `_result` |
| M45 | done 为 `hd_j16_yanwei_peace_done`；fire 设 `hd_j16_yanwei_peace`（兼卒年 PRE）；另有 `_skip`、`_wlog`、`_yan`、`_wei` |
| M50 | done 为 `hd_j16_yanwei_broken_done`；fire 标志 `hd_j16_yanwei_broken_result`；`hd_j16_yanwei_broken` 只作卒年 PRE、有条件设置；另有 `_skip`、`_wlog` |
| M55 | `hd_j16_xiyan_*`，含 `_started`、`_won`、`_lost`、`_att`、`_def`、`_key`、`_go`、`_wait`、`_asked`、`_wsf_wlog` |
| T40 | `hd_j16_tiefu_*`，同 M55 一组，另加 `_result` |
| Y30 | `hd_j16_houqin_di_*`，含 `_result` |
| Y40 | `hd_j16_fudeng_end_*`，同 M55 一组 |
| X30 | `hd_j16_qiangui_*`，含 `_result` |
| X40 | `hd_j16_lvguang_wang_*`，含 `_result` |
| X45 | `hd_j16_xiqin_wang_*`，含 `_result` |

**其他新名字：**
- 修正：`hd_j16_yanwei_peace_modifier`、`hd_j16_xiyan_dongjin_modifier`
- 好感修正：`hd_j16_yanwei_peace_opinion`、`hd_j16_helan_support_opinion`
- 事件兵名字键：`hd_j16_e4b_army_xiyan_name`、`_tiefu_name`、`_feiqiao_name`
- 新 KIND：`xiyan`、`tiefu`、`feiqiao`

**06 写法 → 实际变量名对照：**
- 06 只给了 done 名，`_result`、`_won` 等按 08 §5 补全。
- `hd_j16_yanwei_peace`：拆成 `_done`（防重入）加原名（fire 时设，兼 PRE）。
- `hd_j16_yanwei_broken`：拆成 `_done`、`_result`（fire 标志）加原名（只作 PRE、有条件设）。
- `hd_j16_tiefu_done`：06 原写「魏胜时设」，现改为了结即设；胜负看 `_won` 和 `_result`。
- `hd_j16_fudeng_end_*`：沿用 06 原名，与 A4 的 `hd_j16_fudeng_done` 不同名。
- X45：新起 `hd_j16_xiqin_wang_*`。

**我设给别路的变量（交汇总人对账）：**

| 变量 | 含义 | 读者（06） |
|---|---|---|
| `hd_j16_xiyan_done` | 灭西燕已了结 | 6-N1 E5-M10 |
| `hd_j16_xiyan_won` | 燕胜 | 慕容永卒年（建议补 PRE） |
| `hd_j16_houyan_di_done` / `_result` | 燕称帝 | E5-M10 等下游 |
| `hd_j16_yanwei_broken_done` / `hd_j16_yanwei_broken_result` | 交恶已了结 / 已 fire | E5-M10 等下游 |
| `hd_j16_yanwei_broken` | 仅拓跋觚卒年 PRE（觚确在燕廷才设），**不得用来判交恶** | 卒年生成物 |
| `hd_j16_yanwei_peace_done` / `hd_j16_yanwei_peace` | 通好已了结 / 已 fire（兼窟咄 PRE） | 下游 |
| `hd_j16_tiefu_done` / `_won` / `_result` | 破铁弗已了结 / 魏胜 | 6-N2 E5-X26 |
| `hd_j16_lvguang_wang_done` / `_result` | 吕光称王 | 6-N2 E5-X10、X14、X18 |
| `hd_j16_qiangui_done` / `_result` | 乾归继立 | 6-N2 |
| `hd_j16_xiqin_wang_done` / `_result` | 乾归称秦王（名字自拟） | E5-Y20（6-N1）及 6-N2 西秦线 |
| `hd_j16_houqin_di_done` / `_result` | 姚苌称帝 | 6-N1 后秦线 |
| `hd_j16_fudeng_end_done` / `_won` | 苻登了结 / 后秦胜 | 苻登卒年（建议补 PRE） |
| `hd_j16_wei_wang_done` / `_result` | 魏王 | 6-N1 北魏线 |

审查已核对：N1 读 `hd_j16_xiyan_done`，N2 读 `hd_j16_tiefu_done` 与 `hd_j16_lvguang_wang_done`，变量名都对得上；N1、N2 目前都不读 `hd_j16_yanwei_broken`。

**我读别路的变量：** 本期其他四路的变量一个都不读。只读第 5 期已落盘的：
- `hd_j16_start_year`
- `hd_j16_fudeng_done`（A4 E4-Q80）
- `hd_j16_qin_title`（E4-W50）
- `hd_hi_started_murongchong`、`hd_hi_started_tuobagui`（p5-C）
- `hd_nbc_<KIND>_active`（`hd_nbc_start_war_effect` 设置）

## 七、卒年表 PRE 的设置位置（现文件行号）

tsv 第 8 列里归本路节点的 PRE 共 4 个。都只在 fire 时设；跳过、前标、玩家选 b 时都不设；名字与 TEMPLATE §5-15 一致，tsv 不需要改名。

| PRE | 卒年行 | 设置位置 |
|---|---|---|
| `hd_j16_yanwei_peace` | 拓跋窟咄 `tuoba_039` | `zz_hd_j16_e4_395_effects.txt:839`（M45 执行体：AI 由节点调，玩家在 5820 a 调） |
| `hd_j16_yanwei_broken` | 拓跋觚 `1415139` | 同文件 `:966`（M50 fire 分支，只在觚确会进燕廷时设） |
| `hd_j16_tiefu_result` | 刘卫辰 `xiongnu_liu_018`（die 类） | 同文件 `:1311`（T40 结局，魏胜时与 `_won` 一起设） |
| `hd_j16_lvguang_wang_result` | 杜进 `hd_j16_du_jin` | 同文件 `:1797`（X40 执行体：AI 由节点调，玩家在 5892 a 调） |

本路节点不直接杀任何人。慕容永、苻登、苻崇、杨定、慕容冲按 tsv 照常执行（前两人建议补 PRE，见第五节第 1 条）。

## 八、闸门（本轮复跑）

运行命令照任务给的 `--overlay p6-E4 --compare baseline.json --only-changed`，输出在 `D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p6-E4_gate.txt`。

**error 4 条，都是误报，与审查结论一致：**
- `hd_hi_started_tuobagui`：由 `zz_hd_hi_effects.txt:14` 以 `hd_hi_started_$KEY$` 拼名设置，闸门跳过了参数拼名。
- `hd_nbc_xiyan_active`、`hd_nbc_tiefu_active`、`hd_nbc_feiqiao_active`：由 `hd_nbc_start_war_effect` 以 `hd_nbc_$KIND$_active` 设置，属 TEMPLATE §5-14 列出的误报。

**warn 27 条**（上次 30）：节点现在会读 `_go`，3 条 `_go` warn 已消失。其余都是只写不读：
- 各节点的 `_skip`、`_result`、`_won`、`_lost` 等记录变量，或别路、面板才读的变量；
- PRE 变量（卒年生成物用宏参数读它们，闸门看不到）。

有效果的 on_action 数仍为 6721。7 个文件括号都配平；中英 loc 各 63 键。

## 九、回归（08 §10）

- 404 开局：本路 12 个节点全部只做自保护前标，只设 done。
- 本路没有改动 H 线、永嘉、入侵文件、核心心跳、开局文件，也没有改 `hd_nbc_war_result_effect` 分发表。新战争走 `hd_nbc_war_cb`，在 D24 豁免内。
- 因此 R1–R7 不受影响，其中 R5 永嘉、R7 404 H 线照旧。
- 写法上：国号键与入侵数据一致，慕容统一写 `dynasty:murong`（R6）。

## 十、仍未解决项

都需汇总人决定，本路无权改：
1. tsv 是否给慕容永、苻登补 PRE。
2. 自建修正文件，以及全局宣战倾向的副作用。
3. `_go` 写法是否回移到 5-A1。
4. core 的 E4 粗筛是否延长。