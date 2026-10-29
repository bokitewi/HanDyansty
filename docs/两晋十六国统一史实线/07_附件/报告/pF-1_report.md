# pF-1 最终报告（修正后合并版）

## 审查意见处理结果

审查共 2 条 minor，没有 blocker 或 major。两条都已处理；第 2 条超出 F-1 的写入范围，转交汇总人。

### 1. 南线 9 行挪组没写进偏差（minor）：已处理

- **代码**：不改。南线 9 行仍在 `hd_hev_grp_404`，9 行的适用范围都是 le404，功能不受影响。
- **组名**：e5 组的年份由 395–421 改为 **395–412**。组内最晚一行是 412 年的北凉入姑臧，现在组名与内容一致。共改了三处：
  - 中文 yml 第 25 行的组名，以及第 682 行的注释；
  - 英文 yml 第 25 行；
  - 生成数据 `rows_j16.py` 的第 649–651 行，日后重跑 gen.py 时结果保持一致。
- **编码核对**：中文 yml 仍是 BOM + 全 CRLF（763/763），英文 yml 仍是 BOM + 全 LF（750 行）。gui 和 scripted gui 里没有这个组名字串，没有改动。
- **报告**：「自拟与偏差」新增第 11 条，写明这次挪组和理由，见下文。

### 2. hd_hev_window_rule_off 缺英文（minor）：不在 F-1 写入范围，转交汇总人

- 我核了整个规则 yml `localization/simp_chinese/zz_hd_history_events_rule_l_simp_chinese.yml`，缺英文的不止这一个键。全部 6 个键在 english 目录下都找不到：
  - rule_hd_history_events_rule
  - setting_hd_history_events_on
  - setting_hd_history_events_on_desc
  - setting_hd_history_events_off
  - setting_hd_history_events_off_desc
  - hd_hev_window_rule_off
- 结果是：英文界面里，游戏规则页的这条规则、关闭规则后的面板提示，都会显示裸键。
- 这个缺口本轮之前就存在，不是 F-1 引入的。
- 已写入第七节第 6 条：建议汇总人新建 `localization/english/zz_tr_zz_hd_history_events_rule_l_english.yml`，补齐这 6 个键。
- 报告里「英文覆盖全部」的说法改为「覆盖面板 yml 全部 750 键」。

### 仍未解决项

- 规则 yml 的 6 个英文键（交汇总人）。
- 其余照原报告：12 个只设变量不建行的项、s6/s7 去重、6-E4 的 5 个候选。

### 闸门（修正后重跑）

- 命令：`gate.py --overlay pF-1 --compare baseline.json --only-changed --out ...\stage\pF-1_gate`
- 结果：error 16，warn 0，`resolved_vs_baseline` 0，overlay 4 个文件。
- 16 条全部是 `gvar_read_never_set`，与修正前一致，都是宏参数拼变量名造成的误报，逐条对应见第六节。
- 输出文件：`D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\pF-1_gate.txt`

---

# pF-1「史实事件面板」实施报告（修正后合并版）

面板三个文件已在暂存区改完，英文面板文件也已新建。闸门新增 16 条，全部可解释（见第六节）。本轮没有直接写 mod，没有跑生成器，没有开游戏，没有提交 git。

## 一、暂存任务名与文件清单

任务名 **pF-1**，共 4 个文件：

| 操作 | 文件 | 编码与换行 |
|---|---|---|
| edit | common/scripted_guis/hd_hev_scripted_guis.txt | BOM、CRLF |
| edit | gui/hd_hev_window.gui | BOM、CRLF |
| edit | localization/simp_chinese/hd_hev_l_simp_chinese.yml | BOM、CRLF |
| new | localization/english/zz_tr_hd_hev_l_english.yml | BOM、LF |

