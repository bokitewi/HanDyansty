# p3-B1 最终报告（修正后合并版）

p3-B1 修正报告：304 节点（晋、汉赵、后赵、乱世锁），第 3 期第二轮

# 〇、逐条处理审查意见

8 条审查意见全部处理：2 条 major 已修；6 条 minor 中 5 条已修，1 条（王敦）只调了顺序和注释，写进已知局限。所有改动都在暂存区。

1. 【major·已修】E2-J60 成帝、康帝两次继统
   - 外层闸门先解析再判：hd_j16_304_res_effect 存 scope:hd_j16_ck_yan（si_ma_yan_4）和 scope:hd_j16_ck_yue（si_ma_yue_2），limit 改成 scope:... ?= { has_title = title:h_china }。
   - 原写法 character:ID 在 304 局取不到这两个 hbirth 人物。hd_j16_b1_heir_effect 内部本来就是解析的，没动。
2. 【major·已修】E2-J40 苏峻宣战失败后无法重试
   - 本节点让苏峻独立时，设全局变量 hd_j16_sujun_rose。
   - 苏峻的局面条件改为两种情况之一：
     - 仍是天子封臣，且 is_at_war = no；
     - 已设 hd_j16_sujun_rose、是独立君主，且没在和天子交战（NOT is_at_war_with）。
   - 已独立时不再重复调用独立效果。
   - 第二种情况只认本节点造成的独立，避免别的原因独立的苏峻被误触发。
3. 【minor·写入已知局限，只调顺序】E2-J30 王敦开战前先解辅政
   - 曾试过改成开战成功后才解辅政，后来撤回。原因：权臣在任时，AI 天子是他的傀儡（puppet），两头政治（diarchy）也没解除，必须先清掉才能保证明帝能宣战。
   - 现在的顺序：先解辅政，再独立（已独立就跳过独立），再宣战。
   - 注释写明：宣战失败不回滚，下一跳按 is_independent_ruler 重试；一直开不成的话，窗口关闭后王敦是无战争的独立势力，辅政已被解除。
4. 【minor·已修】E2-Z50 缺第二条上游
   - 上游条件改为二选一：
     - 已设 hd_j16_shihu_zhuan_result；
     - 弘存在，且虎的 sub_realm_size ≥ { value = 弘.sub_realm_size multiply = 0.5 }。
   - 这种「触发器里拿内联脚本值比较」的写法，原版有先例（00_tributarize.txt:43 的 realm_size <= { value = scope:attacker.realm_size ... }）。
5. 【minor·已修】称号类节点改走 hd_nbc_found_realm_effect

   | 节点 | NAME | STYLE | FIXED |
   |---|---|---|---|
   | J15 司马保 | dynn_title_jin | wang | no |
   | H10 靳准 | dynn_title_han | tianwang | no |
   | Z30 石勒（执行体 hd_j16_shile_emperor_effect） | dynn_title_zhao | $STYLE$ | yes |
   | Z50 石虎 | dynn_title_zhao | tianwang | yes |

   - 都不造头衔。
   - J10 晋王（第 1 期原有节点）不改：司马睿可能仍是封臣，不应被换政体。
6. 【minor·已修】建武年号说法更正
   - 核实结果：SG_nianhao_jianwu 这把全局锁，在 304 开局时就由 hd_304_era_effect → hd_nbc_set_era_effect 设上了，到 404 年失效，与 J10 无关。
   - 这把锁只把建武排除出随机年号池（WJ_tianjia_era_effects）。后赵 335 建武是直接设人物变量，不受影响。
   - b1 改元效果的实际作用只是「不把锁续到 417 年」。
   - J10 注释、Z50 注释、b1 效果注释都已改成这个说法。
7. 【minor·已修】决议 B 的两处过时注释
   - 文件 common/decisions/zz_hd_j16_304_decisions.txt 新登记为 edit，原样 UTF-8 带 BOM、LF，只改了两行注释。
   - 现在写的是新选法：京城郡（干净，且郡内有县属天子一方）优先；否则权臣首府郡；无权臣取颙首府郡；不看接壤。另一处：无目标或宣战失败时退还威望。
