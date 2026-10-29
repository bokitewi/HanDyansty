# p5-B 最终报告（修正后合并版）

# p5-B「鸠摩罗什位置修正」修正报告

审查共提出 2 条意见，都是 minor，都已处理。两条都只要求补写报告，所以**暂存区里的三个文件这一轮没有再改动**。

## 零、逐条处理审查意见

### minor 1：04 正文仍写着调用 `hd_fo_e27_effect`
- **处理**：已在下文第五节第 1 条加入「交 5-A 之前回填 04 设计文档」，写明要回填的位置、新调用名和注意事项。
- **为什么不由我直接改 04**：`docs/两晋十六国统一史实线/04_370王猛伐燕.md` 不在 p5-B 的文件分工里，所以交汇总人回填；也可以改为写进 5-A 的交接文本。

### minor 2：304 开局的接纳者结论偏弱
- **处理**：已只读核实，并把结论补进下文第二节。
- **核实结果**：`zz_hd_304_characters.txt:434-440` 里的 `hd_304_chief_qiuci_tianshanbeilu` 只有 name、culture、rite 和生卒年（259.10.12–319.5.17），没有 dynasty，也没有配偶。全部 history/characters 里没有任何人以他为 father 或 mother。
- **结论**：已改为可执行的写法，并给出首测时的核对办法。

## 一、暂存任务名与文件清单

**暂存任务名**：p5-B。

三个文件都是改现有文件（stage edit），没有新建，也没有删除：

| 文件 | 编码 | 备注 |
|---|---|---|
| `docs/佛教东传_开局推导表.md` | UTF-8，无 BOM，LF | 与原文件一致 |
| `tools/hd_fo/gen_hd_fo_monks.py` | UTF-8，无 BOM，LF | 只改源码，**没有运行**，只做了 ast.parse 语法检查，通过 |
| `common/scripted_effects/zz_hd_fo_story_effects.txt` | UTF-8 带 BOM，LF | 花括号配平检查通过 |