- 三个现有文件都在动笔前一刻才 stage，暂存时与 mod 原文件逐字节相同。审查时又核过一次：base_sha256 与 mod 现文件一致，没有被并发会话改动。
- 生成数据与脚本都在 `D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\pF1\` 下：
  - rows_j16.py：两晋 172 行的数据，本轮已同步改了 e5 组的年份；
  - en_old.py：非两晋旧行的英文；
  - gen.py：生成脚本；
  - scan.py 与 sets.json：变量对账。
- **gen.py 不是幂等的**，只能以 mod 原文件为底重跑。

## 二、逐项做法与证据

### 1. 现有面板的结构

- 每行有三种状态：
  - done：行 gui 成立；
  - wait：本行适用（ap）而行 gui 不成立；
  - na：本行不适用。
- 窗口本来就是 scrollbox，加行不需要改窗口结构。

### 2. 01 §8 的落实

**适用范围**
- 新增 `hd_hev_ap_j16_le304`、`le346`、`le370`、`le404` 四个，用 OR 列开局日期。规则是：节点的史实日期晚于哪些开局日期，这一行就适用于哪些开局。
- `grp_304`、`grp_346`、`grp_370`、`grp_404` 改为按组适用，另新增 `grp_j16_e2`、`grp_j16_e5j`、`grp_j16_e5` 三组。

**旧行的改法**
- 旧 24 行的 is_shown 去掉了 `game_start_date`。
- 界面里旧行的 st_wait、st_na 也换成新的 ap。

**新行类型 `hd_hev_row_j16`，分四种状态，互斥且覆盖全部情况。** A 是本行适用，R 是本行变量已设，J 是 le404（即任一两晋开局）：

| 状态 | 条件 |
|---|---|
| 已触发 | A 且 R |
| 未触发 | A 且非 R |
| 开局前 | J 且非 A |
| 非本局 | 非 J |

- 「开局前」的鼠标提示是「开局前已成往事」。
- 适用范围本身就是 le404 的行，「开局前」写 `visible = no`。

**tooltip 与帮助**
- 旧 24 行的 tooltip 按节点文件头注释重写。
- 304_04、370_02 两条值里的裸换行已改成 `\n`。
- 346_02、346_03、346_06、404_01、404_03 五行改为「选史实项时点亮」。依据：events/zz_hd_nbc_events.txt 第 254、316、374、479、559 行，变量都在事件的 option a 里设。
- 帮助文本加了一句说明「开局前」；新增键 `hd_hev_st_past` 与 `hd_hev_st_past_tt`。

### 3. 避开「空玩家根每帧刷错」

- j16 相关的全部 scripted gui 都不声明 scope；界面一律用 `IsShown(GuiScope.End)` 调用。
- is_shown 里只用 `game_start_date` 和 `has_global_variable`。
- 两晋段 SetRoot 出现 0 次。
- 非两晋的旧行没有改。

### 4. 代码与清单对账

- scan.py 扫了全部 `set_global_variable = hd_hev_*`，并展开了 KEY、KIND 两类宏：
  - KEY 宏：304b 第 73、95 行；
  - KIND 宏：e3_346 第 3977 行、346c 第 332 行。
- 对账结果：

| 项目 | 结果 |
|---|---|
| 报告有、代码无 | 0 |
| 代码有、报告无 | 只有 `hd_hev_j16_jinwang`（e2_304 第 147 行），已补一行 |
| 面板读、但没人设 | 0 |
| 有人设、但面板不读 | 正好是有意不做的 14 个 |

- 旧 24 行读的非面板变量，在 j16 路径上都核到了设置处。

### 5. 汇总人已定事项，均已照做

- 370 组只做 mieliang、miedai 两行，不做 s6、s7。
- 404_05、404_06 加读 `hd_j16_nanyan_won/_lost` 和 `hd_j16_houqin_won/_lost`。
- liuyu_regent 一行加读 `hd_hev_404_restore`。

### 6. 本地化

- 中文格式：「#high 名#!\n窗口\n条件\n结果」。新键统一用 `hd_hev_j16_<语义>_name/_tt`。
- 英文 750 键，与中文 750 键一一对应。已检查：英文里没有汉字，没有 `"`、`[`、`$`。
- 译名照 zz_tr 约定。

## 三、最终行数（按组）

| 组 | 组头适用范围 | 行数 | 其中旧行 |
|---|---|---|---|
| grp_304 西晋末·八王与永嘉 304–317 | le304 | 35 | 304_01–04 |
| grp_j16_e2 东晋初·二赵 317–346 | le304 | 36 | — |
| grp_346 后赵崩解与秦燕并起 346–370 | le346 | 59 | 346_01–06 |
| grp_370 王猛伐燕与前秦一统 370–383 | le370 | 16 | 370_01–05、346_07、346_08 |
| grp_j16_e5j 东晋末·王恭孙恩桓玄 | le370 | 4 | — |
| grp_j16_e5 北方诸国 395–412（本轮由 395–421 改） | le404 | 6 | — |
| grp_404 刘裕北伐与晋宋禅代（含南线 9 行） | le404 | 16 | 404_01–07 |

- 合计 172 行：新增 148 行，改造旧行 24 行。整个窗口约 362 行。
- e5 组 6 行里，参合陂、魏取中山、南燕称帝、柴壁 4 行用 le370；夏建国、北凉入姑臧 2 行用 le404。

## 四、未做的行及原因

| 变量 | 原因 |
|---|---|
| `dir_qin_s6`、`dir_qin_s7` | 汇总人已定去重，由 mieliang、miedai 代替 |
| 5-A2 的 12 个只设变量项 | 照 04 §1.5 ★ 不建行：xiaowu_li、xinting、jiuxi、xiewang、qinzheng、xiebeifa、xiean_chuzhen、daozi、wanggong_jingkou、andi、huanxuan_jing、liuyu_jingkou |
| 6-E4 的 5 个候选 | 不在任何清单里，读的也是 `_result/_won`，不是面板变量 |

## 五、自拟与偏差（boki 10-27 授权）