8. 【minor·已修】character:ID 直取改为解析
   - E2-J20：刘隗、刁协 → scope:hd_j16_wd_liu、scope:hd_j16_wd_diao。
   - E2-H60：刘曜 → scope:hd_j16_sg_yao。
   - e1 张背督观察块：石勒 → scope:hd_j16_bd_le。
   - 复查用 grep -nP '^[^#]*character:'，e1、e2 两个文件都已清零。

# 一、暂存任务与文件

暂存任务名：p3-B1。暂存目录：D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p3-B1\files。
没有直接写 mod，没有跑生成器，没有开游戏，没有提交 git。

共 11 个文件，全部是 edit：
- common/scripted_effects/zz_hd_j16_e1_304_effects.txt
  - B2 返工；
  - W10 改写；
  - 新增 8 个 E1 节点；
  - 张背督观察块；
  - 刘聪立储节点加靳准摆位；
  - 处决块加索綝；
  - 入口末尾调用 hd_j16_e1_304b_effect。
- common/scripted_effects/zz_hd_j16_e2_304_effects.txt
  - 整文件重写：J10 照旧，只把改元换成 b1 效果；
  - 新增 24 个 E2 节点、E2 处决块和本路小工具 hd_j16_b1_*；
  - 入口加 hd_j16_restore_tributary_effect，入口末尾调用 hd_j16_e2_304b_effect。
- common/decisions/zz_hd_j16_304_decisions.txt：本轮新增，只改决议 B 的两行注释。
- events/zz_hd_j16_304_events.txt：新增 18 个事件。
- 本地化中英两份（zz_hd_j16_304_l_simp_chinese.yml / zz_hd_j16_304_l_english.yml）：
  - 各新增 85 键，两份都是 229 键，一一对应；
  - 改了决议 B 的 tooltip。
- common/scripted_triggers/zz_hd_j16_304_triggers.txt：删 border_county 触发器，新增 hd_j16_yingjia_valid_duchy_trigger，保留 clean_duchy。
- common/modifiers/zz_hd_j16_304_modifiers.txt：新增 3 个修正（君子营、轻信、专权）。
- common/casus_belli_types/zz_hd_nbc_war_cb.txt（授权）：on_victory 里，kind 为 yingjia 时跳过领地转移。
- common/scripted_effects/zz_hd_nbc_history_effects.txt（授权）：分发表加一行 KIND = yingjia。
- common/on_action/zz_hd_history_events_rule_on_actions.txt（授权）：规则关闭时的兜底改为调用 hd_j16_mandate_lock_check_effect。

编码：全部 UTF-8 带 BOM、LF，大括号平衡已核。四个共享文件与 mod 原件 diff 后只剩预期改动。旧 304 事件文件不在清单里。

# 二、闸门结果

- **单跑**（p3-B1_gate.txt）：error 13，warn 75，相对基线消掉 9 条旧问题，与修前一致。
  - ref_scripted 2 条：hd_j16_e1_304b_effect、hd_j16_e2_304b_effect，是 3-B2 的入口。
  - gvar_read_never_set 11 条，都是带参数的变量名，闸门跳过不统计，属误报：
    - hd_nbc_yingjia_won/_lost/_white/_invalid：由分发表的 $KIND$ 设置；
    - changan316、bingzhou316、luoyang328、wangdun2 的 _won：由结局宏的 $KIND$ 设置；
    - jingzhen1、jingzhen2、huanwen_jing 的 _asked：由跳效果的 $KEY$ 设置。
  - warn 75 条都是只写不读，读取方是面板（F-1）和日后可能补的 PRE。新变量 hd_j16_sujun_rose 有写有读，没有增加 warn。
- **与 B2 合跑**（--overlay p3-B1 p3-B2，p3-B1_gate_b1b2.txt）：error 25，全部是带参数变量的误报（本路 11 条，B2 的 *_heir_done 14 条）；ref_scripted 0；消掉旧问题 10 条。
- **p3-B1 必须与 p3-B2 同批落盘。**

# 三、实现概要

## B2 迎驾之战返工

