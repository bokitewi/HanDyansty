# p2-A「合并重复人物」报告

暂存任务名为 p2-A，共 19 个文件：16 个改动、1 个新建、2 个工具。没有直接写 mod，没有跑任何生成器，没有开游戏，没有提交。闸门结果为 error 0、warn 0，比基线少 8 条。

## 一、做了什么

**合并数量**
- 共 88 对，实删 87 个人物块；`1415923` 库里已经没有，只登记防复发。
- 每一对都按合并处理：引用改指保留 ID，保留方缺的信息补上，再删重复块。

**合并范围**
- 05 §2.1 表 30 行：其中 #19 只并了 `1409696`，`1403020` 不并，原因见第三节。
- 06 §5.4 的 7 组：
  - 拓跋遵、刘库仁、赫连璝；
  - 柔然三组并入柔然整理；
  - 李歆与 #29 重复，按一组处理。
- A6-F8 柔然：保留 s1，删除 OE 中有对应者的全部 `yujiulu_*`（R 组 23 对、R2 组 6 对）。OE 独有的 6 人改挂 s1 父亲，王朝改为 `Rouran_yujiulv_dynasty`。
- A5-G1：吐谷浑、高句丽保留 OE 链，删 mod 自建的 7 人。304、346、370、404 和 370_undo 里的 k/d/c 头衔持有人全部改指。逐一 grep 过，没有同一人同时挂两条 liege 链的冲突。
- A3 §4.4 第 1～3 步（刘玄链）：
  - 另删 `1800071`，并入 `zhuojun_liu_009`；
  - `1800077` 的 father 改为 `zhuojun_liu_010`；
  - 出生年按 F6★B 顺延。
- 级联合并（表外，自拟）：OE 子女改挂以后，在同一父亲下变成同名同生卒的同胞，所以一并合并。共 C 组 5 对、R2 组 6 对。

**改指方式**
- 全 mod 扫描 history、common、events、localization、gui。生成物不改。
- 只替换 `#` 之前的代码部分。

**非人物文件**
- `zz_hd_263_startup_effects.txt`：删掉 `hd263_dup_effect = { DROP = wang_han ... }` 一行，副本已不存在。
- `zz_hd_nbc_startup_effects.txt:166`：`WHO = hd_nbc_meng_chang` 改为 `pingchang_meng_chang`。
- `01_shiliuguozhu.txt:4113`：`killer = 1415154` 改为 `xiongnu_liu_056`。

**防复发**
- 新建 `docs/人物审查/合并记录_2026-10-27.csv`：88 行，表头与 10-25 版一致，UTF-8 带 BOM、CRLF。
- `import_oe.py` 加读这个 csv，只取删除方是 OE 文件的行，`1415923` 也在内。
- `apply_del18.py` 加读这个 csv。
- 两个 py 都用 ast 自检通过。

**清理**
- 删掉了被删块前面的说明注释：UUII 的「##### 【名】」6 行，nbc/304/370 文件的单行注释 9 行。

**编码**
- 全部按 latin-1 字节读写，原 BOM 和换行保持不变（OE 文件是 CRLF，其余是 LF）。

**自检（暂存叠加到 mod 上重建索引，共 49,335 人）**
- 被删 ID 已不再有定义；全库没有重复 ID。
- 没有 father/mother 指向被删 ID。
- 涉及的 261 人逐一核对了亲子年龄（≥13）、性别和卒年顺序，没有新增问题。剩下 4 条是原有的，与本次无关：
  - `1415218`/`1415219` 的母亲 `1415170` 先卒；
  - `qi_zhou_ci_shi` 与 `qi_ba`；
  - `yujiulv_furen_1` 与 `qi_li_fu`。

## 二、附表

字段说明：
- 「改指」只数被删块以外的引用。被删者自己的子女如果也一并被删，引用会随块消失，记为 0。
- 17 号那一条是删行，不是改指。

