# pY-B 最终报告（修正后合并版）

# pY-B「全线机械扫描」修正轮报告

## 〇、审查意见逐条处理

审查共提 4 条意见，都是 minor，没有 blocker 或 major。处理如下：

1. **zz_tr_hd_370_l_english.yml 第 2 行注释与事实不符**：已修。
   - 第 2 行后半句原来写年号键在 zz_tr_WJ_names 里，现改为 "its era-name keys (SG_nianhao_*) are on lines 40-47 of this file, matching the Chinese line numbers."
   - 只改了注释文字，行数不变，中英行号仍然对齐。

2. **zz_hd_oe_l_english.yml:4608 的 liaodongxianggong 英文是占位**：已修。
   - 新增一次暂存登记：`stage.py pY-B edit localization/english/names/zz_hd_oe_l_english.yml`。
   - 在原地把第 4608 行的值从 "liaodongxianggong" 改成 "Duke Xiang of Liaodong"，没有另加同名键。
   - 证据：
     - 和 mod 原文件做 diff，只有 1 行改动（1 insertion、1 deletion）。
     - 文件仍有 UTF-8 BOM，换行仍是 LF，总行数仍是 4845。
     - 中文同文件同一行是「辽东襄公」，和新补的 _desc 英文一致。
   - 动笔前确认过 ck3.exe 不在运行。
   - 修正脚本：D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\pyb\fix_review.py（只写暂存区）。

3. **扫描脚本有覆盖缺口**：不改暂存区，只更正说法。
   - 上一版报告说「没有漏扫的类别」，这个说法偏乐观，现收回。
   - scan_j16.py 的口径限制有两点：
     - loc_ref 不查 character_interactions 的名称和 _desc，也不查嵌套在 triggered_desc 里的 desc。
     - ref_scripted 只查以 _effect/_trigger 结尾、或以 hd_/WJ_/j16 开头的调用。nbc_*、tgp_* 这类前缀不同、又不带这两个后缀的 scripted 调用查不到。
   - 这些缺口已由审查员的 xcheck2.py（查全部未知调用键）和 xcheck3.py（查全部右值的中英不对称）补查过，没有发现新的真问题，所以不影响本轮结论。
   - 以后要复用 scan_j16.py，建议做两处改动：
     - loc_ref 加上 interaction 的 key/_desc，以及任意深度的 triggered_desc/desc。
     - ref_scripted 改成：凡未定义的 X = yes/no/{ 一律报出，再排除引擎键。
   - 本轮没有改脚本，因为改了也不会改变结论，工具调用预算优先留给修复和复跑。

4. **hev 英文手工对齐后，重跑生成器可能冲掉**：交汇总人处理。
   - 请汇总人在 07_实施记录 里记一笔：zz_tr_hd_hev_l_english.yml 已手工按中文行位对齐，还插入了中文注释行。重跑 build_data.py 之前要先同步生成器，否则重跑后要再对齐一次。
   - 原文件末尾没有换行，这次补上了，无害。
   - 07_实施记录 归汇总人维护，本任务不写 docs。

## 一、暂存任务与文件清单

暂存任务名：pY-B。共 6 个文件，都是 edit，没有新建或删除。比上一版多了第 6 项：
- localization/english/zz_tr_hd_370_l_english.yml
- localization/english/custom_localization/zz_tr_WJ_names_l_english.yml
- localization/english/zz_tr_hd_hev_l_english.yml
- localization/simp_chinese/zz_hd_j16_core_l_simp_chinese.yml
- localization/english/zz_hd_j16_core_l_english.yml
- localization/english/names/zz_hd_oe_l_english.yml（本轮新增，只改了第 4608 行的值）

本轮没有写任何 hd_asp 文件，没有直接写 mod，没有跑生成器，没有开游戏，也没有提交 git。

扫描和修正脚本：
- 主扫描脚本（只读）：D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\pyb\scan_j16.py
  - 用法：`python -I scan_j16.py [--overlay pY-B] --out <目录>`
- 中英配对行号对比：D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\pyb\pairline.py
- 修正脚本（都只写暂存区）：
  - D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\pyb\fix_loc.py
  - D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\pyb\fix_review.py
- 扫描结果：
  - 修前：D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\pyb\out0\scan.txt
  - 上一轮修后：D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\pyb\out1\scan.txt
  - 本轮修后：D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\pyb\out2\scan.txt

## 二、扫描范围与方法

- **对象**：07_实施记录.md 附录 B 的 B.1 与 B.2 中所有 txt、yml、gui 文件，另加 zz_tr_hd_370、zz_tr_hd_history_events_rule、zz_tr_hd_hev 三个英文 yml，共 202 个。docs、tools、csv、tsv、py 不在内。
- **定义表与本地化表**：取全 mod 的 common、events、gui 和 localization，localization 含 replace 子目录。原版只取没被 mod 同路径文件遮蔽的部分，用来核对 scripted effect/trigger 定义、事件号和本地化键。
- **新旧区分**：本线的改动都没有提交，所以 git HEAD 就是本线动工前的基线。每条命中都和 HEAD 比较，HEAD 已有的标为「旧」。
- **覆盖计数**（说明各项检查确实执行了）：
  - 括号：158 个 txt/gui
  - 本线 yml 键：12909 个
  - 本地化引用：32968 次
  - 脚本调用：7784 次
  - 事件引用：395 次
  - 本线涉及的顶层定义：2021 个（全 mod 共 45630 个）
  - hd_j16 事件号：300 个（全 mod 共 6881 个）
- **自测**：
  - 少一个 }、多一个 }、值跨行、结束引号后还有内容，这几种情况都能报出。
  - hd_j16.0001 和 hd_j16.1 会归一为同一个事件号。
  - 在全 mod 范围能查出 28 处非本线的 scripted_effect 重名，说明查重机制有效。