1. **CB 改动**
   - on_victory 里六段转移包进条件 `if NOT { AND { exists = root.war  root.war.var:hd_nbc_war_kind ?= flag:yingjia } }`。六段是：create_title_and_vassal_change、conquest_cb_title_transfer、去国号、vassals_taken、titles_taken、resolve。
   - 停战和 hd_nbc_war_result_effect 留在包裹外面，对所有场次照常执行。
   - 其他场次除缩进外逐字不变。
   - 原版 00_civil_war.txt 的 CB 结算里就在用 root.war。
2. **分发表**加一行 KIND = yingjia。
3. **直接宣战**：hd_j16_yingjia_start_war_effect
   - 照 hd_nbc_start_war_effect 去掉 wct 一步：break_alliance，再 start_war（cb = hd_nbc_war_cb，target 为天子，target_title 为目标郡）。
   - 然后设 kind 为 yingjia，存 scope:hd_nbc_war_yingjia（宣战前先清掉旧的），设 hd_nbc_yingjia_active，记 HD_NBC WAR_CONFIRMED / WAR_START_FAILED 日志。
   - 目标郡由 hd_j16_yingjia_pick_target_effect 选：
     - 守方取现任权臣，没有权臣时取颙；
     - 京城县所在郡优先，条件是 clean_duchy 且 valid_duchy（valid_duchy 等价于 CB 的 should_invalidate）；
     - 否则取守方首府所在郡（须满足 valid_duchy）；
     - 取不到就等待，日志 WAIT no_target。
   - 0103 选项 a、决议 B 共用这套选法。
4. **结局**：hd_j16_yingjia_result_effect
   - hd_nbc_yingjia_won 记为 _won；_lost、_white、_invalid 都记为 _lost。
   - 兜底：攻守双方都已不在 yingjia 场次的战争里、又没有任何结果旗标，记 lost 并自清 _active。
   - _key、yj_key、yj_atop 已删：已 grep，B5、B6、决议 C 不读它们。
5. border_county 触发器已删，clean_duchy 保留；hd_court 没有动。

## E1-W10 乱世锁

- 新写 hd_j16_mandate_lock_check_effect：hd_j16_jinjian_done 已设，或 ≥320.1.1，即解锁。
- 心跳节点和规则关闭兜底调用的是同一个效果。规则关闭时 J3 不跑，所以按 320.1.1 解锁。
- 旧的 hd_304_lock_check_effect 现在无人调用。

## 节点

E 号以 02 §0.3 为准，写法照 TEMPLATE：
- 346 及以后开局自保护，只设 done；
- 等待式窗口，止日按次日判；
- 解析前先清 scope；
- WAIT 只记一次日志；
- _result 和 hd_hev_* 只在 fire 时设。

E1（共 8 个）：
- E1-J30 愍帝即位
- E1-J35 祖逖北伐
- E1-J40 刘曜破长安（KIND = changan316）
- E1-H60 刘乂之废
- E1-Z10 张宾归石勒
- E1-Z20 葛陂退兵
- E1-Z30 袭蓟擒王浚（KIND = jicheng）
- E1-Z40 取并州（KIND = bingzhou316）

E2（共 24 个）：
- J 线：
  - J11 东晋建立
  - J15 司马保称晋王
  - J20 王敦之乱（一）
  - J25 明帝立
  - J30 王敦之乱（二）（KIND = wangdun2）
  - J35 庾氏秉政
  - J40 苏峻之乱（KIND = sujun）
  - J50 荆州镇守两跳
  - J60 成帝、康帝两次继统
  - J70 桓温出镇荆州
- H 线：
  - H10 靳准之乱
  - H20 刘曜即位
  - H30 迁长安、改国号赵
  - H40 刘曜西征
  - H50 洛阳之战（KIND = luoyang328）
  - H60 前赵亡（KIND = shanggui329）
- Z 线：
  - Z10 石勒称赵王
  - Z20 灭段匹磾（KIND = duanpidi）
  - Z30 石勒称帝
  - Z40 石虎专权
  - Z45 石虎徙氐羌
  - Z50 石虎废弘
  - Z60 立石宣
  - Z70 段辽之亡（KIND = duanliao）

