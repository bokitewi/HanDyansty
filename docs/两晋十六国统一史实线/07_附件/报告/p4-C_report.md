# p4-C 最终报告（修正后合并版）

# p4-C 修正轮报告（第 4 期第二轮，4-C「四名可选人物与刘玄」）

暂存任务名：**p4-C**。只改了暂存区：D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p4-C\files\

本轮改了 2 个暂存文件，都保持 UTF-8 带 BOM、LF，括号配平：
- common/scripted_effects/zz_hd_j16_346c_effects.txt（现为 2382 行）
- events/zz_hd_j16_346c_events.txt

其余 14 个暂存文件本轮没有动。

## 甲、审查意见逐条处理

**1. [major] 玩家刘群 X50 问得太早 —— 已修。**
- 改在 `hd_j16_node_liuqun_zhandui_effect` 的玩家分支。
- 现在满足下面任一条件才设 done 并发 hd_j16.1380：
  - 已有 `hd_nbc_ranmin_done`，且魏主（hd_nbc_ran_min）有地、独立；
  - 或日期已到 350.10.1（这时还没有魏，a 不显示）。
- 等待期间不设 done，只走 `hd_j16_304_wait_effect = { KEY = liuqun_zhandui_wr LOG = e3_x50 WHY = wait_ranmin }`（用单独的 KEY，等待日志单独记一次）。
- `hd_j16_liuqun_wei_ok` 仍在发问前按头衔层级判定。
- 节点头注释已同步。

**2. [minor] L90/L91 同年可能连打三场 —— 已修，用了两道闸。**
- L90 节点：窗口内若 `hd_j16_maqiu2_started` 已设，直接 `hd_j16_304_skip_effect = { KEY = maqiu ... WHY = superseded_by_l91 }`。
- L91 的「再战」分支：调用 ready 之后，若 maqiu2 已开战、L90 从未开成、也未 done，就给 L90 设 done 和 skip（WHY 同上）。
- 另外新增一处等待：L90 还在问玩家攻方时（`hd_j16_maqiu_asked`、`_go`、`_wait` 任一存在，且 L90 未 done），L91 先等，WHY = l90_player_pending。这样 1305 不会同时挂两问，maqiu2 的问也不会被 maqiu 的答复吞掉。
- L91 头注释已同步。

**3. [minor] X55 在 304 局的处理与晋天子好感 —— 好感已修，节点偏离请汇总人确认。**
- 节点结构重写为：
  - 304 局首跳只给刘群加 `hd_j16_yuesi_modifier`，并设新变量 `hd_j16_yuesi_mod304`；
  - 晋天子好感一律等到 346.12.10–347.6.1 窗口内，由当时的晋天子补加，不再记在司马衷身上；
  - 窗口规则、actor_dead、window_closed 两种开局统一。
- 顺带改了面板：fire 改在窗口内，所以 `_result` 和面板 `hd_hev_j16_yuesi` 两种开局都设（原先 304 局不设）。
- 没有改动 3-C 的 startup_304，偏离任务「只列给汇总人」，见丙节第 1 条。

**4. [minor] hd_asp.0317 第 1108 行注释已过时 —— 未改，列给汇总人。**
- 本路只获准改第 1109 行，所以没动。
- 合并时请把第 1108 行注释改为「修正在 zz_hd_j16_346c_modifiers.txt（4-C），已启用」。

**5. [minor] 1310 b 下狱分支白给 5000 兵 —— 已修。**
- 现在只在张祚有地、且已与 root（张耀灵）交战时，才在首府生成 `hd_j16_346c_army_xieai`。
- 下狱分支不给兵。

**6. [minor] 刘群、刘玄出生即带成年性格和教育 —— 未改，列为实测项。**
- 不改的理由：
  - 原版 `childhood_education.0007` 只在角色没有任何教育特质时才补，并移除童年特质，所以不会出现两个教育特质。
  - 若把特质挪到 311/316 的历史条目，304 局按未来日期不执行，hbirth 也不管已出生的这两人，304 局反而会丢掉这些特质。
- 实测时重点看：304 局两人 16 岁后的性格是否超过 3 项，以及 `education_point_acquisition_effect` 有没有升降教育档位。

