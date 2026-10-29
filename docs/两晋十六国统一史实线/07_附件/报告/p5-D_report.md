# p5-D 最终报告（修正后合并版）


# p5-D 第三轮修正：处理审查意见

两条 minor 审查意见都已处理。只改了暂存区，闸门重跑后相对基线新增 0 条。

## 逐条处理结果

**1.【minor，已修】百济移交清单补全**
- 只改报告，代码不动。
- 第五节第 6 条补成 8 行，holder 都由 `hd_nbc346_chief_baiji` 改为 `korean_buyeo_49`：
  - `history/titles/zz_hd_370_titles.txt` 的 :82（d_baiji）、:524（3353）、:525（3887）、:526（3904，沙热伊）；
  - `history/titles/zz_hd_370_undo.txt` 的 :75（d_baiji）、:515、:516、:517（3353、3887、3904）。
- 这 8 行已在 mod 现文件中用 grep 逐行核实。
- 同时写明以下几点：
  - 只动 chief_baiji 本人，`_mahan`、`_lelang` 不改；
  - 05:185 的前置检查：先核 `baekje` 文化、`korean_buyeo` 王朝的本地化和纹章；
  - 与 346 节（`zz_hd_346_titles.txt:207` 和 346 的 undo）的改法一起核对；
  - 由 5-A1 或汇总人执行。
- 第二节第 16 行的处理栏同步改为「titles 与 undo，补全为 8 行」。

**2.【minor，已修】乞伏国仁一行**
- 采用审查给的第二种办法：COURT 由苻坚 `lueyang_fu_020` 改为其父乞伏司繁 `qifu_004`。
- 已核：司繁 349–376 在世，是 `zz_hd_370_titles.txt:231` d_longdong 的独立持有者。
- 这一行只用于引擎没给他雇主的情况；引擎已安置时只记 SKIP。
- 行尾注释写明了用途，报告第三节名单和第四节第 10 条也已更新。
- 暂存文件 BOM 和 LF 不变，括号 89/89。

**附带修正**：报告结论段的笔误「404 节」改为「04、06」。

## 仍未解决项
- 本路不能写的移交仍在第五节，需汇总人或其他路处理：
  - 第 1 条：E3-J80 和读 fangtou_gong 的地方，要加 370 开局的放开条件；
  - 第 3 条：节点里入宫廷前先判雇主；
  - 第 6 条：百济 8 行；
  - 第 7 条：司马奕廷臣在废立后的去向。
- 首测项见第五节第 5 条。

## 闸门结果
- 改动后重跑 `gate.py --overlay p5-D --compare baseline.json --only-changed`：errors 0，counts 为空，即相对基线新增 0 条，resolved_vs_baseline 0。
- 输出在 D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p5-D_gate.txt

---

# p5-D「370 开局内容」实施报告（合并更新后全文）

报告文件：D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p5-D_report.md

**结论**：370 开局在本路能做的只有宫廷安置一件事。它写进了 `hd_j16_startup_370_effect`，放在历史入侵预设块之后，外面包了规则开关。04、06 里没有任何要在 370 开局授郡或任命的内容，所以本期不授郡、不任官，也不补设结果变量。闸门相对基线没有新增。

## 一、暂存任务名与文件
- 暂存任务名：**p5-D**。只有一个文件：
  - edit `common/scripted_effects/zz_hd_j16_startup_370_effects.txt`（BOM、LF 不变，括号 89/89）。
- 暂存副本：D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p5-D\files\common\scripted_effects\zz_hd_j16_startup_370_effects.txt
- 没有新建 370c 的事件、yml、触发器文件。
- 没有直接写 mod，没有跑生成器，没有开游戏，没有提交。
- 闸门：第三轮改动后重跑，errors 0，相对基线新增 0 条。
- 执行顺序已核实：冻结文件里 `hd_370_after_lobby_effect` 的最后一行才调本入口，排在旧宫廷安置、桓温权臣装配和任命之后。

## 二、「370 开局」项清单