H1（E1-H40）核对：刘和、呼延攸已在卒年表里，PRE 为 hd_j16_liu_cong_heir_result，节点不另杀。刘和的死因要改成处决，交汇总人。

战争节点：
- 宣战用 hd_j16_b1_war_effect：攻方本人宣战失败、且攻方是封臣时，改由其最高领主宣战，攻方加入攻方阵营。
- 开战成功后才设 _started/_result/_att/_def（以及 _key）、给事件兵。
- 结局用 3-A 的 hd_j16_304_war_result_effect 按关键县判定。

3-A 移交四项：
- e2 入口已加 restore_tributary。
- b12_done 无人读取，所以无需改。
- J1、J3b 分别迁京城到 c_uuii_p_867、c_uuii_p_4389。
- E2-J11 已设 jinjian_done。

impl_notes「3-B」移交三项：
- E2-J11 加了王导授尚书令（若空），用 hd_j16_b1_minister_effect。
- 本路所有改元（J10 建武、J30 建兴、Z30 建平、Z50 后赵建武）都用 hd_j16_b1_change_era_effect，不设全局锁。
  - 更正：304 开局惠帝建武已把全局锁设到 404 年，与 J10 无关。
  - 这把锁只管随机年号池，后赵 335 建武直接设人物变量，从来不受影响。
  - b1 效果的实际作用只是不把锁续到 417 年。
- 编号式变量名已全部改为语义名，对照见第七节。

3-D 卡读的名字：
- Z4：KIND = jicheng；
- Z10：fire 时设 hd_j16_shile_emperor_result；
- Z2：fire 时设 hd_j16_zhangbin_result。

# 四、自拟与偏差

**通则**
1. 问玩家的战争事件：
   - 选项 a 只设 _go，由下一跳的节点开战；选项 b 跳过节点。
   - 节点已了结后才回复的，不生效，日志 player_late_reply。
2. 02 写「无分支」的节点，AI 和玩家一律直接执行：J1、J5、J7、J9、J12、H2、H4、Z2、Z11、Z13、Z17。
   - 改储类节点：玩家君主不改储，只记日志。
   - 「只能认」的两处另发通报：0301（靳准夺位）、0357（石虎废弘）。
3. R-继统写成 hd_j16_b1_heir_effect，条件是君主在世有地、继承人在世且同一王朝。兄终弟及（祖逖传祖约）不在其列。
4. 夺位类节点（H3、Z12）用 hd_370_take_realm_effect，夺位者先独立，被夺位者由卒年表处死。不用 hd_nbc_seize_realm_effect：它会当场杀人，和卒年机制重复，还会直接杀死玩家。
5. 【本轮新增】称号类节点 J15、H10、Z30、Z50 改走 hd_nbc_found_realm_effect。
   - 副作用：不在天朝政体时会被换成 celestial_government。靳准、司马保都可能被换。
   - H10、J15 用 FIXED = no，Z30、Z50 用 FIXED = yes。
   - J10 晋王（第 1 期原有）仍是直接设称谓：司马睿可能是封臣，不应被换政体。

**B2**
6. 目标、结局、tooltip 的改法见第三节。决议 B 的 tooltip 和注释都已同步为新选法。

**J 线**
7. J1：
   - 迁京长安和改元建兴推迟到邺真正持有 h_china 之后才做，只做一次，313 年内有效。
   - 长安已失守时，邺（AI、无地）改投司马睿宫廷，本节点跳过。
8. J3a：只把改元换成 b1 效果。
9. J3b：
   - 兜底强转 h_china 只在两种情况下做：h_china 无人持有，或持有者是胡人。外姓汉人持有时不强转，只记日志 WAIT hchina_held_by_other。
   - 改元太兴没做：mod 里缺年号键。
10. J4：要求司马保独立，他是封臣时等到窗口关闭。
11. J5：
    - 不发事件；
    - 2000 事件兵：有地给他本人，无地给他的主君；
    - 宣称一个汉豫州里被胡人占着的县；
    - 祖约的 R-继统没做。
