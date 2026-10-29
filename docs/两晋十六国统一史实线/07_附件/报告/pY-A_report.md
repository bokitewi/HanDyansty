# pY-A 最终报告（修正后合并版）

# pY-A 报告：志向卡额外目标改回逐年判定（遵 D56）

## 一、暂存任务与文件
暂存任务名为 pY-A。5 个文件全部以 edit 方式登记，动笔前一刻才 stage。暂存目录是 D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\pY-A\files\ 。

| 文件 | 改动 |
|---|---|
| common/scripted_effects/zz_hd_asp_effects.txt | 3184 行 → 3088 行，删 12 块，每块 8 行 |
| common/scripted_triggers/zz_hd_asp_triggers.txt | 2687 行 → 2735 行，补 12 段，每段 4 行 |
| common/customizable_localization/zz_hd_asp_custom_loc.txt | 6880 行，行数不变 |
| localization/simp_chinese/zz_hd_asp3_l_simp_chinese.yml | 723 行，行数不变 |
| localization/english/zz_tr_hd_asp3_l_english.yml | 723 行，行数不变 |

- 5 个文件都保持 UTF-8 BOM，换行符和文件末尾字节与原文件相同。
- 修改脚本放在 D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\pYA\ ：
  - revert.py：效果、分派、custom_loc，以及 yml 的 pre、done、todo 三行；
  - desc.py：卡面 desc 行；
  - desc.log：desc 行逐行的新旧对照。
- 每处替换前都断言旧文本恰好出现 1 次。yml 只做整行或行内替换，所以行号不变。
- 主 asp yml（zz_hd_asp_l_*）里只剩 cc_zhengxi 一项带达成时措辞，不在本次范围内，未动。

## 二、逐项做法与证据
**1. 效果文件**
- 删去 hd_asp_complete_effect 开头这 12 项的达成时 if 块，每块包括注释行在内共 8 行。
- 脚本断言删完后函数开头只剩 3 块：cc_zhengxi b1、smteng_qihuo b1、smyong_xidu b3。

**2. 分派链**
- 12 个 b 触发器都已 grep 核实，全部定义在 zz_hd_asp3_triggers.txt 中。
- 补回的分派段按主链里的卡序插回原位，都在 `trigger_else = { always = no }` 之前。
- 脚本断言 bonus1、bonus2、bonus3 每条链里每个 flag 只出现一次，三条链分别有 105、45、28 个 flag。
- 与两份备份对照，原来就在链里的 3 项位置一致：
  - smteng_beimen b2、xan_feishui b2 对照 p3d_fix 备份；
  - smyue_yingjia b1 对照 pF-0 备份。
- 另外 9 项从未进过分派链，没有原位可比，按主链卡序插入。
- bonus1、bonus2、bonus3 链头的注释「达成时才判定的项不在此列」仍然准确，未改。

**3. 本地化**
- custom_loc 中 12 处 `_N_final` 改为 `_N_todo`。
- 中英 yml 每项 3 行：
  - final 行改名为 todo，格式恢复为 `"\n· 文本"`；
  - pre 行去掉「达成之时，」；
  - done 行同样去掉「达成之时，」；
  - 英文同步去掉 "(Checked when the main goal is met) When the goal is reached, "，首字母改大写。
- 中英行号逐项一致，脚本已断言。
- **与任务原文的差异一：「仍」和 still 也去掉了。** 这两个字词是和「达成之时」一起加进去的。
  - smyue_yingjia、smteng_beimen、xan_feishui b2 三项照备份原文恢复，备份为 pF-0 备份和 p3d_fix 备份。
  - 其余 9 项在 data_p3d.py 里从一开始就是达成时措辞，没有原文可恢复，按设计文档 02 的表述（如「张方在世」「李越无地或已死」）去掉了配对的「仍」和 still。
- **与任务原文的差异二：卡面 desc 也改了。** 任务第 3 步只写了 pre、done、final，但 11 张卡的 _desc 行里也有「· 达成之时，…」。
  - 中英各 11 处已在原行内替换，行号不变。
  - smyue_yingjia 的 desc 本来就是逐年措辞，未动。
  - smyong_xidu 的 desc（第 53 行）中，b2 已改为逐年措辞，b3 保留达成时措辞，这是有意的。

**4. 全 mod grep**
- 在 *.txt、*.yml、*.gui 中搜这 12 项的 `_final`，只出现在上面 3 个暂存文件的原件里；暂存版中为 0 处。
- 12 个 `_todo` 在暂存版中各出现 3 次（custom_loc 1 次、中 yml 1 行、英 yml 1 行），没有悬空键。
- 暂存版里剩下的 `_final` 只有 cc_zhengxi_1、smteng_qihuo_1、smyong_xidu_3。

**5. 逐项改动位置**
- 「效果」列是原文件行号，其余列是暂存版行号。
- yml 三列是 pre、done、todo 三行的行号，中英相同。