| # | 来源 | 内容 | 处理 |
|---|---|---|---|
| 1 | 04:308 | 燕凤作什翼犍廷臣 | 已实施 |
| 2 | 04 节点表各行的当事人条件 | 当事人入宫廷 | 已实施（自拟） |
| 3 | 06:254、04 覆盖表 :19/:21 | `hd_hi_done_*` 预设 | 第 1 期已有，未改 |
| 4 | 01 §3.2、03 跨开局列 | 旧节点前标 | p1-S 已做 |
| 5 | 03:232 | J45 桓温权臣 | 旧开局已做，不设结果变量 |
| 6 | 04:77/:78 | E3-M85、E4-M05 | 归 5-A1 |
| 7 | 04:92 | E4-Q50 淝水 | 归 5-A1 |
| 8 | 04:96 | W50 的 404 开局设置 | 归 6-B |
| 9 | p4-A 报告 | 导演 stage 置 3 | 4-A 已做 |
| 10 | 04 §4、p5-B | 罗什开局县 | 等 F-3 重跑生成器 |
| 11 | 04 §8.2 | 吐谷浑持有者 | 2-A 已做 |
| 12 | p3-D 报告 | 什翼犍京城 1333 | 汇总人定不改 |
| 13 | 04 授郡 | — | 都在节点里做，开局不做 |
| 14 | 04 E4-J40 | 任命 | 开局不做 |
| 15 | 06 §4 | — | 对 370 开局无新增项 |
| 16 | 03 §6 #21、05:185 | 百济持有者换人 | titles 与 undo 共 8 行，交第五节第 6 条 |

## 三、实施内容

**入口改动**：加了一段

```
if = { limit = { hd_history_events_enabled_trigger = yes } hd_j16_370c_court_place_effect = yes }
```

**`hd_j16_370c_place_effect = { WHO COURT CROSS KNIGHT }`**
- 对 WHO：在世、无地、`is_ruler = no`。
- 对 COURT：在世、有地、不是 WHO 本人，WHO 也还不在这个宫廷。
- 执行条件，满足其一即可：
  - WHO 没有雇主；
  - `CROSS = yes`，且 WHO 已成年、雇主不在 COURT 的最高领主治下。
- 执行用 `add_courtier`；KNIGHT = yes 且已成年时再设 `set_knight_status = force`。

**`hd_j16_370c_move_effect = { WHO FROM COURT }`**：WHO 的雇主是 FROM 或没有雇主时，改入 COURT 宫廷。

**安置名单**：
- **苻坚宫廷**：
  - 苟太后、姚兴；
  - 武将，设骑士：张蚝、梁熙、苟苌、梁成、朱肜、彭超、俱难、苟池、杨安（唯一一个 CROSS = yes）；
  - 苻登，不设骑士。
- **乞伏司繁 qifu_004 宫廷**：乞伏国仁，只作兜底（第三轮改）。
- **王猛宫廷**：邓羌，设骑士。
- **桓温宫廷**：何谦设骑士；刘牢之不设骑士；桓熙、桓玄。
- **桓豁宫廷**：朱序、谢玄设骑士；冯该不设骑士。
- **周楚宫廷**：杨亮设骑士；杨佺期不设骑士。
- **司马昱宫廷**：谢石、谢琰、王恭、王国宝、殷仲堪、孙泰。王坦之、褚蒜子用 move 改投过来。
- **什翼犍宫廷**：燕凤、许谦、刘库仁、拓跋寔君。
- **杨纂宫廷**：杨统。
- **慕容暐宫廷**：慕舆文、高盖、韩延，都不设骑士。

## 四、自拟与偏差
1. **安置规则**
   - 只安置还没有雇主的人；
   - 只有杨安一人跨政权改投；
   - 接收者：节点或史料写明的上级在世且有地，就归这位上级，否则归本政权之主；
   - 成年武将设为骑士，已知有阵亡风险。