12. J6：
    - 清君侧指名刘隗，刘隗不在时取刁协；本轮改为解析取人。
    - 要求王敦是元帝的直属封臣。
    - 胜负判定：h_china 上的 hd_dc_ten_qjc_regent 指向王敦，或王敦是 hd_court 权臣。
    - 胜后刘隗（AI、无地）改投石勒宫廷。
    - 事件兵 1 万（自拟）。
13. J8：
    - 开战前，王敦先解辅政：清 hd_dc_ten_qjc_regent、hd_court 罢官并解除记录。这是因为权臣在任时 AI 天子是他的傀儡，不先解除就打不起来。
    - 然后王敦脱离明帝独立；已独立就不重复。
    - 明帝以 hd_nbc_war_cb 讨伐，目标王敦首府所在郡，明帝得 1 万兵。
    - 宣战失败不回滚，下一跳按 is_independent_ruler 重试。
    - 钱凤、沈充的凶手自拟为明帝。
14. J9：窗口提前到 325.8.18，以便在明帝卒前 60 天做 R-继统；庾亮授尚书令（若空）。
15. J10：
    - 不走 hd_yiguan.1103（那是衣冠南渡局势里随机生成「苏峻型流民帅」的事件），本节点直接举兵：苏峻先独立（设 hd_j16_sujun_rose），再攻建康所在郡。
    - 宣战失败时，凭 rose 变量和「独立、未与天子交战」的条件，下一跳重试（本轮修正）。
    - 要求苏峻有地。
    - 天子得 5000「陶侃之师」。
    - 祖约（AI、有地）先独立，再加入攻方。
16. J11、J13：
    - 「荆州镇」取江陵 c_uuii_p_1813 所在的郡。
    - 分三跳：陶侃→庾亮→庾翼→桓温；庾冰没有用上。
    - 玩家天子由事件 0205 决定（a 授 / b 自留）。
    - 镇郡在玩家手里或在天子一系以外：只给后任宣称。
17. J12：
    - 窗口延到 345.3.1，好等穆帝即位后给何充授尚书令。
    - 两次 R-继统先解析再判（本轮修正）。

**H 线**
18. H3：被夺位者按位置解析（并州之主，独立，匈奴刘氏），不按刘粲的 ID。
19. 靳准的摆位：E1-H60 fire 时把靳准送进刘聪宫廷，H3 判定条件前再兜底一次。
20. H4：刘曜宣称的头衔取 k_uuii_bingzhou。
21. H5：STYLE = huangdi，FIXED = yes；持有长安县才迁都。
22. H6：
    - 契约组用 tributary_settled（实测项）。
    - 张茂先结束原有朝贡，再向刘曜纳贡。
    - 凉州续签只对不在朝贡中的人补签，不会来回翻转。
23. H7：石勒 1.5 万、刘曜 1 万事件兵；胜后刘曜关进地牢。
24. H8：
    - 攻方是石虎，开不成时由其最高领主宣战。
    - 目标天水郡，关键县为天水郡治。
    - 攻方的最高领主是玩家时，发事件 0305。

**Z 线**
25. Z1：张背督入汉宫廷改为心跳观察块，312 年止。旧事件 0120/0122 不改。
26. Z2：全体臣属好感 +5，另加学识 +2，持续 30 年。
27. Z3：玩家选 b 时只给兵，节点跳过。
28. Z4：
    - 轻信：征召 −50%，30 天；
    - 目标王浚首府所在郡，关键县为王浚首府县；
    - 事件兵 8000（自拟）。
29. Z5：给玩家石勒加了事件 0353；胜后刘琨入段匹磾宫廷。
30. Z6：「冀州 ≥3 郡」近似为国内汉冀州县 ≥12；不改元。
31. Z7：石虎在石勒国内时，8000 兵给石虎，否则给石勒。
32. Z11：石生得 5000 兵和对石虎首府所在郡的宣称，不另开场次。AI 石弘任石虎为 chancellor。
33. Z12：
    - 上游为二选一：Z11 已发生，或虎的 sub_realm_size ≥ 弘的一半。「持地」用 sub_realm_size 近似（本轮补）。
    - 持有邺才迁都邺。