| 组 | 保留 ID | 删除 ID | 删块所在文件 | 改指（按文件） | 补入信息 |
|---|---|---|---|---|---|
| 1 | zhuojun_liu_010 | 1800072 | oe | oe×1（1800077.father） | 见第三节刘玄链 |
| 1 | zhuojun_liu_009 | 1800071 | oe | 0 | — |
| 2 | xiongnu_liu_027 | liu_can | uuii | 0 | — |
| 3 | xiongnu_liu_026 | 1415068 | oe | 0 | — |
| 4 | langya_sun_004 | taoist_sun_en | oe | 0 | 补特质 education_learning_4、lifestyle_mystic、zealous、ambitious；信仰保留 zhengyi |
| 5 | changli_murong_004 | 1415908 | oe | 0 | — |
| 6 | changli_murong_008 | 1415913 | oe | oe×1（killer） | 生年 331→298 |
| 7 | changli_murong_018 | 1415923 | 库中已无 | 0 | 只登记 csv |
| 8 | yuwen_mogui | hd_304_yuwen_mogui | 304 人物 | 304 头衔×5 | — |
| 9 | yuwen_qidegui | henan_yuwen_012 | oe | 0 | — |
| 10 | tuoba_026 / tuoba_032 / tuoba_029 / tuoba_028 | 1415114 / 1415119 / 1415120 / 1415121 | oe | 0 | 贺傉生年 308→292，纥那生年 310→294 |
| 11 | tuoba_yigui / tuoba_038 | 1415127 / 1415133 | oe | 0 | — |
| 12 | tuoba_013 | 1415010 | oe | 0 | 卒日块补绰号 shihao_mingyuan |
| 13 | tuoba_qinghe | 1415204 | oe | 0 | — |
| 14 | yigui_tuoba_002 | 1415136 | oe | 0 | — |
| 15 | changli_murong_017 / changli_murong_016 | 1415935 / 1415910 | oe | 0 | 配偶已在 tuoba_005，不用补 |
| 16 | xiangxian_liu_007 | oe_xiangxian_liu_021 | oe | 0 | 配偶已在谢安，不用补 |
| 17 | langya_wang_030 | wang_han | uuii | 263 开局效果 删 1 行 | — |
| 18 | shangdang_shi_026 | shi_sheng | uuii | 0 | — |
| 19 | zhongzu_cui_016 | 1409696 | oe | 0 | 1403020 不并（偏差） |
| 20 | 247346 | hd_304_chief_tuyuhun | 304 人物 | 304 头衔×5 | — |
| 20 | 247348 | hd_nbc_tyh_ye_yan | nbc 人物 | 346 头衔×6；370_undo×6 | — |
| 20 | 247349 | hd_370_sui_xi | 370 人物 | 370 头衔×6 | — |
| 20 | 247352 | hd_nbc_tyh_wu_he_ti | nbc 人物 | 404 头衔×6 | — |
| 21 | korean_go_goguryeo_18 | hd_304_gao_yifu | 304 人物 | 304 头衔×13 | name = "Eul_bul"（乙弗，原版键） |
| 21 | korean_go_goguryeo_16 | hd_nbc_gjl_gao_zhao | nbc 人物 | 346 头衔×13；370 头衔×13；370_undo×13 | name = "Sa_yu"（斯由） |
| 21 | korean_go_goguryeo_13 | hd_nbc_gjl_gao_tan_de | nbc 人物 | oe×1（_12.father）；404 头衔×13 | name = "Dam_deok"（谈德）；补 diligent |
| 22 | tufa_008 | 1415818 | oe | oe×2（吐若留、素渥改挂） | — |
| 22 | tufa_009 | 1415819 | oe | oe×1（奚于） | — |
| 22 | tufa_010 | 1415820 | oe | oe×3（羌奴、赴单、樊尼） | — |
| 22 | tufa_011 / 012 / 013 / 015 / 016 | 1415821 / 1415822 / 1415824 / 1415825 / 1415826 | oe | 0 | — |
| 23 | lueyang_fu_001 | linwei_fu_0001 | oe | 0 | — |
| 24 | lueyang_fu_034 | linwei_fu_0024 | oe | 0 | — |
| 25 | longxi_li_003 | longxi_li_0030 | oe | 0 | — |
| 26 | si_ma_song_2 | henei_sima_203 | oe | 0 | — |
| 26 | si_ma_song | henei_sima_079 | oe | 0 | 卒日 329.7.1→329.3.29 |
| 26 | si_ma_wen_si | henei_sima_285 | oe | oe×1（妙玉改挂） | — |
| 26 | si_ma_wen_bao | henei_sima_288 | oe | 0 | 卒日 415.1.1→415.1.27 |
| 27 | pingchang_meng_chang | hd_nbc_meng_chang | nbc 人物 | nbc 开局效果×1（WHO） | 卒年 409.1.1→410.6.1 |
| 28 | bacong_li_026 | li_shi_3 | uuii | 0 | — |
| 29 | longxi_li_007 | li_xin_3 | uuii | 0 | — |
| 30 | langya_wang_063 | wang_xi_zhi | uuii | 0 | — |
| B1 | tuoba_changshan | 1415210 | oe | 0 | father 改为 tuoba_035（寿鸠，依据 OE 和《魏书》卷15）；卒日 407.1.1→407.6.21 |
| B2 | henan_dugu_001 | 1415176 | oe | 0 | — |
| B3 | xiongnu_liu_056 | 1415154 | oe | 01_shiliuguozhu×1（killer） | — |
| R | mu_gu_lv、yujiulv_02、yujiulv_04、yujiulv_10001、wu_jie、lv_da_fei、lv_da_ni_bei_yi、yujiulv_20005、da_tan、yujiulv_30002、yujiulv_30004、wu_ti、qi_li_fu、tu_he_zhen、yujiulv_50001、yujiulv_50002、fu_tu、yujiulv_60002、yujiulv_70002、a_na_gui | yujiulu_01、_02、_04、_06、_0715、_0711、_0712、_073、_077、_081、_083、_084、_087、_09、_10、_101、_111、_112、_mb1、_mb2 | oe | 0 | — |
| R | yujiulv_10002 | yujiulu_061 | oe | oe×2（技圭支、吐奴傀改挂） | — |
| R | pu_hun | yujiulu_062 | oe | oe×3（乌卢胡、冯、麟改挂） | 生年 347→332（取 OE），否则改挂来的子女不足 13 岁差 |
| R | yujiulv_20004 | yujiulu_072 | oe | oe×1（示巴改挂） | — |
| R2 | he_duo_han、qi_ba、pi_li、tu_lu_gui、qi_lie_gui、zuo_zhao_yi | yujiulu_07、_0714、_079、_085、_086、_088 | oe | 0 | 级联，表外 |
| C | tuoba_023 | 1415011 | oe | 0 | 卒日块补绰号 shihao_taiwu；级联，表外 |
| C | yigui_tuoba_003 | 1415137 | oe | oe×1（henan_yuan_926 改挂） | 级联，表外 |
| C | changshan_tuoba_001 / changshan_tuoba_002 | 1415211 / 1415212 | oe | 0 | 级联，表外 |
| C | si_ma_mi_tuo | henei_sima_286 | oe | 0 | 级联，表外 |