2. **晋方的「本政权之主」取司马昱，不取司马奕**：废立效果不搬司马奕的廷臣，司马昱的宫廷就是 371 年的新帝宫廷。
3. **覆盖了旧开局的一处安置**：王坦之改投司马昱。褚蒜子 history 里的雇主是已死的司马聃，同样处理。
4. **慕舆文、韩延、冯该不设骑士**：他们是卒年 K 类的凶手，要活到 384–386 年。
5. **安置包在规则开关里**，与 p3-C 的 304 安置不同。
6. **燕廷三人**之后的去向只记录，不另处理。
7. **许谦**是 06 附表的人物，一并放入什翼犍宫廷。
8. **原生无雇主、未安置的人**：宋氏、刘允、尹纬、杜进、段业、辟闾浑、张贵人，以及 360–370 年出生的幼童，理由见报告。
9. **苻登、刘牢之、杨佺期不设骑士**：三人在 383 年以后仍是节点当事人。谢玄保留骑士，已知有风险。
10. **（第三轮）乞伏国仁的接收者改为其父乞伏司繁**
    - 原写法在引擎未安置时，会把独立君主的继承人送进苻坚宫廷，不合史实。司繁到 371 年才降秦。
    - 现在只作兜底，正常情况下这一行记 SKIP。

## 五、需要汇总人处理的事项
1. **【核对 5-A1】枋头相关变量在 370 开局不设**
   - E3-J60 在 370 开局只由自保护设 done，`yuanzhen_blamed`、`fangtou_gong`、`fangtou_won/_lost` 都不会设上。
   - E3-J80、袁真特例、读 `fangtou_gong` 的地方，都要写成「变量已设，或 `global_var:hd_j16_start_year >= 370`」。
   - 落盘前请再核一次。
2. **`hd_j16_huanwen_regent_result`、`hd_j16_chui_benqin_result` 在 370 开局不设**
   - 下游一律按 `hd_court_is_regent_trigger` 判桓温状态。
   - E4-J10 已核，写法一致。
3. **【交 5-A1/5-A2】节点里凡是「入某宫廷」的，add 之前先判 `NOT = { employer ?= 接收者 }`**
   - 涉及 E4-Q30、J60、T20、J97 等。
   - 已在两路暂存中落实。
4. **生成器**：本路没有新建人物，不需要重跑。
5. **首测项**
   - game.log 搜 `HD_J16 startup_370`，看各人是 FIRE 还是 SKIP；
   - 杨安是否改投到秦；
   - 王坦之、褚蒜子在废立后是否仍在晋天子领内；
   - error.log 里有没有 add_courtier、set_knight_status 报错。
6. **【交 5-A1 或汇总人】百济持有者换为 korean_buyeo_49**
   - 共 8 行：
     - `zz_hd_370_titles.txt` 的 :82、:524、:525、:526；
     - `zz_hd_370_undo.txt` 的 :75、:515、:516、:517。
   - 只动 chief_baiji 本人那几行。
   - 改之前先核 baekje 文化、korean_buyeo 王朝的本地化和纹章。
   - 与 346 节的改法一起核对。
7. **【建议交 5-A1，E4-J10】司马奕原有廷臣的去向**：在 `hd_j16_feili_proceed_effect` 里，把司马奕无地、非家属的成年廷臣 add_courtier 给新帝，事先判雇主。

## 六、面板行清单（交 F-1）
- 无。开局不设任何 `hd_hev_*`。
- 04 §1.5 建议的 370 组 06–10 行，以及 E5 组 `hd_hev_grp_j16_e5j` 的各行，都在节点 fire 时设置，归 5-A1 / 5-A2。

## 七、新增事件号与变量名
- 事件号、本地化键、全局变量、人物变量、旗标：全部无。
- 新效果 3 个：`hd_j16_370c_court_place_effect`、`hd_j16_370c_place_effect`、`hd_j16_370c_move_effect`。
- 新 saved scope 3 个：`hd_j16_370c_court`、`hd_j16_370c_top`、`hd_j16_370c_who`。没有占用 `hd_fo_*` 那 5 个名字。
- 日志键：`HD_J16 startup_370 FIRE court_place`、`FIRE|SKIP place_<ID>`、`FIRE|SKIP move_<ID>`。
- 04 编号式旧名→语义名对照：本路没有节点，不涉及。

## 八、卒年表 PRE 变量
- 本路没有节点，不设任何 PRE。
- 卒年在 360–370 之间、带 PRE 的只有张玄靓（`tianxi_result`，卒 363）和四公（`sigong_result`，卒 368）两组，370 开局时都已死。
- 因此没有任何一行会因 370 前标而永远拿不到 PRE。
- 也没有发现 tsv 的 PRE 名与 TEMPLATE §5-15 不符、需要改 tsv 的情况。