34. Z13：要求石邃在世。
35. Z14：
    - 赵优先做攻方。
    - 赵为攻方时，石虎 2 万兵；慕容皝（AI、独立、接壤、未参战）加入攻方并得 8000。
    - 燕为攻方时，慕容皝 8000。
36. Z17：AI 独立的苻洪、姚弋仲改投石虎，无地者入石虎宫廷；枋头、滠头的授县没做。

**其他**
37. 索綝的 DATE10 收在 326.12.15，因为 E1 粗筛到 327.1.1 为止。
38. S4 永嘉的「汉方兵力加成（读 b12）」没有做。

# 五、本期面板行清单（交 F-1，只列不写）

共 32 行。适用开局都是 le304；都在 fire 时设，自保护、跳过时都不设。

| 面板变量 | 节点 |
|---|---|
| hd_hev_j16_mindi | E1-J30 愍帝长安即位 |
| hd_hev_j16_zuti | E1-J35 祖逖北伐 |
| hd_hev_j16_changan316 | E1-J40 刘曜破长安、西晋亡（开战时设） |
| hd_hev_j16_liuyi_fei | E1-H60 刘乂之废 |
| hd_hev_j16_zhangbin | E1-Z10 张宾归石勒 |
| hd_hev_j16_gebei | E1-Z20 葛陂退兵、北据襄国 |
| hd_hev_j16_jicheng | E1-Z30 袭蓟擒王浚 |
| hd_hev_j16_bingzhou316 | E1-Z40 取并州、刘琨奔段 |
| hd_hev_j16_jinjian | E2-J11 东晋建立 |
| hd_hev_j16_baowang | E2-J15 司马保称晋王 |
| hd_hev_j16_wangdun1 | E2-J20 王敦之乱（一） |
| hd_hev_j16_mingdi | E2-J25 元帝崩、明帝立 |
| hd_hev_j16_wangdun2 | E2-J30 王敦之乱（二） |
| hd_hev_j16_yuliang | E2-J35 庾氏秉政 |
| hd_hev_j16_sujun | E2-J40 苏峻、祖约之乱 |
| hd_hev_j16_jingzhen | E2-J50 荆州镇守更替（第一跳 fire 后设） |
| hd_hev_j16_chengkang | E2-J60 成帝、康帝继统 |
| hd_hev_j16_huanwen_jing | E2-J70 桓温出镇荆州 |
| hd_hev_j16_jinzhun | E2-H10 靳准之乱 |
| hd_hev_j16_liuyao_ji | E2-H20 刘曜即位 |
| hd_hev_j16_qianzhao | E2-H30 迁长安、改国号赵 |
| hd_hev_j16_xizheng | E2-H40 刘曜西征 |
| hd_hev_j16_luoyang328 | E2-H50 洛阳之战 |
| hd_hev_j16_shanggui329 | E2-H60 前赵亡 |
| hd_hev_j16_shile_wang | E2-Z10 石勒称赵王 |
| hd_hev_j16_duanpidi | E2-Z20 灭段匹磾 |
| hd_hev_j16_shile_emperor | E2-Z30 石勒称帝 |
| hd_hev_j16_shihu_zhuan | E2-Z40 石虎专权 |
| hd_hev_j16_xidiqiang | E2-Z45 石虎徙氐羌 |
| hd_hev_j16_shihu_fei | E2-Z50 石虎废弘 |
| hd_hev_j16_shisui | E2-Z60 石邃之死、立石宣 |
| hd_hev_j16_duanliao | E2-Z70 段辽之亡 |

另外两行之前已存在，本轮没有变化：hd_hev_j16_jinwang（E2-J10）、hd_hev_j16_yingjia（E1-B10）。

# 六、需要汇总人处理的事项