**按文件合计**
- 删块：OE 69 个，UUII 6 个，nbc 5 个，304 3 个，370 1 个；另有 1415923 不在库。
- 改指：
  - 304 头衔 23 处、346 头衔 19 处、370 头衔 19 处、370_undo 19 处、404 头衔 19 处；
  - OE 内部 17 处；
  - 01_shiliuguozhu 1 处、nbc 开局效果 1 处；
  - 263 开局效果删 1 行。

## 三、自拟与偏差

1. **偏差：#19 的 1403020「崔岳」不并。**
   - 名字键是「嶽」不是「悅」；
   - 父系是崔就→崔公安，和崔悦（崔林→崔基一系）完全不同；
   - 它自带崔牧→崔荫两代后人。
   - 判为不是同一人，只并了 1409696。请汇总人或 boki 确认。
2. **级联合并（表外）**：C 组 5 对，R2 组 6 对，依据同父、同名、生卒相同或相近。
3. **柔然 OE 独有 6 人**（071、074、0713、078、0710、082）：改挂 s1 父亲，王朝改为 s1 的郁久闾。
   - 下面三组没有合并，待核：
     - 078 乌卢胡与 ta_wu_wu_lu_hu「吾无鹿胡」：生卒相差 14 年；
     - 0710 冯与 lv_feng「凤」：字不同，生年差 32 年；
     - 082 示巴与 yujiulv_30003「某」：同父、同卒于 414。
4. **度拔性别**：OE 是女、s1 是男。史载度拔是社仑之子，保留 s1 的男性。
5. **刘玄链**
   - 生年：1800077→322、1800078→347、1800079→372（依 F6★B）。1800080 由 381 自拟改为 390，否则父亲顺延后只有 9 岁。
   - 家族：按 05「1800077→1800082」改为 zhuojun_liu，并延伸到 1800083（灵助），A3 §4.4 只写到 079。
   - A3 §4.4 第 4～6 步（三人取名、刘玄之妻、刘永家族）没有做，属于 2-B/2-C。
6. **拓跋遵**：父亲改为寿鸠 tuoba_035，卒日改为 OE 的 407.6.21。06 §5.2 写的是 407.6.15【待核】，请 2-D 统一。
7. **pu_hun 生年**改为 332（取 OE 仆浑）。
8. **高句丽三王**
   - 原版 history/characters 被 replace_path 覆盖，OE 块没有生时名，所以用原版名字键补上（原版 loc 里有：Eul_bul、Sa_yu、Dam_deok）。
   - _13 补 diligent。
   - 王朝仍是原版 korean_go_goguryeo，显示为「高」，不是「高句丽高氏」，没有改。