- **口径限制**：见第〇节第 3 条，审查员已用 xcheck2/xcheck3 补查过。

## 三、各项计数

格式为「修前 out0 → 本轮修后 out2」。out2 与上一轮的 out1 完全相同；本轮两处改动都在注释或值里，不改变任何计数。

1. **花括号配平（brace）**：0 → 0。
2. **跨全 mod 顶层定义重名**：0 → 0。
   - 涵盖 scripted_effects、scripted_triggers、modifiers、opinion_modifiers、decisions、character_interactions、casus_belli_types、game_rules、nicknames。
   - on_action「同名且都带 effect」（只作参考）：0。
3. **事件号重复**：0 → 0。
4. **本地化**：
   - **loc_dup（同语言重复定义）**：185 → 185，全部是旧问题。
     - 来源是 replace 目录有意覆盖 WJ_names 的键：zz_WJ_real_fief_miaoshi 174 条，WJ_family_name_fixes 11 条。
     - 新增 0 条：OE 英文是原地改值，没有新增重复。
   - **loc_pair（中有英无 / 英有中无）**：249 → 233。
     - WJ_names 中有英无 193 条：旧问题。
     - 370 中有英无 40 条：英文在 zz_hd_english_missing_events_20261015 里。
     - zz_tr_WJ_names 英有中无：8 → 0。
     - 相对 HEAD 新增：0 → 40，这 40 条就是上面 370 那 40 条。
   - **loc_pair_line（同对中英行号不同）**：724 → 0。
     - 只统计至少一侧是本线新建文件的配对。WJ_names、nbc 两对旧配对的错位在 HEAD 就已存在，不计入。
   - **loc_value（值必须单行、引号闭合）**：0 → 0。
5. **引用的本地化键中英都要存在（loc_ref）**：173 → 172，相对 HEAD 新增 0。剩下 172 条全是旧问题：
   - 绰号缺 _desc：105 条
   - 书签人物缺英文：36 条
   - 年号缺英文：28 条
   - hd_idfix 人物名缺英文：3 条
6. **引用检查**：
   - ref_event：0。
   - ref_scripted：0。
     - bookmark_portraits 里的 gene_balding_hair_effect 是基因名，不是 scripted effect，属误报，已排除。
   - 补充检查（没有 _effect/_trigger 后缀的 hd_/WJ_/j16 前缀调用）：0。

hd_asp 文件：各项命中都是 0。zz_hd_asp/zz_tr_hd_asp 这对有 1407 个键，zz_hd_asp3/zz_tr_hd_asp3 这对有 722 个键，中英键集合一致，行号也一致。pY-A 不需要处理任何项。

## 四、逐项修法与证据

所有修改都按字节进行，6 个文件都保留了 UTF-8 BOM 和 LF 换行。