1. **落盘顺序**：p3-B1 必须和 p3-B2 同批 apply。
2. **卒年表 tsv（建议，不阻断）**
   - 刘和 xiongnu_liu_021 的死因改为 death_execution。
   - 建议补的 PRE：

     | 人物 | 建议 PRE |
     |---|---|
     | 王浚 taiyuan_wang_005 | hd_j16_jicheng_won |
     | 刘粲 xiongnu_liu_027 | hd_j16_jinzhun_result |
     | 愍帝 si_ma_ye | hd_j16_changan316_won |
     | 刘乂 xiongnu_liu_026 | hd_j16_liuyi_fei_result |
     | 刘曜 xiongnu_liu_041 | hd_j16_luoyang328_won |
     | 刘熙 liu_xi_2、刘胤 xiongnu_liu_043 | hd_j16_shanggui329_won |
     | 段匹磾 liaoxi_duan_006、段文鸯 liaoxi_duan_007 | hd_j16_duanpidi_won |
     | 段辽 liaoxi_duan_011 | hd_j16_duanliao_won |
     | 石弘、石宏、石恢（shangdang_shi_005/006/007） | hd_j16_shihu_fei_result |
     | 石邃 shangdang_shi_011 | hd_j16_shisui_result |
     | 程遐、徐光、石堪、石生 | hd_j16_shihu_zhuan_result |
     | 周顗 runan_zhou_003 | hd_j16_wangdun1_won |
     | 王含 langya_wang_030 | hd_j16_wangdun2_won |

   - 表外四人请补进表，并带同样的 PRE。他们现在由本路的处决块执行；补进表后两边共用同一个 done 变量，不会死两次。

     | 人物 | DATE / DATE10 | 凶手 | PRE |
     |---|---|---|---|
     | 索綝 oe_dunhuang_suo_007 | 317.1.15 / 326.12.15 | 刘聪 | hd_j16_changan316_won |
     | 戴渊 hd_j16_dai_yuan | 322.5.15 / 332.5.15 | 王敦 | hd_j16_wangdun1_won |
     | 钱凤 hd_j16_qian_feng | 324.10.15 / 334.10.15 | 明帝 | hd_j16_wangdun2_won |
     | 沈充 1802193 | 324.10.15 / 334.10.15 | 明帝 | hd_j16_wangdun2_won |

   - 改完 tsv 后由汇总人重跑 gen_deaths_effects.py。
3. **年号键缺失**：「太兴」（J3b）、「晏平」（B2 的 C1）在 WJ_tianjia_era_names.txt 和 WJ_names 本地化里都没有。要补的话，请指定这两个文件的写入者。
4. **头衔历史**：本路不需要改 history/titles。
5. **实测项**
   - 迎驾之战胜利后领地确实不转移；结局能正确读到 hd_nbc_yingjia_*。
   - 直接 start_war 能否绕过 CB 的 valid_to_start。
   - 清君侧 CB 由脚本开战能否成功、胜负能否判出。
   - 王敦解辅政、独立后，明帝能否宣战。
   - 苏峻宣战失败后，下一跳能否重试成功。
   - hd_370_take_realm_effect 用在「封臣先独立、再夺主君」时是否正常。
   - 刘曜西征用 tributary_settled 时，契约能否成立。
   - 轻信的 levy_size −0.5 是否生效。
   - got_minister_position_effect 授尚书令能否授上。
   - set_designated_heir 对被囚天子是否有效。
   - 卒年表里刘粲 318.9.15 与靳准之乱的先后顺序。
   - 【新增】found_realm 换政体对靳准、司马保的影响。
   - 【新增】Z50 的 sub_realm_size 比较是否正常。
6. **已知局限**
   - 庾翼、桓温若是游民，不在天子一方，荆州第二跳、第三跳只会等到窗口关闭。
   - 苏峻无地时开不了战。
   - 新场次（changan316、jicheng 等）的目标经过 wct，回退时关键县可能不在战争目标里，导致恒判失败。
   - 【新增】王敦（二）、苏峻一直开不成战的话，窗口关闭后都会留下一个没有战争的独立势力；王敦另外已被解除辅政。

# 七、新增事件号与变量

**事件**
- J 段：hd_j16.0201（刘曜）、0202（王敦起兵）、0203（明帝讨王敦）、0204（苏峻）、0205（荆州镇守）。
- H 段：0301（靳准夺位通报）、0302（改国号赵）、0303（张茂称藩）、0304（洛阳之战）、0305（前赵亡）。
- Z 段：0351（葛陂）、0352（袭蓟）、0353（取并州）、0354（称赵王）、0355（灭段匹磾）、0356（称帝或称天王）、0357（废弘通报）、0358（段辽）。
- 本节号段（0200–0449）里其余号码都未占用。