9. **崧、文宝**只采用 OE 的精确卒日。崧的父亲问题见第四节。
10. **越界修改**：`zz_hd_nbc_startup_effects.txt` 是 1-E 的共享文件，我只改了一行 WHO。
11. **补谥号绰号**写进原有的卒日块，放在 death 之前，不另开同日期的块。两个绰号键在 `zz_hd_oe_nicknames.txt` 里都有。

## 四、需汇总人处理

**1. 重新生成会冲掉这次的改动**
- D 盘 nbc 生成器（`py\spec.py`/`gen.py`，路径没查到）：产出 `zz_hd_nbc_characters.txt` 和 346、404 头衔。要删掉 5 人，并改持有人。
- gen370.py：产出 370 人物、头衔和 undo。要删碎奚，并改持有人。
- 304 生成器：产出 304 人物和头衔。要删 3 人，并改持有人。
- UUII 书库生成器：east_asian 文件里删了 6 人。
- OE 重导入：被删的人已由新 csv 屏蔽。但以下改动在重导入时会被还原，需要另加规则：
  - 1800077～83 的生年和家族；
  - 柔然 6 人的王朝；
  - 高句丽的名字和特质。

**2. 生成物里出现的被删 ID（没改，重跑后应清零）**
- `zz_hd_hbirth_generated_effects.txt`：被删 ID 中有 85 个出现在这里。按组列：
  - 表内 #1～30（除 1415923、1403020）：1800071、1800072、liu_can、1415068、taoist_sun_en、1415908、1415913、hd_304_yuwen_mogui、henan_yuwen_012、1415114、1415119、1415120、1415121、1415127、1415133、1415010、1415204、1415136、1415935、1415910、oe_xiangxian_liu_021、wang_han、shi_sheng、1409696、hd_304_gao_yifu、hd_370_sui_xi、hd_nbc_tyh_ye_yan、hd_nbc_tyh_wu_he_ti、hd_nbc_gjl_gao_zhao、hd_nbc_gjl_gao_tan_de、1415818、1415819、1415820、1415821、1415822、1415824、1415825、1415826、linwei_fu_0001、linwei_fu_0024、longxi_li_0030、henei_sima_203、henei_sima_079、henei_sima_285、henei_sima_288、hd_nbc_meng_chang、li_shi_3、li_xin_3、wang_xi_zhi；
  - 06 §5.4：1415210、1415176、1415154；
  - 级联：1415011、1415137、1415211、1415212、henei_sima_286；
  - 柔然 yujiulu_ 中有 29 个出现在这里（除 _082）：01、02、04、06、061、062、07、0711、0712、0714、0715、072、073、077、079、081、083、084、085、086、087、088、09、10、101、111、112、mb1、mb2。
- `zz_hd_hbirth_templates.txt`：1415908、longxi_li_0030。
- `zz_hd_popclean_protect_generated.txt`：hd_nbc_meng_chang。
- 第 2 期末重跑 hbirth、popclean 之前，这些引用会报错。

**3. 设计文档里点名的旧 ID，后续写代码时要改用新 ID**

| 文档位置 | 旧 ID | 改用 | 备注 |
|---|---|---|---|
| 06 §1.7 E5-X50 | 曷多汗 yujiulu_07 | he_duo_han | 此人 394 年卒，402 年已不在世。X50 当事人应去掉或换人，由 6-A 定 |
| 06 E5-M45 | 高谈德 hd_nbc_gjl_gao_tan_de | korean_go_goguryeo_13 | — |
| 06 §2 表 | hd_nbc_meng_chang | pingchang_meng_chang | — |
| 06 §5.2 卒年行 | 拓跋遵 | tuoba_changshan | 卒日现为 407.6.21，06 写的是 407.6.15【待核】 |
| 06 §5.2 卒年行 | 斛律 | yujiulv_20005 | 原写 yujiulu_073 已删 |
| 04 E4-T20 | 1415127 | tuoba_yigui | — |
| 04 E5-J22 孙恩 | taoist_sun_en | langya_sun_004 | — |
| 03 #11、04 附表 | 叶延 hd_nbc_tyh_ye_yan | 247348 | — |
| 03 #11、04 附表 | 碎奚 hd_370_sui_xi | 247349 | — |