**7. [minor] 刘群附魏、降秦受头衔层级限制 —— 确认属实，未越权，仍请汇总人定。**
- 现状：346 局刘群持王国 k_qinzhou，而冉闵、苻健都只是郡级，按报错清单不能收编刘群。
- 可选做法：
  - (a) 由 4-B 在冉闵称帝时，用 create_dynamic_title 把魏升到王国以上；
  - (b) 本节点 fire 前先把刘群的主头衔降为 d_long1，把王国交给魏主，再收编。
- 两种都需要拍板。在定下来之前，major 修复只能保证玩家等得到魏，a 仍可能因层级不显示。

## 乙、仍未解决

- 第 4、6、7 条见上。
- X55 是否保留在节点内，见丙节第 1 条。

## 丙、自拟与偏差（合并更新后全文）

1. **E2-X55 的 304 局处理**
   - 做在节点里，没有改 startup_304。304 局首跳只加修正（设 hd_j16_yuesi_mod304）；晋天子好感与 `_result`、面板都在 346.12.10–347.6.1 窗口内 fire 时设，两种开局相同。
   - 如果汇总人更想放进 startup_304：把首跳加修正那段挪进去即可，节点里的 mod304 判断可以保留。
2. **凉胜受赏**：L90、L91 任一场攻方败且没有求和时发，只发一次。内容为谢艾加威望、`hd_j16_xieai_modifier`、unyielding_defender 特质；凉主加威望。03 只把它写在 L91。
3. **攻方或夺位者是玩家时都给选项**
   - 攻方是玩家时问 1305（a 出兵 / b 90 天后再问）。
   - 张祚、张瓘、宋混、张天锡、杨俊作为夺位者是玩家时也给 a/b（1311、1316、1315、1314、1357）。
   - 张瓘起兵时张祚是玩家，则打内战并给通报 1313。
   - 本轮新增：L90 还在问玩家时 L91 先等；L91 开战后 L90 作废（superseded_by_l91）。
4. **c「求和」**：用 end_war 白和。边境 CB 的白和本身会让攻方赔小额金，另外凉主付攻方中额金、失中额威望。
5. **L10 的偏离分支预设卒年 done**
   - 谢艾受信（hd_j16_xieai_trusted），或玩家选「讨祚」「不动」时：预设耀灵、谢艾的 done。
   - 玩家耀灵「禅让」时只预设耀灵的 done，谢艾照表处死。
   - 本轮新增：1310 b 的 5000 兵只在内战真打起来时给。
6. **L20**：玄靓取不到时头衔交张瓘。「专政」修正借用 `hd_j16_zhuanquan_modifier`，5 年。
7. **X20**
   - a 的谋略检定：基础 50%，谋略 ≥12 时 +25。
   - b 里杨宋奴「出奔」用 move_to_pool。
   - c 只能选一次，选后窗口延到 356.12.31。
   - a、b 预设杨初的卒年 done，不设 PRE。
8. **X30 b**：杨俊有地时打内战并给 3000 兵；无地时只得宣称、出奔。
9. **X50 a「尚书左仆射」**：取议会 councillor_steward。本轮新增：玩家等魏（或到 350.10.1）后才问。
10. **X50 a、X57 a**：只在新主头衔高于刘群时才成立（AI 取 a 的条件、玩家 a 是否显示都按这一条）。346 局多半落空，请汇总人定（甲第 7 条）。
11. **X70**：改宗主用自建的 `hd_j16_346c_join_lord_effect`。c「隐居」用修正（学识 +2，10 年）加减压。
12. **304 局刘玄、李氏补婚**（hd_j16_346c_marry304_effect）：318–330 年间，两人都在世、成年、未婚时补。
13. **「举汉帜」改为每个主头衔一次**
    - 封臣一支：发起 independence_war，5 年冷却。
    - 已独立一支：found_realm（STYLE=wang，FIXED=no），并设 `hd_j16_lxuan_han`。
    - 定号直接 set_title_name = dynn_title_han，不受 TGP 占用影响，不需要另建国号键。
14. **「蜀中起兵」**
    - 代价：金 100、威望 300。
    - 取县顺序：所在县 → 蜀郡 → 益州；只取非独立 AI 持有、且非其首府的县。
    - 取县后即独立，得该郡宣称，在当地生成 3000 兵，并发通报 1401。
15. **性格第三项**（just、ambitious、honest、shy）为自拟。
16. **L15 张祚改元「和平」**：没做，年号键还没注册。
17. **startup_346 宫廷安置**
    - 用 add_courtier，排除统治者、囚犯、议政大臣、已在该宫廷的人。
    - 主人无地时改放宗主宫廷，且只放无雇主的人。
    - 孙盛取 sun_sheng_2。