暂存副本在 `D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p5-B\files\` 下。

我没有碰 hd_hi 那组文件（5-C），也没有碰 304、346、导演、风味各文件。

### 推导表改了什么
- `:36` 县头衔表：龟兹从 c_uuii_p_2766 改为 c_uuii_p_6216，并注明是西域龟兹（d_qiuci_tianshanbeilu），不是上郡龟兹 c_uuii_p_2766（d_shangjun）。
- `:145` 370 开局一行：罗什所在改为「龟兹（西域，c_uuii_p_6216）」，备注写明不是上郡龟兹。

### 生成器改了什么
- **罗什的两处位置**
  - SPAWN 改为 `'jiu_mo_luo_shi': (351, 'c_uuii_p_6216', None)`，在 :87。
  - `START['370.2.13']` 改为 `('jiu_mo_luo_shi','c_uuii_p_6216',26,None)`，在 :116。
  - 两处都加了注释。404 开局的长安 c_uuii_p_867 没有动。
- **新增内容**：`import re, sys`、HOMONYM_OK 字典，以及三个函数：
  - `load_counties()`：只读 mod 的 common/landed_titles（descriptor 有 replace_path），用花括号栈求出每个县所属的郡；县重复定义时报 WARNING。
  - `load_title_names()`：先读 simp_chinese，再读 replace/simp_chinese，后读的覆盖先读的。
  - `check_places()`：
    - PLACE 不存在就 assert 中断。
    - 打印「县 ID → 本地化名 → 所属郡（郡名）[用处]」对照表。
    - 同名县已在 HOMONYM_OK 登记的，打印说明；没登记的报 WARNING。
    - 没有本地化名的县报 WARNING。
    - 末行打印「县 ID 校验：N 个县，WARNING n 条」。
- **调用与输出**：`check()` 末尾调用 `check_places()`；`main()` 开头加 `sys.stdout.reconfigure(errors='replace')`。

### story effects 改了什么
- 年度调度里 e26、e27 两行改成两层 if：
  - 到期且 `has_global_variable = hd_j16_pulse_started` 时，只调 `hd_fo_expire_effect`（E26 的 EXP=385，E27 的 EXP=394）；
  - 否则照原样调 `hd_fo_e26_effect` / `hd_fo_e27_effect`。
- 新增 j16 入口：`hd_fo_e26_j16_effect = { WHO = … }`（:680）、`hd_fo_e27_j16_effect = { WHO = … }`（:699）。
- 原 `hd_fo_e26_effect`（:639）和 `hd_fo_e27_effect`（:657）一字未改。

### hd_j16_pulse_started 的来源
这个变量只在 `zz_hd_j16_core_effects.txt:14` 的 `hd_j16_bootstrap_effect` 里设置，条件是 `hd_j16_start_trigger`（开局日期为 304.11.20、346.12.10、370.2.13、404.3.24 之一）。调用方有两个：
- on_game_start_after_lobby 的 `hd_j16_history_start`，另要求 `hd_history_events_enabled_trigger`；
- yearly_global_pulse 的 `hd_j16_yearly_rescue`。

因此：
- 史实事件规则关闭的 j16 局，以及 190、218 等开局，都不设这个变量，按年份触发的原行为保留；
- 421 年以后变量仍在，但 E26、E27 早已了结，没有影响。

## 二、第 6 步接纳者核对（只读）

- **370 开局**：6216 和 d_qiuci_tianshanbeilu 的持有人是 hd_nbc346_chief_qiuci_tianshanbeilu（312.5.9–378.1.3），见 `zz_hd_370_titles.txt:96`、`:587`。郡头衔 liege = 0，独立、在世。罗什开局进他的宫廷。
- **346 开局**：同一人，见 `zz_hd_346_titles.txt:235`、`:1620`。351 年罗什出场时此人 39 岁，满足条件。
- **304 开局（已按审查补强）**：
  - **情况**：持有人 hd_304_chief_qiuci_tianshanbeilu（`zz_hd_304_characters.txt:434-440`）生于 259.10.12，卒于 319.5.17，没有 dynasty、配偶和子女。全部 history/characters 里没有人以他为父母。
  - **结论**：351 年龟兹这一支必然已换成引擎随机生成的继承者，或已被他人吞并。罗什的接纳者**完全取决于运行时的局面**，基本要靠 `zz_hd_fo_core_effects.txt:95-125` 的退路决定：
    - ② 6216 县持有人的最高领主；
    - ③ 同一法理王国里领地最大的独立君主；
    - ④ 离龟兹最近的独立君主。

    其中③、④可能把罗什交给远处的君主。
  - **建议（只记录，不阻塞本期）**：汇总人首测 304 局时，在 game.log 里搜「hd_fo: 高僧出场 jiu_mo_luo_shi」「hd_fo: 高僧出场失败」「hd_fo: 高僧移居」，核对罗什落在谁的宫廷。如果落到远处君主那里，再考虑两种补法：
    - 由 304 节或 5-D/6-B 在 6216 补一位长寿、有王朝的龟兹王；
    - 给罗什的 SPAWN 指定接纳者。
- **404 开局**：罗什直接放在长安 867，不涉及。

## 三、自拟与偏差

1. **【偏差】j16 改调两个新入口，不直接调原效果。** 04 §4 第 7 步原写调用 `hd_fo_e27_effect`，现改为带参入口 `hd_fo_e27_j16_effect = { WHO = … }`；E26 同样新增 `hd_fo_e26_j16_effect`。
   - **理由**：原效果写死了吕光 `character:lueyang_lv_002`（生于 333）和苻坚 `character:lueyang_fu_020`（生于 338）。304 开局时 history 里没有这两人，只有 hbirth 出场指针。照原文调用的话，304 局里罗什会落到姑臧之主那里，道安会落到长安之主那里。
   - **守卫**：新入口不看年份，所以自带 `hd_fo_done_eNN` 守卫；高僧已死或已做过时，什么都不做。
   - **E26 不用预存 scope 的办法**：原效果在道安已死时仍会设 done、移慧远、发 1026，所以没有采用「预存 scope:hd_fo_actor 再调原效果」。
   - **兼容**：原效果保持不变，非 j16 局零变化。
   - **文档未同步**：04 正文还没改，见第五节第 1 条。
2. **【自拟】同名县的处理。** 在 HOMONYM_OK 里登记、写明是哪一个的，只打印说明，不报警告；没登记的报 WARNING，不中断。PLACE 不存在才 assert 中断。
3. **【自拟】j16 下的作废年份**沿用原 EXP：E26 为 385，E27 为 394。西征没有发生或失败时，罗什留在龟兹等 E30（401）。
4. **【自拟】`main()` 开头加 `sys.stdout.reconfigure(errors='replace')`**，防止 GBK 控制台打印中文县名时报错。
5. **行号漂移**：
   - 04 写的 `01_landed_titles.txt:37558`，实际在 `:37549`；
   - 生成器的 :84、:112 现在是 :87、:116；
   - story 里的 e26、e27 现在在 :639、:657。
6. **check_places 没有通过生成器执行过**，只做了 AST 检查。我另写了只读探针跑同一套逻辑，结果是：
   - 2168 个县，没有重复定义；
   - SPAWN、START 用到的县全部存在；
   - 同名的只有 2766 和 6216（都叫「龟兹」），已登记；
   - WARNING 0 条。

   审查方也用探针执行过 check()，同样是 WARNING 0 条。

## 四、本期面板行清单（交 F-1）
无。04 §1.5 里没有 hd_fo 或罗什的面板行。

## 五、需汇总人处理

1. **【本轮新增】交 5-A 之前回填 04 设计文档**，或者写进 5-A 的交接文本。
   - **要改的位置**：`docs/两晋十六国统一史实线/04_370王猛伐燕.md` 的 §4 第 7、8 步表格（约 :250-251）、§1 E4-Q45 第②步（约 :90）、E4-Q40 结局列（约 :87）。
   - **改成的调用**：
     - E4-Q45 第②步：`hd_fo_e27_j16_effect = { WHO = <解析出的吕光> }`
     - E4-Q40：`hd_fo_e26_j16_effect = { WHO = <秦主> }`
   - **要同时注明三点**：
     - 不能写 `= yes`，必须传 WHO；
     - 吕光要先经 `hd_j16_resolve_effect = { ID = lueyang_lv_002 AS = … }` 解析；
     - 不要占用 hd_fo_actor、hd_fo_place、hd_fo_receiver、hd_fo_monk、hd_fo_kingdom 这几个 saved scope 名。
   - **不回填的后果**：5-A 照 04 正文调原效果，功能上能跑，但 304 局的接纳者会错，新入口等于白做。
2. **重跑生成器**：`python -I tools/hd_fo/gen_hd_fo_monks.py`。会重写以下文件：
   - `common/scripted_effects/zz_hd_fo_monks_generated_effects.txt`
   - `common/customizable_localization/zz_hd_fo_custom_loc.txt`
   - 两份 `zz_hd_fo_monks_l_*.yml`

   重跑后核对两点：罗什的出场和 370 开局两处都是 c_uuii_p_6216；check 输出「WARNING 0 条」。重跑之前，生成物仍写 2766，行为不变。
3. **落盘顺序**：5-B 落盘后、5-A 加调用之前，j16 局的 E26、E27 只会到期作废，不会触发。建议与 5-A 同批落盘，或在 5-A 之后落盘。
4. **要 5-A 代加的调用**（写在 `zz_hd_j16_e4_370_effects.txt`）：
   - **E4-Q45 第②步「破龟兹」成功时**：
     ```
     hd_j16_resolve_effect = { ID = lueyang_lv_002 AS = hd_j16_q45_lv }
     hd_fo_e27_j16_effect = { WHO = scope:hd_j16_q45_lv }
     ```
     - 作用域名可以换。
     - WHO 需在世且 is_ruler；吕光此时已受敦煌 d_dunhuang_hexi，满足条件，罗什归吕光。
     - WHO 无地或不存在时，罗什移居姑臧 1564。
   - **E4-Q40 襄阳之战秦胜时**：
     ```
     hd_fo_e26_j16_effect = { WHO = scope:<节点解析出的秦主> }
     ```
     - WHO 在世即可，不要求有地。
     - 效果：道安归 WHO，慧远移柴桑，WHO 得虔诚 +100、威望 +75，并收到 hd_fo.1026（文案用「朕」，没有写死苻坚）。
   - 两个入口在任意作用域都能调。5-A 不需要设任何变量。
   - 玩家秦主在 Q45 选 b（不遣）时什么都不用调，E27 会在 394 年由调度作废。
5. **5-D、6-A、6-B**：无需配合。如果首测 304 局发现罗什落到远处君主那里，见第二节的补法建议。
6. **旧档**：修正前开的 370 档，罗什已经在上郡龟兹；修正只对新开的局生效。
7. **顺带观察（不阻塞）**：E30（`hd_fo_e30_effect`，401 年）写死了姚兴 `shaodang_yao_013`。304、346 局里姚兴同样只有 hbirth 指针，会回退到长安之主。是否给 E30 也做 j16 入口，由 6-A 或汇总人决定。

## 六、新增事件号与变量名
- **新增事件号**：无，复用 hd_fo.1026。
- **新增变量**：无。只读写已有的 hd_fo_done_e26、hd_fo_done_e27，并读 hd_j16_pulse_started。
- **新增效果**：`hd_fo_e26_j16_effect`、`hd_fo_e27_j16_effect`，参数都是 WHO。
- **新增生成器常量和函数**：HOMONYM_OK、`load_counties()`、`load_title_names()`、`check_places()`。

## 七、闸门（本轮复跑）
- **命令**：照任务给的执行，输出在 `D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p5-B_gate.txt`。
- **结果**：相对基线新增 error 2 条、warn 0 条，与上一轮相同，都是 gvar_read_never_set，都是误报：
  - `zz_hd_fo_story_effects.txt:683` 的 hd_fo_done_e26
  - `zz_hd_fo_story_effects.txt:702` 的 hd_fo_done_e27
- **为什么是误报**：这两个变量由 :7 的 `hd_fo_done_effect` 用 `hd_fo_done_$E$` 带参写法设置，gate 跳过带 $参数$ 的变量名（共 53 个），所以判成只读不写。
- **扫描范围**：overlay 只扫到 1 个 txt（overlay_files=1），py 和 md 不在 gate 范围内。

## 八、仍未解决项
1. 04 设计文档的回填不在本任务的文件分工内，交汇总人或 5-A，见第五节第 1 条。
2. 304 局 351 年罗什实际由谁接纳，只能首测时看 game.log 确认，见第二节。
3. 生成器重跑由汇总人在收尾时做；在那之前，生成物仍写 2766。