其余命中都在合并表本身，不需要动。第 1 期的暂存里只有 `zz_hd_nbc_startup_effects` 引用过这些 ID（第 1 期已落盘，这次已改）。

**4. 交 2-B：往上一辈的疑似重复和数据问题（只往下级联，没有往上追）**
- 疑似重复：
  - 1415874（OE 慕容廆妻）与 liaoxi_duan_068；
  - 1415135、1409695、1415174/1415178（刘库仁的 OE 父母）、1415170、1415181。
- 高句丽：
  - _13 原本就同时有 education_martial_4 和 education_martial_prowess_4 两个教育特质；
  - _12、_14、_15 没有生时名，原版有键 Geo_ryeon、I_ryeon 等。
- 司马崧：s1 写父亲是司马羕，OE 和《晋书》都作「充子崧」。
- 247346 的文化（§3 #40）。
- 370_undo 在 370.2.14 把头衔还给已故的叶延：原有做法，这次只是机械改指。

**5. 落盘**
- 暂存时 ck3 没有运行。
- 所有 history/titles 文件都是在动笔前一刻才 stage，基准哈希已记入 manifest。

## 五、闸门

命令：`gate.py --overlay p2-A --compare baseline.json --only-changed`

- 两次都是 error 0、warn 0，比基线少 8 条，char_ids 为 49,335。
- 第二次是修正绰号写法之后重跑的。
- 输出：`D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p2-A_gate.txt`