| 项 | 效果(原) | 分派(新) | custom_loc | yml 三行 | desc |
|---|---|---|---|---|---|
| smyong_xidu b2（张方） | 943–950 | bonus2 第 2477 行附近 | 5991 | 64–66 | 53 |
| smying_taidi b2（卢志） | 959–966 | bonus2 第 2485 行附近 | 6027 | 116–118 | 105 |
| smying_yexia b1（公师藩） | 967–974 | bonus1 第 2256 行附近 | 5010 | 130–132 | 123 |
| smyue_sheji b1（司马毗） | 975–982 | bonus1 第 2272 行附近 | 5082 | 196–198 | 189 |
| lxiong_chuanzi b1（李越） | 983–990 | bonus1 第 2292 行附近 | 5172 | 288–290 | 281 |
| mrc_yanyuan b1（农宝德） | 991–998 | bonus1 第 2320 行附近 | 5298 | 412–414 | 404 |
| xan_feishui b3（新亭/桓冲） | 999–1006 | bonus3 第 2658 行附近 | 6810 | 479–481 | 465 |
| syj_jianguo b3（慕容配偶） | 1007–1014 | bonus3 第 2662 行附近 | 6828 | 534–536 | 520 |
| syj_nankui b2（慕容配偶） | 1015–1022 | bonus2 第 2545 行附近 | 6297 | 568–570 | 558 |
| smteng_beimen b2（并州≥4郡） | 1023–1030 | bonus2 第 2473 行附近 | 5973 | 32–34 | 22 |
| xan_feishui b2（尚书令） | 1031–1038 | bonus2 第 2525 行附近 | 6207 | 476–478 | 465 |
| smyue_yingjia b1（苟晞） | 1039–1046 | bonus1 第 2264 行附近 | 5046 | 162–164 | 154（未改） |

各分派段在链中的插入位置：
- **bonus1**：
  - yexia 在 taidi 与 hebei 之间；
  - yingjia 在 hebei 与 qingjun 之间；
  - sheji 在 qingjun 与 wjun_youzhou 之间；
  - chuanzi 在 bashu 与 zgui_baoxi 之间；
  - yanyuan 在 lxuan_xinghan 与 mrc_baoqin 之间。
- **bonus2**：
  - beimen、xidu 依次接在 qihuo 之后，在 guanzhong 之前；
  - taidi 在 guanzhong 与 yexia 之间；
  - feishui 在 mrc_fengying 与 xan_huandu 之间；
  - nankui 在 kangqin 与 hw_yihuo 之间。
- **bonus3**：feishui、jianguo 依次插在 mrc_fengying 与 hw_yihuo 之间。

## 三、若要恢复某项为达成时判定（供 07 §4 引用）
共四处：
1. 照 smteng_qihuo 块的写法，在 hd_asp_complete_effect 开头加一个 if 块。条件写 `var:hd_asp_aspiration ?= flag:<卡>` 和 `hd_asp_<卡>_b<N>_trigger = yes`，块内 `set_variable = hd_asp_b<N>`。
2. 从 hd_asp_bonus<N>_trigger 链里删掉该卡那 4 行分派段。
3. custom_loc 和中英 yml 中的 `_N_todo` 改为 `_N_final`。
4. 文本加回前缀：
   - todo 行改为「【主要目标达成时判定】达成之时，…仍…」；
   - pre、done 行和卡面 desc 行加「达成之时，」，并补回「仍」；
   - 英文对应改为 "(Checked when the main goal is met) When the goal is reached, …still…"。

## 四、需要汇总人处理
1. **D56 的实际后果。** 发卡时已经成立的项会被 hd_asp_mark_pre_bonus_effect 标为 p，即开局已有、永不发赏。这些项的额外目标实际作废，符合 D56，请知悉。
   - 已有报告明说开局即成立的：smteng_beimen b2、xan_feishui b2（见 p3-D 审查）、smyue_yingjia b1（见 pF-0）。
   - 按设计文档推测也很可能开局即成立的：
     - smyong_xidu b2：张方开局在颙宫廷；
     - smying_taidi b2：卢志的 liege 是颖，见 02 第 320 行；
     - smyue_sheji b1：司马毗开局在世。
2. **以下文档已过时，pY-A 不能改 docs，请在 07 §4 更新：**
   - p3-D 报告第四节第 1 条（D56 待拍板的 13 项）；
   - pF-0 报告第三节第 3 条；
   - pF-0 报告第五节第 9 条。
3. **生成器文案未同步。** scratchpad\p3d\data_p3d.py 里仍是达成时文案。该生成器本来就禁止重跑，这里只补记一句。
4. **以下三项保持达成时判定，未动：** cc_zhengxi b1、smteng_qihuo b1、smyong_xidu b3。

## 五、闸门结果
- 运行 gate.py，参数为 --overlay pY-A --compare baseline.json --only-changed。
- 结果：error 0、warn 0，相对基线无新增，overlay_files=5。
- 报告文件：D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\pY-A_gate.txt
- 未跑生成器，未开游戏，未提交 git，未直接写 mod。