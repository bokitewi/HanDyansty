# p6-N2 最终报告（修正后合并版）

# p6-N2 修正报告：北线 · 夏、西秦、后凉、南凉、北凉、西凉、柔然（E5）

本轮只改了暂存区，涉及 effects、triggers 两个文件。没有直接写 mod，没有跑生成器，没有开游戏，没有提交 git。
改完复跑闸门，两份文件仍是 UTF-8 带 BOM、LF，花括号配平（effects 1304/1304，triggers 64/64）。

## 〇、逐条处理结果

### 1. major：报告与代码脱节 —— 已修
本报告按现有暂存文件重出，第一至十二节全部更新：
- X60 已补进报告，事件 28 个、中英各 120 键、节点 22 个；
- 闸门用本次复跑的数字；
- 跨路对账两张表按 grep 实况重写；
- PRE 行号按最终文件现取；
- 删去已完成的「6-S 加入口」和「6-B 预设 tufawugu」两项；
- 第四节第 10、20 条按代码实况改写。

### 2. major：X60 缺「南凉曾立」前提 —— 已修
- **新触发器** `hd_j16_n2_nanliang_founded_trigger`（triggers 第 112–122 行），条件为二者满足其一：
  - `global_var:hd_j16_start_year >= 404`；
  - `has_global_variable = hd_hi_started_tufawugu`（入侵真正起过兵，由 p5-C 的 `hd_hi_begin_effect` 设）。
- **用在两处**：X60 开始执行的 else_if（effects 第 1992 行），以及执行体 `hd_j16_nanliang_restore_exec_effect` 开头（第 2048 行，防玩家迟选 5720 a）。
- **不满足时**：节点整窗等待（记一次 WAIT not_ready），到期跳过。
- **「已成」支不加此前提**：该支只在傉檀本已独立有地时设 done/_result，不改动任何东西。
- **与审查建议的偏离**：没有把 `hd_j16_nanliang_result` 放进 OR。X14 在 try_start 之前就设了它，它只表示「开过闸」，不表示「起过兵」。规则关闭或首领自弃时它也为真，放进去会重开凭空立国的漏洞。

### 3. minor：授郡改投没查主君等级 —— 已修，三层
- **节点 ready 条件**：
  - X22 加 `scope:hd_j16_x22_lg ?= { highest_held_title_tier > tier_duchy }`；
  - X26 加 `scope:hd_j16_x26_qin ?= { … > tier_duchy }`。
  - 原因：X22、X26 都是先设 done 再调执行体，只在 grant 里写 WAIT 不会有下一跳。
- **X22 选主君**：`hd_j16_ligao_dunhuang_sides_effect` 在两支（北凉、后凉）里各自要求候选主君高于郡级。北凉之主只有郡级时落到后凉支，不会整窗干等。
- **grant 本体**（`hd_j16_n2_grant_duchy_effect`，玩家迟复的兜底）：
  - `$LIEGE$` 最高头衔 ≤ 郡级时不授，记 `WAIT liege_tier_low`；
  - swear 之后复核 `liege ?= $LIEGE$`，不成立记 `WARN fealty_failed`。

### 4. minor：wct 改目标后关键县不在战争目标里 —— 已修，照 E4 先例
- **新工具** `hd_j16_n2_war_key_effect`（effects 第 413 行）：从 p6-E4 的 `hd_j16_e4b_war_key_effect` 原样内联，scope 与日志改成本路前缀，不跨路调用。
- **X66、X82**：
  - 开战前把原定关键县存成 scope（`hd_j16_x66_key` = 姑臧 `c_uuii_p_1564`，`hd_j16_x82_key` = 白土 `c_baitu`）；
  - 开战成功后调 war_key，再存全局 `hd_j16_guzang_key` / `hd_j16_ledu_key`；
  - 事件兵改投到关键县所在郡；
  - 结局改判：实际关键县归攻方一系，或原关键县（姑臧、白土）归攻方一系，都算胜。
- **X90**：
  - 关键县（西凉都城县）先存成 scope `hd_j16_x90_key`，开战后经 war_key 处理，再存 `hd_j16_xiliang_end_key`；
  - 事件兵改投到该县所在郡。