1. **「开局前」做成独立状态**，并新建行类型 `hd_hev_row_j16`；旧的 `hd_hev_row` 不动。
2. **346_07、346_08、dir_qin_start 移到 370 组**。因此 `grp_346` 只用 le346（01 §8 原写 le370）。
3. **N1 四行用 le370**（06 §4.4 原写 le404）。这四件事都早于 404.3.24，按 01 §8 的日期规则应适用于 370 开局。
4. **王恭两次举兵合成一行**。
5. **组名改成时代名**，并注明适用的开局。
6. **补了 jinwang 一行**。
7. **旧行「弹出即算」改为「选史实项时点亮」**，依据见二.2。
8. **英文覆盖面板 yml 全部 750 键**，含约 190 行非两晋旧行，用的是精简意译。面板窗口另外引用的规则 yml 键不在其内，见第七节第 6 条。
9. **旧 ap 保留未删**：`hd_hev_ap_s304`、`s346`、`s370`、`s404` 已无引用，但仍保留。
10. **tooltip 依据节点文件头注释撰写**。tuyuhun3、duanbu、murongren、chengkang、jinzhun、jinwang、zhangping 这几行另外按执行体核过并修正。
11. **（本轮补写）南线 9 行改归 `grp_404`**，偏离 06 §4.4 与 p6-S 的「归 e5 组」。涉及 liuyu_regent、luxun_north、tao_liuyi、pingshu、tao_xiuzhi、changan_lost、songgong、gongdi、songwang，按日期穿插在 404_01–07 之间。
    - 理由：这 9 行都是刘裕掌政、北伐、晋宋禅代的主线，与旧行 404_01–07 是同一条叙事，放在一起按时间顺序读更连贯。
    - 9 行的适用范围都是 le404，与 `grp_404` 相同，所以组头「本局」的判定和各行状态都不受影响。
    - e5 组因此只剩北线 6 行。组名年份随之由 395–421 改为 395–412（最晚一行是 412 年北凉入姑臧），rows_j16.py 已同步。

## 六、闸门

- 修正后重跑：error 16，warn 0，全部是 `gvar_read_never_set`。闸门会跳过带 `$参数$` 的变量名，所以宏拼出的变量被误报为「读而未设」。
- KEY 类 3 条：zhangshi_heir、zhangmao_heir、lishi_heir。宏的调用在 304b 第 380、1191、1164 行，宏内的设置处在 304b 第 73、95 行。
- KIND 类 13 条：maqiu、shichong、chupou、xiangguo351、liuxian、liantai、yinhao、huanqin354、guanggu、sanyuan、luoyang365、sigong、fangtou。
  - 宏内的设置处在 e3_346 第 3977 行、346c 第 332 行。
  - 各变量写出 KIND 值的调用行：

| 变量 | 调用位置 |
|---|---|
| shichong | e3_346:856 |
| xiangguo351 | e3_346:1258 |
| liuxian | e3_346:1486 |
| sigong | e3_346:1976、2057 |
| sanyuan | e3_346:2286 |
| liantai | e3_346:2365 |
| guanggu | e3_346:2713 |
| luoyang365 | e3_346:2825 |
| chupou | e3_346:3157 |
| yinhao | e3_346:3239 |
| huanqin354 | e3_346:3423 |
| fangtou | e3_346:3708 |
| maqiu | 346c:270 |

- 其他自检：四个文件都带 BOM，各自没有混合换行；大括号配平，scripted gui 918/918，gui 2076/2076；yml 格式合规。

## 七、需要汇总人处理的事项

1. 不需要重跑任何生成器。
2. 旧生成器 build_data.py 不得再跑，否则会冲掉全部手工行。
3. 以后增删两晋行：改 rows_j16.py，把 mod 原三文件复制到空目录，运行 `python -I gen.py <sg> <gui> <zh> <en>`，再把产物拷进暂存区。
4. apply 时如果三个原文件的哈希变了，需要以新文件为底重跑 gen.py。
5. 可选：把非两晋的旧行也改成无根写法。
6. **（审查新增）规则 yml 缺英文。** 中文文件 `localization/simp_chinese/zz_hd_history_events_rule_l_simp_chinese.yml` 的全部 6 个键在 english 目录下都不存在：
   - rule_hd_history_events_rule
   - setting_hd_history_events_on
   - setting_hd_history_events_on_desc
   - setting_hd_history_events_off
   - setting_hd_history_events_off_desc
   - hd_hev_window_rule_off（面板窗口 gui 第 34 行引用）

   英文界面会显示裸键。这个缺口本轮之前就有。建议新建 `localization/english/zz_tr_zz_hd_history_events_rule_l_english.yml` 补齐，F-1 无权写这个文件。

## 八、实测项（未开游戏，全部待测）

1. 观察者模式下 190 开局跑 30 秒：error.log 里 hd_hev 新行报错应为 0，无根的 `game_start_date` 求值也应正常。
2. 304、346、370、404 四个开局各打开一次面板，核对：
   - 「开局前」显示正常，并有悬停提示；
   - 适用的行显示「未触发」或「已触发」；
   - 各组组头「本局」标记正确；
   - e5 组名显示为 395–412。
3. 190 开局：两晋行显示「非本局」。
4. 304 开局跑一段：节点触发时相应的行会点亮；404_05、404_06 在节点自判胜负后能点亮。
5. 英文界面：750 个键都能解析，「Lü」和 en dash 显示正常；规则 yml 的英文补上后再看关闭规则时的提示。
6. 约 362 行时滚动是否卡顿。