**节点变量**：一律写成 hd_j16_<语义>_done/_result/_skip/_wlog。语义名如下：
- mindi、zuti、changan316、liuyi_fei、zhangbin、gebei、jicheng、bingzhou316；
- jinjian、baowang、wangdun1、mingdi、wangdun2、yuliang、sujun、jingzhen1、jingzhen2、huanwen_jing、chengkang；
- jinzhun、liuyao_ji、qianzhao、xizheng、luoyang328、shanggui329；
- shile_wang、duanpidi、shile_emperor、shihu_zhuan、xidiqiang、shihu_fei、shisui、duanliao。

战争节点另有 _started/_won/_lost/_att/_def/_go/_asked/_wsf_wlog；jicheng、bingzhou316、wangdun2、duanpidi、duanliao 还有 _key。

**其他变量**
- 全局：hd_j16_mindi_era、hd_j16_yuliang_heir、hd_j16_chengkang_heir1/_heir2、hd_j16_jingzhen_next、hd_j16_jingzhen_key、hd_j16_beidu_done、【本轮新增】hd_j16_sujun_rose、hd_nbc_yingjia_active/_won/_lost/_white/_invalid。
- 本轮新增 scope 名：hd_j16_ck_yan、hd_j16_ck_yue、hd_j16_wd_liu、hd_j16_wd_diao、hd_j16_sg_yao、hd_j16_bd_le。
- 修正：hd_j16_junziying_modifier、hd_j16_qingxin_modifier、hd_j16_zhuanquan_modifier。
- 新工具效果：hd_j16_b1_change_era_effect、hd_j16_b1_heir_effect、hd_j16_b1_minister_effect、hd_j16_b1_war_effect、hd_j16_yingjia_start_war_effect、hd_j16_yingjia_result_effect、hd_j16_mandate_lock_check_effect、hd_j16_beidu_watch_effect / hd_j16_beidu_join_effect、hd_j16_jingzhen_hop_effect、hd_j16_e2_304_kills_effect。
- 新触发器：hd_j16_yingjia_valid_duchy_trigger。

**02 编号式旧名 → 语义名**

| 02 旧名 | 语义名 | 实施方 |
|---|---|---|
| hd_j16_b01_done | hd_j16_xiqian_done | 3-A |
| hd_j16_b02_done | hd_j16_yingjia_done | 3-A |
| hd_j16_b06_done | hd_j16_huanluo_done | 3-A |
| hd_j16_b12_done | hd_j16_ningping_done | 3-A |
| J3b | hd_j16_jinjian_done | 本路 |
| hd_j16_j13_done | hd_j16_huanwen_jing_done | 本路 |
| hd_j16_z04_done | hd_j16_jicheng_done / _won | 本路 |
| hd_j16_c01_done | hd_j16_lixiong_emperor_result | 3-B2 |
| B0 | hd_j16_daling_done | 第 1 期 |

已 grep 全 mod：编号式名字只在 e1 的一行注释里出现过。

# 八、卒年表 PRE 变量的设置处

gen_deaths.py 读的是 mod，不读暂存区，所以我直接 grep 了暂存副本加 mod 来核对。

- tsv 第 8 列里卒年早于 347 的 PRE 共 6 个。属于本路的只有 hd_j16_liu_cong_heir_result（刘和、呼延攸），设置处在 E1-H40：fire 和 already_ruler 两处都设，另有旧档补设在 core 文件里。
- 其余 5 个都是 3-A 的：
  - yingsi_result、yong_kill_result、zhangfang_result、ningping_result 能 grep 到字面设置；
  - poye_won 由结局宏的 $KIND$ 设置，grep 查不到字面，但有设置。
- 本路没有让「无人设置」的 W 增加。
- 本路新设的 result、won 变量都只在 fire 或结局时设。如果按第六节第 2 条补 PRE，这些变量名可以直接使用。