18. **麻秋接管金城**：放在规则 if 之外。
19. **刘群、刘玄童年特质**：出生时加童年特质，同时带成年性格和教育（甲第 6 条，待实测）。

## 丁、本期面板行清单（交 F-1，只列不写，均为 le346，前缀 hd_hev_j16_）

maqiu（麻秋压境开战）、maqiu2（枹罕再战）、xieai_chan（谢艾出守酒泉）、liang_jiawang（张重华称假凉王）、longli（龙黎之战）、zhangzuo（张祚夺位）、zhangzuo_wang（张祚称凉王）、zhangguan（张瓘讨祚）、songhun（宋混诛瓘）、tianxi（张天锡自立）、qiuchi_fanchen（杨初附晋）、xicheng（袭西城）、liangshiwang（梁式王之变）、yangjun（杨俊杀杨国）、yuesi（刘越石之子；现在两种开局都只在窗口内点亮）、liuqun_zhandui（刘群附魏）、liuqun_qin（刘群降秦）、lxuan_qiuliu（刘玄去留）。

## 戊、需要汇总人处理

1. **交 4-B 加两行调用**：
   - `hd_j16_e2_346_effect` 末尾：`	hd_j16_e2_346c_effect = yes     # 4-C 四人与刘玄（E2-L90～L92、X05、X55、X70）`
   - `hd_j16_e3_346_effect` 末尾：`	hd_j16_e3_346c_effect = yes     # 4-C 四人与刘玄（E3-L05～L40、X10～X57）`
2. **重跑生成器**：先 hbirth，再 popclean。原因是四人加了特质和能力值，宋氏、强氏改了生年，杨国、耀灵、1800077 补了母亲指针。
3. **年号「和平」**
   - 在 WJ_tianjia_era_names.txt 注册 SG_nianhao_heping（正文和 _tt 两处，加中英本地化）。
   - 注册后在 `hd_j16_zhangzuo_wang_effect` 加一行：`if = { limit = { is_independent_ruler = yes } hd_370_change_era_effect = { KEY = heping YEAR = 1 } }`。
4. **交 4-B（E3-M20）与头衔层级**
   - 刘群「仕魏」可读 `hd_j16_liuqun_wei`。
   - 头衔层级的限制（甲第 7 条）请拍板：魏升王国，还是刘群先降为 d_long1。
   - 不处理的话，346 局 M20 会走预设 done，刘群按 D15 至 362 年。
5. **防重名**：确认 4-B 没有重复定义 `hd_j16_xieai_modifier`、`hd_j16_jin_fanchen_modifier`、`hd_j16_yuesi_modifier`、`hd_j16_hanshi_yuyin_modifier`（都在 zz_hd_j16_346c_modifiers.txt）。
6. **hd_asp.0317 第 1108 行注释**：按甲第 4 条更新。
7. **OE 重导入防复发**：zz_hd_oe_characters.txt 里 1800077 新加的 mother 行会被 import_oe.py 冲掉。
8. **304 开局**：本路没有改 startup_304，请确认丙节第 1 条的偏离。

## 己、新增事件号、变量名

**事件号**
- 已用：hd_j16.1300–1305、1310–1316、1350、1352、1354、1356、1357、1380、1382、1400、1401。
- 其余（1306–1309、1317–1349、1351、1353、1355、1358–1379、1381、1383–1399、1402–1419）未占用。

**节点变量**（各带 _done/_skip/_wlog，下列为另有的后缀）
- 战争类：maqiu、maqiu2、longli、xicheng 各带 _started/_won/_lost/_att/_def/_go/_asked/_wsf_wlog。
  - maqiu、maqiu2 另有 _wait/_peace/_xieai；maqiu2 另有 _result。
  - longli、xicheng 另有 _rolled。
- fire 结果 _result：xieai_chan、liang_jiawang、zhangzuo、zhangzuo_wang、zhangguan、songhun、tianxi、qiuchi_fanchen、liangshiwang、yangjun、yuesi、liuqun_zhandui、liuqun_qin、lxuan_qiuliu。
- 其他：
  - yaoling_heir_*、xieai_trusted、xieai_rewarded；
  - liangshiwang_asked/_delay/_c_used；
  - liuqun_wei、liuqun_wei_ok、liuqun_qin_ok；
  - lxuan_wed_done；
  - border_&lt;KIND&gt;_target（4-A 工具设）、hd_nbc_&lt;KIND&gt;_active。