1. **年号英文挪回 370 的英文文件**
   - 从 zz_tr_WJ_names_l_english.yml 删掉 8 行：SG_nianhao_jianxi、shengping、jianguo、xianan 及各自的 _tt。
   - 这 8 行挪进 zz_tr_hd_370_l_english.yml 第 40～47 行，和中文 zz_hd_370 第 40～47 行对齐。
   - 证据：git diff HEAD 证实这 8 行是本线 pX-B 加进 WJ_names 的。挪完后英有中无 8 → 0，英文没有新增重复。
2. **zz_tr_hd_370_l_english.yml 按中文第 1～47 行逐行对齐**
   - 第 2 行注释在本轮改成符合事实的说法。
   - 第 48 行注释说明，第 49 行以后的事件英文在 zz_hd_english_missing_events_20261015。
   - 结果：错位 26 → 0。
3. **zz_tr_hd_hev_l_english.yml 按中文行位重排**
   - 两边键集合一致（750 对 750）。
   - 只插入了 12 行注释和 1 行空行，外加文件末尾补了换行。
   - 译文一字未改，错位 698 → 0。
4. **慕容廆新绰号补 _desc**
   - 原因：history/characters/01_shiliuguozhu.txt:8229 新增了 give_nickname = liaodongxianggong，但 liaodongxianggong_desc 中英都没有。
   - 在 j16 core 中英两个文件的第 8 行各加一条 liaodongxianggong_desc。
5. **（本轮新增）绰号本身的英文**
   - zz_hd_oe_l_english.yml:4608 的 liaodongxianggong 改为 "Duke Xiang of Liaodong"，和 _desc 的英文一致。

## 五、需要汇总人处理（仍未解决）

1. **370 剩余 40 条中有英无**（hd_370.0110～0170 的 t、desc、a、b）
   - 英文在非本线文件 zz_hd_english_missing_events_20261015_l_english.yml 里，游戏中能正常显示。
   - 如果要求中英文件严格一一对应，可以把这 40 行挪进 zz_tr_hd_370 的第 49 行以后，同时从原文件删掉。
2. **绰号普遍缺 _desc，共 105 条**（旧问题）
   - 分布：OE 绰号 60 条、shihao_* 谥号约 30 条、晋帝庙号 13 条（zz_hd_nbc_startup_effects.txt:204-216）。
   - 另外 WJ_tianjia_history_nicknames 定义的 33 个绰号全部没有 _desc。
   - 是否统一补齐需要拍板。
3. **22、89、263、531、617 剧本缺英文**（旧问题）
   - 书签人物名 36 个。
   - 年号 14 个，加上各自的 _tt 共 28 条。
   - 对应剧本没有英文 yml，补的话要新建或改非本线文件。
4. **人物名缺英文 3 条**（旧问题）
   - hd_idfix_lu_huai_ren_name
   - hd_idfix_guangping_song_079_name
   - hd_idfix_pingyuan_liu_015_name
5. **两对旧配对的行号整体错位**（HEAD 已有）
   - WJ_names 与 zz_tr_WJ_names
   - zz_hd_nbc 与 zz_hd_english_completion_nbc
6. **hev 生成器风险**
   - 请在 07_实施记录 记一笔：hev 英文已手工对齐，重跑 build_data.py 前要先同步生成器，或者重跑后再对齐一次。
7. **扫描脚本口径限制**
   - 写进汇总报告时请注明第〇节第 3 条的限制，以及审查员已用 xcheck2/xcheck3 补查、结果为 0 新增。
8. **pY-A 不需要处理任何项。**

## 六、闸门结果

命令：`gate.py --overlay pY-B --compare baseline.json --only-changed --out ...\stage\pY-B_gate`

结果：
- overlay 文件 6 个，errors 0。
- 相对基线没有新增项（counts 为空），退出码 0。
- 结果文件：D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\pY-B_gate.txt

复跑 scan_j16.py --overlay pY-B，输出到 out2：
- 全量计数：brace、dup_def、dup_onaction、dup_event、loc_pair_line、loc_value、ref_event、ref_scripted、ref_scripted_noprefix 都是 0；loc_dup 185，loc_pair 233，loc_ref 172。
- 相对 HEAD 新增：只有 loc_pair 的 40 条，也就是上面 370 那 40 条。