**工作脚本**（在 `D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\p2a\` 下）：
- 合并对表：`final_pairs.txt`
- 执行器：`exec.py`，日志 `exec_log.json`
- 自检：`verify.py`
- 叠加索引：`idx_ov.tsv`

# REVIEW
{
 "issues": [
  {
   "severity": "major",
   "file": "history/characters/zz_hd_oe_characters.txt",
   "where": "1403020（name=\"Yue_5DBD\"，280–351，father=1403019）",
   "problem": "偏离已拍板的设计。02_304左国称王.md 第 321、425 行和 05 §2.1 #19 都写明崔悦 zhongzu_cui_016 要合并 1403020 和 1409696 两个 OE 副本，实施只并了 1409696。报告的理由之一是父系不同，但这条不成立：被合并的 1409696，父亲 1409695 也不是 zhongzu_cui_012，同样属于另一条父系。真正能区分两人的只有名字键：嶽（U+5DBD）和悅（U+60A6/6085）。而 1403020 的生卒 280–351 与崔悦的 286–349 很接近，它还带有崔牧（1403021）一支后人。",
   "fix": "落盘前由 boki 或汇总人拍板：①认定是同一人（嶽是悦的误写），就按设计合并，1403021 改挂 zhongzu_cui_016，并在 csv 补一行；②认定是另一人，就在 05 §2.1 #19 和 02 附表上注明「1403020 不并」以及理由，防止后续阶段再按旧表处理。"
  },
  {
   "severity": "minor",
   "file": "history/characters/01_shiliuguozhu.txt",
   "where": "changli_murong_004（慕容廆）333.6.12 卒日块",
   "problem": "被删副本 1415908 的卒日块里有 give_nickname = liaodongxianggong（辽东襄公），没有补到保留方，保留方现在没有任何绰号。这和 tuoba_013、tuoba_023 补了谥号绰号的做法不一致，也与报告所说「保留方缺的信息补上」不符。另外，1415908 的 add_spouse = 1415874 没有迁移。1415874 是 OE 的武宣段氏，报告列为 liaoxi_duan_068 的疑似重复，她现在既无丈夫也无子女，在 304 开局时是一个游离的未婚贵妇，可能被 AI 另行婚配。",
   "fix": "在 333.6.12 块的 death 之前加 give_nickname = liaodongxianggong（先确认 zz_hd_oe_nicknames.txt 里有这个键）。1415874 交 2-B 与 liaoxi_duan_068 合并；如果暂时不合并，就在报告里写明她已成为孤立副本。"
  },
  {
   "severity": "minor",
   "file": "history/characters/00_xuzhou.txt",
   "where": "langya_sun_004（孙恩）",
   "problem": "只补了 4 个特质。OE 块里的 learning = 20 和 disallow_random_traits = yes 没有带过来，报告也没说明是有意舍弃。另有一处原有问题（不是本次引入）：该块卒日写 killer = 辛昺，用的是汉字，不是人物 ID，违反报错清单「凶手引用必须存在」。",
   "fix": "补上 learning 和 disallow_random_traits，或者在报告里写明舍弃。killer = 辛昺 交给后续卒年阶段（2-D）改为真实 ID，或者删掉 killer。"
  },
  {
   "severity": "minor",
   "file": "history/characters/zz_hd_oe_characters.txt",
   "where": "henan_yuan_926 father=yigui_tuoba_003",
   "problem": "这是本次唯一新增的亲子年龄问题。从 1415137（380 年生）改挂到 yigui_tuoba_003（390 年生）以后，父子年龄差只剩 13 岁，基线时是 23 岁。报告说「涉及 261 人，年龄差都在 13 岁及以上，没有新增问题」，这次算是压线通过。",
   "fix": "核实 henan_yuan_926 的生年，或者核实 yigui_tuoba_003（六状）的生年（OE 作 380 年），必要时取 OE 的 380 年，这样年龄差能恢复到 23 岁。"
  },
  {
   "severity": "minor",
   "file": "（实施报告）",
   "where": "二、按文件合计：删块",
   "problem": "报告写「OE 69 个」。块级 diff 实测 zz_hd_oe_characters.txt 删了 72 块：72+6（UUII）+5（nbc）+3（304）+1（370）=87，与「实删 87」一致；按 69 合计只有 84。",
   "fix": "报告里 OE 删块数改为 72。"
  },
  {
   "severity": "minor",
   "file": "history/characters/zz_hd_integrated_s1_characters.txt",
   "where": "柔然 R/R2 生年差较大的配对：qi_li_fu↔yujiulu_087、wu_jie↔0715、qi_ba↔0714、zuo_zhao_yi↔088、pi_li↔079",
   "problem": "这几对生年差 15～43 年。R2 是表外级联，报告自己写的标准是「生卒相同或相近」，qi_ba、zuo_zhao_yi、pi_li 并不满足。不过名字核对下来是一致的：s1 名字键解析为「力弗」「颉」「拔」「昭仪」，与 OE 的「乞利夫」「吴颉」Qiba、Zuozhaoyi、Pili 吻合；s1 的名字缺首字，是原有的写法。双方父亲也已对应到同一人，所以判为同一人，不算误删。另外 qi_li_fu 生于 427 年，比父亲大檀晚 59 年；qi_ba 和 qi_li_fu 的子女都在父亲死后出生（qi_zhou_ci_shi、yujiulv_furen_1）。这两处都是 s1 原有的数据问题，本次保留 s1 生年后仍然存在。",
   "fix": "不用回退。交 2-B/2-D 复核 s1 柔然几人的生年（OE 的年份多半更合理），并在 05 柔然附表里补上 R2 的级联依据。"
  }
 ],
 "gate_summary": "没有阻断项。重点是 #19 的 1403020 没有按设计合并，需要 boki 或汇总人拍板；另有 5 条 minor（见 issues）。\n\n**闸门**\n- 按指定命令（叠加 p2-A、对照 baseline.json、只看改动文件）重跑：error 0，warn 0，比基线少 8 条，char_ids 49,335。\n- 去掉「只看改动文件」再跑全量：仍是 0 新增。\n- 输出：D:\\Temp\\claude\\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\\scratchpad\\stage\\p2-A_gate_review.txt，以及 D:\\Temp\\claude\\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\\scratchpad\\rv2a\\gate_full.txt。\n\n**独立脚本核对**（D:\\Temp\\claude\\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\\scratchpad\\rv2a\\ 下的 drift.py、chdiff.py、refs.py、tdiff.py、pairs.py、hdates.py、dang.py、lost.py）\n\n1. **基准与编码**\n   - 19 个文件的当前哈希都等于 manifest 里的基准，没有并发漂移。\n   - BOM 和换行都保持原样（OE 文件 CRLF，其余 LF）；新 csv 为 UTF-8 带 BOM、CRLF。\n2. **删块**\n   - 块级 diff：实删 87 块，其中 OE 72、UUII 6、nbc 5、304 3、370 1。\n   - 删除的块全部在合并表内，没有表外误删，也没有新增块；1415923 基线里本来就没有。\n   - 全库没有重复 ID；father/mother/spouse/killer 指向不存在人物的悬空引用，前后都是 194 条，没有新增。\n3. **其余改动**\n   - 26 个 OE 块只改了父亲、王朝或家族、生年、名字；s1 和 dishishixing 等文件只改了生卒、父亲、特质、绰号，逐项与报告一致。\n   - 绰号键 shihao_mingyuan、shihao_taiwu 在 OE 绰号文件里存在；Eul_bul、Sa_yu、Dam_deok 在原版本地化里存在。\n4. **残留引用**\n   - 扫描 common、events、history、localization、gui 等目录（只看 # 之前的代码部分），除生成物外，88 个删除 ID 已没有任何引用。\n   - 生成物里有 86 个删除 ID 残留，报告已登记。\n5. **头衔改指**\n   - 5 个头衔文件都是逐行替换，不含其他改动：304 共 23 处、346 共 19 处、370 共 19 处、370_undo 共 19 处、404 共 19 处。\n   - 开局持有日期都在保留者的生卒范围内。\n   - 370_undo 在 370.2.14 把头衔写回已故的 247348、bacong_li_026、tufa_008、zhuojun_liu_010，这是原有做法，本次没有引入新问题。\n   - 263 开局效果删 1 行、nbc 开局效果改 1 处 WHO，两处都正确。\n6. **同一人核对**\n   - 逐对对照了姓名、生卒、父亲、性别，都是同一人。#19 的 1403020 不并是有意偏差，另列在 issues 第 1 条。\n   - 柔然生年差较大的几对，名字解析后吻合。\n7. **防复发**\n   - csv 共 88 行，与 final_pairs 完全一致，表头与 10-25 版相同。\n   - import_oe.py 只读删除方是 OE 文件的行（73 行，含 1415923）；apply_del18.py 读全部行；两处写法与已有各条一致。\n\n**落盘的硬前提**：落盘后、开游戏之前，必须重跑 hbirth 和 popclean。原因不只是清掉报错：\n- zz_hd_hbirth_templates.txt 里还有 hd_hb_t_1415908、hd_hb_t_longxi_li_0030 两个模板。\n- hd_hb_spawn_effect 找不到原生人物时，会按模板现场生成一个新人，等于把慕容廆、李弇的副本又带回来。\n- 其余 80 多个删除 ID 没有模板，会在运行时报错。\n\n另外请汇总人注意：nbc、370、304、UUII 各自的生成器，以及 dedupe263.py，重跑时都会把这次的删改冲掉，需要另加规则（报告第四节已列）。"
}

# FIX
## p2-A 修正报告

本轮只改了暂存区的两个文件：01_shiliuguozhu.txt 和 00_xuzhou.txt。两处都按字节（latin-1）做精确替换，原编码、BOM 和 LF 换行都没变。改动前核对过：manifest 里 18 个基准文件的哈希仍与 mod 现状一致，没有并发漂移。

### 逐条处理

**#1（major）崔悦 1403020：不合并，作为有据偏差交汇总人登记**

审查认为这一条要由 boki 或汇总人拍板。我补查了 1403020 的上下游，结论是它和崔悦不是同一人，设计表这一行是启发式匹配误配出来的（同给名、同姓、生卒相近，拼音都是 Yue）。依据如下：

- **祖先链不交叉**
  - 1403020 的祖先链：崔济 1403014 → 崔湫 1403015 → 崔融 1403016 → 崔温 1403017 → 崔就 1403018 → 崔公安 1403019，都属 qinghe_cui_dyn。
  - 崔悦在 mod 里的祖先链：cui_lin → zhongzu_cui_011（崔参）→ zhongzu_cui_012（崔基）。
  - 两条链没有交点。
- **儿子不同**
  - mod 的《广韵》注记写崔悦有浑、潜、湛、液四子，已经挂在 zhongzu_cui_017～020。
  - 1403020 的儿子是崔牧 1403021。
- **名字不同**：嶽 Yue_5DBD，悦 Yue_60A6。
- **合并代价很大**
  - 1403021 以下约有 36 名后裔：崔蔭、崔怡、崔曠、崔靈茂、崔稚寶、崔逵……一直到 1403157。
  - 按名字推断，这一支应是崔光先世（崔光之祖名崔曠）。但 OE 注释里没有出处，这一点没有原文依据。
  - 合并等于把一整支崔氏嫁接到崔悦名下，错误比留一个疑似副本大得多。
- **审查的反驳不成立**：审查说被并的 1409696 父系也不同，但它的父亲 1409695 是「unnamed son of zhongzu_cui_011」，正好在崔基的位置，与「崔林曾孙」吻合。所以并 1409696 有父系依据，并 1403020 没有。

现状与这个结论一致，不用再动：
- csv、final_pairs、import_oe 都不含 1403020。
- hbirth 模板 hd_hb_t_1403020 应保留，因为这个人还在库里。

请汇总人：在 07 写明这条偏差；在 05 §2.1 #19 和 02 第 321、425 行注明「只并 1409696，1403020（崔嶽，另支）不并」，防止后续阶段按旧表再并。08 第 205 行禁止实施代理改 docs 01–08，所以我没有改这些文件。

**#2（minor）慕容廆：已补绰号，配偶未迁移**
- 已改：changli_murong_004 的 333.6.12 块改为 `{ give_nickname = liaodongxianggong death = yes }`。这个键在 common/nicknames/zz_hd_oe_nicknames.txt 第 50 行，中英文本地化都有。
- 不迁移 `add_spouse = 1415874`：保留方已经娶了 liaoxi_duan_068（武宣皇后段氏），再迁过来，慕容廆会有两个其实是同一人的段氏妻子。
- 1415874（武宣王后段夫人，283–350.10.1）现在是孤立副本，无夫无子，304 开局时可能被 AI 另行婚配。她不在 05 合并表里，本轮不扩表，交 2-B 与 liaoxi_duan_068 合并。

**#3（minor）孙恩：已补两个字段，并删掉非法凶手引用**
- langya_sun_004 在 `rite = zhengyi` 之后补了 `learning = 20` 和 `disallow_random_traits = yes`（取自 OE taoist_sun_en）。
- 卒日块删掉了 `killer = 辛昺`，现为 `death = { death_reason = death_execution }`，行尾 #辛昺 注释保留。
  - 一是凶手引用必须是存在的人物 ID，汉字不合法。
  - 二是孙恩赴海自沉，属于 05 文首表里「投水，killer 留空」一类。
- 死因键要换成投水类，留给 2-D 卒年表处理。

**#4（minor）henan_yuan_926 父子年龄差：不改**
- 不取 OE 的 380 年：yigui_tuoba_002（勿期）生于 370，六状改成 380 后，上一代父子差只剩 10 岁，比现在的 13 岁更糟。
- 沿 OE 链往上一起改也不行：OE 勿期 358 年对乌渥 355 年只差 3 岁；OE 无名子 342 年对寔君 338 年只差 4 岁。
- 现状：寔君 338 → 乌渥 355 → 勿期 370 → 六状 390 → 河内公主 403。父子差 13 岁是压线通过，闸门不报错。
- 没有史料依据，不改河内公主 403 年的生年。这条交 2-D 核史。

**#5（minor）报告计数，更正如下（#1 不合并，审查实测的数字成立）**
- 删块共 87：OE 72、UUII 6、nbc 5、304 3、370 1。原报告「OE 69」写错了。
- csv 共 88 行，比删块多的一行是 1415923，库里本来就没有，登记它是为了防止 OE 重导入时带回。
- import_oe.py 读到的 OE 一侧共 73 行。

**#6（minor）柔然 R2 生年差：不回退，不改 docs，交 2-B/2-D**

R2 的级联依据如下，请汇总人写进 07 或 05 柔然附表：
- s1 的名字键缺首字，这是 s1 原有写法。解析后为力弗、颉、拔、昭仪，与 OE 的乞利夫、吴颉、Qiba、Zuozhaoyi、Pili 吻合。
- 双方父亲已经对应到同一人，所以判为同一人。

s1 原有的数据问题仍然存在，交 2-B/2-D 复核，OE 的年份多半更合理：
- qi_li_fu 生于 427 年，比父亲大檀晚 59 年。
- qi_ba、qi_li_fu 的子女（qi_zhou_ci_shi、yujiulv_furen_1）都生在父亲死后。

### 未解决或移交
1. 1403020 不并：请汇总人写 07，并改 05 #19、02 第 321 和 425 行。
2. 1415874 孤立副本：交 2-B。
3. 孙恩死因键改为投水类：交 2-D。
4. 拓跋六状一支生年偏紧：交 2-D。
5. s1 柔然生年问题：交 2-B/2-D。
6. 落盘的硬前提不变：落盘后、开游戏之前，必须重跑 hbirth 和 popclean。原因是模板 hd_hb_t_1415908、hd_hb_t_longxi_li_0030 会把被删的副本带回来，其余被删 ID 的生成物残留会在运行时报错。
7. nbc、370、304、UUII 各自的生成器和 dedupe263.py 需要另加规则，见原报告第四节。

### 闸门（按指定命令复跑：叠加 p2-A、对照 baseline.json、只看改动文件）
- error 0，warn 0，char_ids 49,335。
- 比基线少 9 条，原来是 8 条，多出的一条应是删掉 `killer = 辛昺` 带来的。
- 输出：D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p2-A_gate.txt
- 修正脚本：D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\p2afix\fix.py

没有跑生成器，没有开游戏，没有提交。