- 本轮新增：hd_j16_yuesi_mod304、hd_j16_liuqun_zhandui_wr_wlog、hd_j16_maqiu2_l90_wlog（后两个是等待日志）。

**人物旗标**：hd_j16_lxuan_juhanzhi_used、hd_j16_lxuan_indep_war（5 年）、hd_j16_lxuan_qibing_used。

**头衔变量**：hd_j16_lxuan_han。

**03 编号 → 语义名**

| 03 编号 | 语义名 |
|---|---|
| E2-L90 | maqiu |
| E2-L91 | maqiu2 |
| E2-L92 | xieai_chan |
| E3-L05 | liang_jiawang |
| E3-L08 | longli |
| E3-L10 | zhangzuo（R-继统 yaoling_heir） |
| E3-L15 | zhangzuo_wang |
| E3-L20 | zhangguan |
| E3-L30 | songhun |
| E3-L40 | tianxi |
| E2-X05 | qiuchi_fanchen |
| E3-X10 | xicheng |
| E3-X20 | liangshiwang |
| E3-X30 | yangjun |
| E2-X55 | yuesi |
| E3-X50 | liuqun_zhandui |
| E3-X57 | liuqun_qin |
| E2-X70 | lxuan_qiuliu |

## 庚、卒年表 PRE 的设置处

本轮重新 grep 了暂存副本：每个变量只在对应执行体里设一次；跳过、前标、偏离分支都不设。

| PRE | 设置处（zz_hd_j16_346c_effects.txt） | 卒年表行 |
|---|---|---|
| hd_j16_zhangzuo_result | :950 `hd_j16_zhangzuo_effect` | 张耀灵、谢艾 |
| hd_j16_zhangguan_result | :1107 `hd_j16_zhangguan_effect` | 张祚 |
| hd_j16_songhun_result | :1225 `hd_j16_songhun_effect` | 张瓘 |
| hd_j16_tianxi_result | :1331 `hd_j16_tianxi_effect` | 张玄靓 |
| hd_j16_liangshiwang_result | :1655 `hd_j16_liangshiwang_effect` | 杨初、杨宋奴 |
| hd_j16_yangjun_result | :1770 `hd_j16_yangjun_effect` | 杨国 |

- hd_j16_liantai_result（刘群）归 4-B。
- 偏离分支预设的 done：hd_nbc_death_anding_zhang_011_done、hd_nbc_death_hd_j16_xie_ai_done、hd_nbc_death_chouchi_yang_052_done、hd_nbc_death_chouchi_yang_054_done。

## 辛、闸门

- 已按原命令复跑，输出在 D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p4-C_gate.txt。
- 结果：overlay 16 个文件，相对基线新增 error 15、warn 55（修正前 warn 57）。
- **15 条 error**：与修正前同一批，只是行号变了，都是 gvar_read_never_set 的参数名误报。这些变量由 `hd_j16_$KIND$_*`、`hd_j16_$KEY$_asked`、4-A 工具的 `hd_j16_border_$KIND$_target` 设置，闸门看不到：
  - maqiu、maqiu2、longli、xicheng 的 _started/_lost/_won/_att/_asked；
  - border_*_target；
  - liangshiwang_asked。
- **warn 少了 2 条**：L91 现在直接读 hd_j16_maqiu_go、_wait。
- **其余 55 条 warn**：都可解释，包括面板 hd_hev_*、PRE _result（经 deaths 宏参读取）、_skip、_att/_def、预设的卒年 done，以及交 4-B 的 hd_j16_liuqun_wei。

## 壬、待实测

1. 346 首跳麻秋战能否开成，实际取到哪一县。
2. 封臣麻秋对独立凉主用 start_war。
3. 给只持世族头衔的刘玄做 change_liege。
4. add_courtier 宫廷安置。
5. 「蜀中起兵」后无地者取县并独立。
6. 脚本发起的 independence_war。
7. 1400 卡面提示能否显示。
8. 304 局刘玄补婚。
9. 本轮新增：
   - 304 局刘群、刘玄成年后的特质数量与教育档位；
   - 玩家刘群在冉闵建魏后收到 1380；
   - L90 未开成时 L91 开战，之后 L90 不再开战。