- **语义自拟**（见第四节第 21 条）：
  - X66 的面板 `hd_hev_j16_guzang_juqu` 只在姑臧实际归北凉一系时设；
  - X82 打赢替换后的关键县，也算「南凉被灭」，设傉檀 PRE。

### 5. minor：opinion_modifiers 新文件 —— 不改代码，交汇总人确认
不放行时有两个替代方案（见第六节第 3 条）：
- 改用人物修正：段业的名义加成已有 `hd_j16_duanye_mingyi_modifier`，把 −20 好感并进去；
- 西凉通好改用原版 `friendly_opinion` 一类现有键。

## 一、暂存任务名与文件
- 任务名：**p6-N2**。暂存目录：`D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p6-N2\files\`
- 共 7 个文件，全部新建（stage new），UTF-8 带 BOM、LF，花括号配平：
  - `common/scripted_effects/zz_hd_j16_395n2_effects.txt`：入口 `hd_j16_e5_395n2_effect`、22 个节点（含自拟 X60）、本路工具（含新增 `hd_j16_n2_war_key_effect`）。
  - `common/scripted_triggers/zz_hd_j16_395n2_triggers.txt`：含新增 `hd_j16_n2_nanliang_founded_trigger`。
  - `events/zz_hd_j16_395n2_events.txt`：`namespace = hd_j16`，28 个事件。
  - `common/modifiers/zz_hd_j16_395n2_modifiers.txt`
  - `common/opinion_modifiers/zz_hd_j16_395n2_opinion_modifiers.txt`：**不在任务列给本路的文件清单内**，按自拟新建，待汇总人确认（第六节第 3 条）。
  - `localization/simp_chinese/zz_hd_j16_395n2_l_simp_chinese.yml`、`localization/english/zz_hd_j16_395n2_l_english.yml`：中英各 120 键，一一对应。
- 没有改任何现有文件，也没有写别路的文件。
- 范围：
  - 06 §1.5：X26、X58、X78、X86；
  - 06 §1.6：X10、X14、X18、X22、X30、X34、X38、X42、X46、X54、X62、X66、X74、X82、X90；
  - 06 §1.7：X50、X70；
  - 自拟补节点 X60（傉檀叛秦·复称凉王）；
  - 共 22 个节点，另含 §3.2、§3.3 中归这几国的开闸与闸门。

## 二、闸门结果

**单路**（命令按任务给定参数，输出 `D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p6-N2_gate.txt`）

相对基线新增 **error 10、warn 51**，resolved_vs_baseline = 11。比审查那次多 1 条 error，就是新增前提读的 `hd_hi_started_tufawugu`。10 条 error 全部能解释：

| 变量 | 原因 |
|---|---|
| `hd_j16_lvguang_wang_done`、`hd_j16_tiefu_done` | 6-E4 设（p6-E4 effects 第 1742、1174 行），单路跑时没有对方文件 |
| `hd_j16_qifu_done`、`hd_j16_guzang_tufa_done` | 6-N1 设（p6-N1 effects 第 3204、3793 行），同上 |
| `hd_j16_houqin_won`、`hd_j16_houqin_lost` | 6-S 的 J80 设（p6-S e5_395 第 2574、2582 行），同上 |
| `hd_nbc_guzang_active`、`hd_nbc_ledu_active`、`hd_nbc_xiliang_active` | `hd_nbc_start_war_effect` 以 `hd_nbc_$KIND$_active` 设，参数拼名误报（TEMPLATE §5-14） |
| `hd_hi_started_tufawugu` | p5-C `hd_hi_begin_effect` 以 `hd_hi_started_$KEY$` 设，参数拼名误报，同 p5-C 报告第 209 行先例 |

**五路合跑**（`--overlay p6-N2 p6-N1 p6-E4 p6-S p6-B`，输出 `D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p6-N2_fix_all5.txt`）

本路只剩 4 条参数拼名误报：3 条 `_active`，加 `hd_hi_started_tufawugu`。跨路读的变量全部对上。

**51 条 warn** 都是「只写不读」，包括：
- 各节点的 `_skip`、`_result`、`_won`、`_lost`、`_go`；
- 面板变量（等 F-1 读）；
- 经 `$PRE$` 参数被卒年表读取的 PRE 结果变量（闸门不认参数）。

新增的 `hd_j16_guzang_key`、`hd_j16_ledu_key` 本路自写自读，不报。

## 三、实现要点

1. **立国一律靠入侵（A6-F1）。**
   - X14、X18、X58 的开闸顺序：先设 `hd_j16_hi_go_<KEY>`，再调 p5-C 的 `hd_hi_try_start_<KEY>_effect`（只调用，不重定义）。
   - 窗口末仍不满足时，同样设 go，另设 `_late`，再 try_start（不短路），然后设 done 与 `_skip`。当跳没起成的，由年度 on_action 补试。
   - 称西平王、推段业、建夏风味这些后续动作，都写成「首领已独立、已起兵」之后的子步，不与 try_start 同跳。
   - 任何一步都不建王国、不抬头衔等级，只改 `hd_nbc_style` 和国号，避免 hd_hi.0200 选项 d 让首领自弃。
   - X60 只让「曾立过的南凉」复国，前提见第〇节第 2 条。
2. **闸门。**
   - X50 设 `hd_j16_hi_gate_shelun_3`：fire、窗口末、社仑已死、404 前标四种情况都设，后三种记 `SKIP gate_opened`。
   - X86 设 `hd_j16_hi_gate_helianbobo_3`：闸门块放在 done 判断之外，按位置判定条件成立即设；窗口末或勃勃已死时照设。
3. **换主一律不杀人。** 06 §0.4 的 `hd_nbc_seize_realm_effect` 会杀旧主，本路不用。
   - 节点 fire 时设 PRE，由卒年表按日期处死；当事人死后，再用 `hd_j16_n2_take_realm_effect` 转移政权。新主若是有地封臣，先独立；旧主留作廷臣。
   - 共用的继统一步效果 `hd_j16_n2_succ_step_effect` 用于 X30（两步）、X34、X42 次步、X70（两步）、X74。
   - 现任是玩家时弹「逊位 / 拒之」。
4. **战争节点 X66、X82、X90** 照 E4-Q20 的写法：
   - 开战成功才设 `_started`、存攻守方和关键县（经 war_key 处理）、给 1 万事件兵；失败下一跳重试。
   - 玩家攻方用 `_asked`（60 天）/ `_go` / `_wait`（90 天）；玩家守方收预警。
   - 新 KIND 按关键县归属自判，并自清 `_active`，不进分发表。
5. 所有当事人都经 `hd_j16_resolve_effect` 解析；判断已死只用 `hd_j16_dead_trigger`；不用 `every_living_character`；接壤判定只在窗口内调用。

## 四、自拟与偏差
1. **工具与按位置取人效果加 `hd_j16_n2_` 前缀**，没有占用 06 §0.2 的 `hd_j16_get_<线>_ruler_effect` 原名。
   - 原因：6-N1 也要取西秦、后凉、后秦之主，两路各自定义会互相覆盖。
   - 本路 getter：`hd_j16_n2_get_{houqin,xiqin,houliang,nanliang,beiliang,xiliang,xia,rouran}_ruler_effect`，取法先人后地。
2. **换主不杀人**（见三-3）。照 p5-A1 的 `hd_370_take_realm_effect` 先例，另加「新主先独立」，没有采用 06 §0.4 的 `hd_nbc_seize_realm_effect`。
3. **入侵立国的政权**（后凉、南凉、北凉、西秦、夏）改国号、称谓用 `hd_j16_n2_style_effect`，不用 `hd_nbc_found_realm_effect`，因为后者会把政体改成 celestial，冲掉入侵设的 tribal 或 nomad。
   - 主头衔须郡级以上才改，免得把县改名。
   - FIXED = yes 只给吕、秃发、沮渠、乞伏四家。
   - 西凉（汉人李氏）照用 found_realm，FIXED = no。
   - 夏称帝 FIXED = no，因为勃勃 413 年以前仍挂匈奴刘氏。
4. **跨路上游一律不阻塞**：上游 done 已设，或已过上游窗口止日。
5. **X26**：勃勃已有地时设 done，记 `SKIP already_landed`，不设结果（06 写「已有县时不授」）。
6. **X58**：条件在 06 两支之外，放宽为「勃勃本人已独立有地」也算。
   - 子步以勃勃的入侵故事处于 `hd_hi_phase = rising` 为「确已起兵」的判据，然后才设没弈干的 PRE、面板与骑兵修正。
   - 自弃或蛰伏时都不设。
7. **X62**：加「已成」支。乾归本就独立有地时，直接设 done 和 `_result`。
   - 依据是 tsv 乾归行备注，前置本意是「X62 已 fire 或乾归独立」。
   - 不加这一支，304/346/370 局里乾归从未降秦，就永远不会被公府所杀，X74 也会断链。
8. **X66、X82**：开窗时若姑臧或白土已在攻方一系，直接按胜处理（善后、PRE、面板）。X66 另要求开战时姑臧在南凉一系（06 只写「姑臧不归北凉」），否则目标落空。
9. **X74**：没有独立的西秦之主时一直等到关窗，不另认「炽磐以封臣身份继承」。
10. **X86 闸门**（已按代码实况改写）：`hd_j16_n2_xia_gate_ready_trigger` 要求同时满足三条：
    - 长安 `c_uuii_p_867` 的 top_liege 不是姚氏；
    - 没有 `hd_nbc_houqin_active`；
    - 下列二者其一：读 6-S J80 的 `hd_j16_houqin_won` / `hd_j16_houqin_lost`（已对账存在），或后秦之主（按位置）已不存在。
11. **X90 变量撞名**：X38 已占 `hd_j16_xiliang_done`。X90 的 KIND 也叫 xiliang，所以它的 done/won/lost 改用 06 原名 `hd_j16_xiliang_end_*`；`_started` 照 tsv 的 PRE 名保留为 `hd_j16_xiliang_started`。
    - 目标取西凉都城县所在的郡（`capital_county.de_jure_liege`），关键县初值即该都城县，开战后经 war_key 处理。
12. **X42 拆两步。** 首步在吕纂（AI）在位时设 PRE；次步在吕纂死后换主给吕隆。玩家吕纂另收 5681：a 逊位于吕隆，当场换主，不设 PRE（人不死）；b 拒之。
13. **X50**：`hd_nbc_style` 没有「可汗」，没有自造旗标，改为「丘豆伐可汗」修正（10 年）加威望 300。曷多汗 `yujiulu_07` 已并入 `he_duo_han`（394 年卒），不用。
14. **X54**：06 写「互加 10 年 AI 不宣战倾向」，改为互加 10 年 +30 好感 `hd_j16_xiliang_tonghao_opinion`（新建 opinion_modifiers 文件）。
15. **X18 子步**：段业入宫廷、任首席议政（councillor_chancellor），加修正，蒙逊对他好感 −20。只在段业是 AI 且无地时执行。
16. **补玩家事件**：X10、X22、X26、X38、X46、X50、X54、X60、X62、X78、X86 在 06 中写「无分支」或只写了 AI（X60 为自拟）。按 06 §0.1-5 与 A1 §7.3（当事人是玩家时一律给选项），各补了「a 史实 / b 拒绝」玩家事件。X14、X18、X58 的起兵选择仍由入侵事件 hd_hi.0200 负责，不另发事件。
17. **AI 现任把位子交给玩家继任者时，不另询问玩家继任者**（这本是继统）。
18. **窗口止日一律写「>= 止日次日」。** 例外：
    - X90 写 `>= 421.1.1`，因为心跳在当日停；
    - 子步与宽限（都是自拟）：X42 次步宽限到 402.6.2，X14 子步止于 401.1.1，X18 子步止于 399.1.1，X58 子步止于 410.1.1。
19. **称号键**：西平王、河西王、天王、夏帝只设称谓旗标。国号用 p5-C 已建的 `dynn_title_houliang`、`_nanliang`、`_beiliang`、`_xiqin`、`_xiliang` 和原版的 `dynn_title_xia`。「河西王」没有另建称号键。
20. **迁都**（已按代码实况改写）：
    - X54（酒泉 `c_uuii_p_5792`）、X78（统万 `c_uuii_p_1434`，肤施代统万）走 `hd_j16_n2_move_capital_effect`：
      - 君主本人直辖时直接迁；
      - 由一系内 AI 持有时，先把这 1 县小幅转给君主（granted，不加宣称，A1 §7.1）再迁；
      - 持有者是玩家或转移不成时不迁，记 `SKIP capital_kept`。
    - X14 子步迁白土（`c_baitu` 代乐都）、X66 善后迁姑臧（`c_uuii_p_1564`），只在君主本人直辖时迁。
21. **（本轮新增）战争关键县语义。**
    - 三场战争经 `hd_j16_n2_war_key_effect`（照 E4 内联）把关键县落进实际目标；新变量 `hd_j16_guzang_key`、`hd_j16_ledu_key`（X90 沿用 `hd_j16_xiliang_end_key`）。
    - X66 打赢替换后的关键县也判胜，设 `_won` 与 `hd_j16_guzang_juqu_result`、做善后；但面板 `hd_hev_j16_guzang_juqu` 只在姑臧实际归北凉一系时设。
    - X82 打赢替换后的关键县也判胜，照设傉檀卒年 PRE `hd_j16_nanliang_end_result`。
22. **（本轮新增）授郡主君等级。** X22、X26 授郡要求改投的主君最高头衔高于郡级：
    - X22 北凉之主不够格时改认后凉之主，都不够格就等待；
    - grant 本体兜底，记 `WAIT liege_tier_low`；改投失败记 `WARN fealty_failed`。
23. **（本轮新增）自拟补节点 E5-X60「傉檀叛秦·复称凉王」，06 无此节点，交汇总人确认。**
    - 窗口 408.6.1–409.12.1（>= 409.12.2 关窗），史实为 408.11。
    - 上游 Y40（`hd_j16_guzang_tufa_done`，6-N1）不阻塞：或 >= 407.6.2。
    - 已成：傉檀本已独立有地时设 done、_result。
    - 前提「南凉曾立」：404 开局，或 `hd_hi_started_tufawugu`。
    - 条件：傉檀有地、是后秦主一系的封臣。
    - 执行：AI 直接 `hd_nbc_become_independent_effect`，国号南凉、称谓 wang、FIXED = yes，不改政体；玩家收 5720（a 复称凉王 / b 仍为秦臣）。
    - 不设 PRE。
    - 补此节点的原因：404 开局傉檀是后秦 `e_bingliang` 的封臣，X66、X82 要求南凉之主独立，不补则两节点在 404 局整窗落空。
    - 非 404 局里入侵未起兵时，本节点整窗等待、到期跳过。
    - 前提有意不认 `hd_j16_nanliang_result`（理由见第〇节第 2 条）。

## 五、已知局限（不修，交汇总人知悉）
1. **X90 撞上 421.1.1 的心跳截止。** 战争若在截止后才结束，没有人判结局，`hd_nbc_xiliang_active` 也不会清（A6-F14 交 AI）。
2. **X42、X46、X74 依赖卒年表**按 PRE 处死当事人后才能推进。凶手取不到时按 D15 顺延，下游节点会等到关窗。
3. **wct 替换关键县后**，X66 判胜不等于得到姑臧，X82 判胜不等于得到白土（语义见第四节第 21 条）。都取不到守方县时，仍用原关键县判，与旧局限相同。
4. **304/346/370 局入侵 tufawugu 若从未起兵**，南凉没有立过，X60、X66、X82 都会整窗等待、到期跳过。这是有意为之（D2）。

## 六、需要汇总人处理的事项
1. **getter 合并**：见第四节第 1 条。本路 `hd_j16_n2_get_*` 与 6-N1 的同类定义合并，或二选一。
2. **「可汗」称谓**：若要显示，需在 `common/customizable_localization/WJ_native_province_pilot.txt` 加一个 style 旗标，不归本路。
3. **opinion_modifiers 新文件**（`common/opinion_modifiers/zz_hd_j16_395n2_opinion_modifiers.txt`，含 `hd_j16_duanye_nominal_opinion`、`hd_j16_xiliang_tonghao_opinion`）：请确认放行。不放行时，前者并入人物修正 `hd_j16_duanye_mingyi_modifier`，后者改用现有 opinion 键。
4. **自拟节点 E5-X60 请确认**（第四节第 23 条）。不认可时，删掉入口第 27 行调用、节点与 5720 事件、4 个本地化键即可。此后 404 局 X66、X82 回到「整窗落空」。
5. 不需要重跑生成器。本路没有新建人物，没有改 tsv。

已落实、不再列入：6-S 已在 `hd_j16_e5_395_effect` 第 36 行调用 `hd_j16_e5_395n2_effect = yes`；6-B 已在 startup_404 第 15 行预设 `hd_hi_done_tufawugu`。

## 七、本期面板行清单（交 F-1，只列不写；06 §4.4）
| 行 | 变量 | 设置处 | 适用 |
|---|---|---|---|
| 夏建国 | `hd_hev_j16_xia_open` | E5-X58 子步（确已起兵时），`hd_j16_xia_open_exec_effect`（effects 第 1921 行） | le404 |
| 北凉入姑臧 | `hd_hev_j16_guzang_juqu` | E5-X66 战胜或已成、且姑臧实归北凉一系时，`hd_j16_guzang_won_effect` | le404 |

组为 `hd_hev_grp_j16_e5`，只在 fire 时设，前标与跳过都不设。

## 八、新增事件号
共 28 个：
- 称号、授郡、自立类：hd_j16.5600（X10）、5610（X14 子步）、5620（X18 子步）、5630（X22）、5640（X26）、5670（X38）、5690（X46）、5700（X50）、5710（X54）、**5720（X60）**、5730（X62）、5770（X78）、5790（X86）
- 逊位类：5650、5651（X30）、5660（X34）、5680、5681（X42）、5750、5751（X70）、5760（X74）
- 战争类：5740 出兵 / 5741 预警 / 5742 善后（X66）；5780 / 5781（X82）；5795 / 5796（X90）

5600–5799 段内其余号未占。

## 九、变量名
**节点 done**（06 有名的照用）：
- `hd_j16_lvguang_tianwang_done`（X10）、`hd_j16_nanliang_done`（X14）、`hd_j16_duanye_done`（X18）
- `hd_j16_ligao_dunhuang`（X22，06 原名，不带 `_done`）、`hd_j16_bobo_shuofang`（X26，同上）
- `hd_j16_rulugu_done` 与 `hd_j16_rutan_done`（X30，后者兼作整体 done）、`hd_j16_lvzuan_done`（X34）、`hd_j16_xiliang_done`（X38）、`hd_j16_lvlong_done`（X42）、`hd_j16_mengxun_king_done`（X46）
- `hd_j16_rouran_khagan_done`（X50）、`hd_j16_xiliang_jiuquan_done`（X54，自拟）、`hd_j16_xia_open_done`（X58）、**`hd_j16_nanliang_restore_done`（X60，自拟）**、`hd_j16_xiqin_restore_done`（X62）、`hd_j16_guzang_juqu_done`（X66）
- `hd_j16_hulv_done` 与 `hd_j16_datan_done`（X70）、`hd_j16_chipan_done`（X74）、`hd_j16_tongwan_done`（X78）、`hd_j16_nanliang_end_done`（X82）、`hd_j16_xia_changan_done`（X86）、`hd_j16_xiliang_end_done`（X90）

**各节点另有** `_result`、`_skip`、`_wlog`，X60 同样有 `hd_j16_nanliang_restore_result/_skip/_wlog`。

**子步与内部变量**：
- 子步：`hd_j16_nanliang_wang_done/_result`、`hd_j16_duanye_tui_done/_result`、`hd_j16_xia_open_go`、`hd_j16_xia_open_sub_done`
- X42 次步：`hd_j16_lvlong_handover_result`
- 继统等待日志：`<DONE>_wlog`

**场次变量**：
- guzang：`hd_j16_guzang_started/_won/_lost/_att/_def/_key/_asked/_go/_wait/_wsf_wlog`（`_key` 本轮新增）
- ledu：`hd_j16_ledu_started/_won/_lost/_att/_def/_key/_asked/_go/_wait/_wsf_wlog`（`_key` 本轮新增）
- xiliang：`hd_j16_xiliang_started`，以及 `hd_j16_xiliang_end_won/_lost/_att/_def/_key/_asked/_go/_wait/_wsf_wlog`

**入侵与闸门**：`hd_j16_hi_go_tufawugu`、`hd_j16_hi_go_juqumengxun`、`hd_j16_hi_go_helianbobo` 及各自的 `_late`；`hd_j16_hi_gate_shelun_3`、`hd_j16_hi_gate_helianbobo_3`。

**本轮新增定义**：
- 触发器 `hd_j16_n2_nanliang_founded_trigger`
- 效果 `hd_j16_n2_war_key_effect`（内部 scope `hd_j16_n2_wk_orig`、`hd_j16_n2_wk_cap`）
- scope `hd_j16_x66_key`、`hd_j16_x82_key`、`hd_j16_x90_key`

**修正与本地化键**：
- 修正：`hd_j16_duanye_mingyi_modifier`、`hd_j16_xia_duoma_modifier`、`hd_j16_rouran_khagan_modifier`
- 好感：`hd_j16_duanye_nominal_opinion`、`hd_j16_xiliang_tonghao_opinion`
- 事件兵名：`hd_j16_n2_army_guzang_name`、`_ledu_name`、`_xiliang_name`

**06 编号式旧名 → 语义名**：无，06 本节本来就用语义名。只有两处说明：X22、X26 的 done 照 06 原名不带 `_done` 后缀；X90 改用 `hd_j16_xiliang_end_*`，避开与 X38 撞名。

## 十、跨路对账表（按 grep 实况）
**我读别路的变量**

| 变量 | 设置方（暂存位置） | 本路读处 | 写法 |
|---|---|---|---|
| `hd_j16_lvguang_wang_done` | 6-E4 E4-X40（p6-E4 effects 第 1742 行） | X10、X14、X18（effects 第 637、730、870 行） | 不阻塞（或 >= 391.1.1） |
| `hd_j16_tiefu_done` | 6-E4 E4-T40（p6-E4 effects 第 1174 行） | X26（第 1177 行） | 不阻塞（或 >= 393.1.1） |
| `hd_j16_qifu_done` | 6-N1 E5-Y20（p6-N1 effects 第 3204 行） | X62（第 2107 行） | 不阻塞（或 >= 401.6.2） |
| `hd_j16_guzang_tufa_done` | 6-N1 E5-Y40（p6-N1 effects 第 3793 行） | X60（effects 第 1989 行）；X66 经 `hd_j16_guzang_ready_trigger`（triggers 第 126 行） | 不阻塞（或 >= 407.6.2） |
| `hd_j16_houqin_won`、`hd_j16_houqin_lost` | 6-S E5-J80（p6-S e5_395 第 2574、2582 行） | X86 闸门 `hd_j16_n2_xia_gate_ready_trigger`（triggers 第 104–105 行） | 与「后秦之主已不存在」二选一 |
| `hd_nbc_houqin_active` | 南线 J80（现有 KIND houqin，参数设） | X86 闸门（triggers 第 102 行） | 直接读 |
| `hd_hi_done_juqumengxun` | 入侵（p5-C，参数设） | X66 ready（triggers） | 直接读 |
| `hd_hi_started_tufawugu` | 入侵（p5-C `hd_hi_begin_effect`，参数设） | X60 前提（triggers 第 117 行） | 直接读 |

另：`hd_hi_done_tufawugu` 由 6-B 在 startup_404 第 15 行预设，本路不读，只作对账备忘。

**我设给别路的变量**

| 变量 | 读者（grep 实况） |
|---|---|
| `hd_j16_lvlong_done` | p6-N1 `zz_hd_j16_395n1_effects.txt`（E5-Y30） |
| `hd_j16_hi_gate_helianbobo_3` | p6-S（e5_395 effects、`zz_hd_nbc_events.txt`，与 J80 共设）；mod `zz_hd_hi_j16_triggers.txt`（入侵读） |
| `hd_j16_hi_gate_shelun_3` | mod `zz_hd_hi_j16_triggers.txt`（p5-C） |
| `hd_j16_hi_go_tufawugu`、`_juqumengxun`、`_helianbobo`（含 `_late`） | mod `zz_hd_hi_on_actions.txt`、`zz_hd_hi_j16_triggers.txt`（p5-C） |
| `hd_j16_rutan_done`、`hd_j16_rulugu_done` | 当前无读者（别路暂存与 mod 都 grep 不到；本路 X30 自读） |
| `hd_j16_xia_changan_done` | 当前无读者 |
| `hd_j16_bobo_shuofang`、`hd_j16_xia_open_done`、`hd_j16_xiqin_restore_done`、`hd_j16_mengxun_king_done`、`hd_j16_xiliang_done`、`hd_j16_nanliang_done`、`hd_j16_nanliang_restore_done`、`hd_j16_chipan_done`、`hd_j16_nanliang_end_done`、`hd_j16_rouran_khagan_done`、`hd_j16_lvzuan_done`、`hd_j16_duanye_done`、`hd_j16_lvguang_tianwang_done` | 别路当前无读者，只有本路下游节点读 |

## 十一、卒年表 PRE 变量的设置处（tsv 第 8 列，归本路节点的 8 条；行号为最终暂存文件）

| tsv 行（死者） | PRE | 设置处 | 条件 |
|---|---|---|---|
| 没弈干 `poduoluo_001` | `hd_j16_xia_open_result` | effects 第 1920 行，`hd_j16_xia_open_exec_effect` | X58 子步：入侵故事 rising 且勃勃独立有地 |
| 乞伏乾归 `qifu_008` | `hd_j16_xiqin_restore_result` | effects 第 2101 行（已独立支）、第 2168 行（复国成功） | X62 fire |
| 乞伏公府 `qifu_006` | `hd_j16_chipan_result` | effects 第 2468 行经 `succ_step` 的 RESULT 参数传入，实际由 `hd_j16_n2_handover_effect` 第 238/252 行设；事件 5760 a（events 第 462 行） | X74 换主，或炽磐已是西秦之主 |
| 吕弘 `lueyang_lv_009` | `hd_j16_lvzuan_result` | effects 第 1357 行经 `succ_step`（同上，由第 238/252 行设）；事件 5660 a（events 第 164 行） | X34 换主，或吕纂已是后凉之主 |
| 吕纂 `lueyang_lv_008` | `hd_j16_lvlong_result` | effects 第 1555 行 | X42 首步：吕纂（AI）在位，吕超、吕隆在世 |
| 沮渠男成 `juqu_007`、段业 `hd_j16_duan_ye` | `hd_j16_mengxun_king_result` | effects 第 1645 行，`hd_j16_mengxun_king_exec_effect`；事件 5690 a 调同一执行体 | X46 fire |
| 秃发傉檀 `tufa_012` | `hd_j16_nanliang_end_result` | effects 第 2719 行，`hd_j16_ledu_won_effect` | X82 战胜（含 war_key 替换后的关键县），或白土已在西秦 |
| 李歆 `longxi_li_007` | `hd_j16_xiliang_started` | effects 第 2926 行 | X90 开战成功 |

- 跳过、前标、到期一律不设 PRE。X60 不设 PRE。
- 8 条都与 TEMPLATE §5-15 相符，**tsv 不需要改**。
- 本路涉及、但没有 PRE 的行照表无条件执行：吕光（N）、吕绍（K，凶手吕纂）、沮渠罗仇（K，凶手吕光）、乌孤、利鹿孤、社仑、斛律（N）、步鹿真（K，凶手大檀）。
- 杜进一行的 PRE `hd_j16_lvguang_wang_result` 归 6-E4。
- 朱龄石、傅弘之的 PRE `hd_j16_changan_lost_result` 归 6-S。

## 十二、实测项建议
1. 404 局：
   - 勃勃 407 年起兵（短路）后，不篡夺并州、只改国号；
   - 408–409 年 X60 让傉檀叛秦复国，X66、X82 随后能开窗。
2. 370 局：
   - 南凉、北凉开闸后能起兵，称西平王子步、段业入宫廷能执行；
   - 入侵未起兵时 X60 记 WAIT 并到期跳过。
3. 继统换主不杀旧主，旧主转为廷臣。
4. X90 的 `capital_county.de_jure_liege` 能取到郡。
5. 三场战争开战后查 game.log 的 `HD_J16 n2 WAR_KEY` 日志：
   - 关键县被替换时，胜负判定、面板（姑臧实归才设）、傉檀 PRE 是否符合预期。
6. X22：北凉之主只有郡级时，是否改认后凉之主；查 `liege_tier_low` / `fealty_failed` 日志。