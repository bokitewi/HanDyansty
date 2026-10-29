# p4-D 最终报告（修正后合并版）

# p4-D「346 风味修正」修正轮报告（第 4 期第一轮，4-D）

## 〇、审查意见处理结果
审查共 3 条，都是 minor，没有 blocker 或 major。

1. **[minor] 第四节第 4 条里 hd_nbc346_gov_longyou 的行号写错了**：已修，只改报告。
   - 现文件 1420 行是键，`culture = wa` 在 1422 行，`rite = fusang_pagan` 在 1423 行，所以改为 `:1422-1423`。
   - 另外两处也复核了，没错：hd_nbc404_gov_longyou 是 3847–3848 行，hd_304_chief_longyou 是 zz_hd_304_characters.txt 380–381 行。
   - 下文第四节已更新。

2. **[minor] 立绘须发行仍用 DLC 或草原物件**：本轮不改，已写进第三节第 8 条和第七节待实测。
   - 涉及第 112、113 行，物件是 mpo_mongol_*、steppe_*。
   - 不改的理由：03 §6 #5 的修法和任务原文都只要求改衣、冠行（121、122 行）。改须发属于范围外的外观决定。
   - 如果要彻底去掉 DLC 依赖，需要另开一项。

3. **[minor] 英文附 b 中英不一致**：已修，直接改了 p4-D 的暂存副本。
   - 位置：`localization/english/zz_hd_english_completion_nbc_l_english.yml:217`，键 `bm_hd_346_zhang_zhonghua_desc`。
   - "at twenty-one" 改为 "barely twenty"，现在这句是 "…has only just inherited power this year, barely twenty. …"。
   - 只替换了这一处。改后 BOM 还在，CRLF 为 0（仍是 LF）。
   - 原报告第四节第 5 条交给汇总人的这件事随之撤销。

**闸门复跑**：`gate.py --overlay p4-D --compare baseline.json --only-changed`，overlay 14 个文件，errors 0，相对基线没有新增（counts 为空），resolved_vs_baseline 0。输出在 D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p4-D_gate.txt

**仍未解决**：
- 须发行的 DLC 依赖：不在本轮范围，留待实测后再定。
- 第四节第 4 条的三名虚构首领：属人物数据，不归 4-D，交汇总人。
- 第四节第 3 条大厅显示：要改冻结文件，由汇总人定。

## 一、暂存任务名与文件清单
任务名 p4-D，共 14 个文件，与上一轮相同，`stage.py p4-D list` 可核对。暂存区：D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p4-D\files

**新建 3 个**（均为 UTF-8 带 BOM、LF）
- common/scripted_effects/zz_hd_j16_346d_flavor_effects.txt
- localization/simp_chinese/zz_hd_j16_346d_l_simp_chinese.yml
- localization/english/zz_hd_j16_346d_l_english.yml

**改现有 11 个**（原编码、BOM、换行均未变）
- localization/simp_chinese/zz_hd_nbc_l_simp_chinese.yml：BOM，CRLF。
- localization/english/zz_hd_english_completion_nbc_l_english.yml：BOM，LF。改了 bm_hd_346_liu_xuan_desc 和 bm_hd_346_zhang_zhonghua_desc 两个键。
- 书签立绘 8 个，只改第 121 行（衣）、第 122 行（冠），没动 entity、tags、id：
  - 346 的 bm_hd_346_zhang_zhonghua、_shi_hu、_yang_chu、_murong_huang：无 BOM，CRLF。
  - 370 的 bm_hd_370_fu_jian、_murong_chui、_murong_wei、_tuoba_shiyijian：无 BOM，LF。
- history/provinces/zz_uuii_generated_county_capitals.txt：BOM，LF。动笔前一刻才 stage edit。

## 二、各项实施（较上一轮只多了英文附 b）

**#1 刘玄书签世系**
- 中文 bm_hd_346_liu_xuan_desc 改为：刘玄是蜀汉昭烈帝的曾孙、甘陵王刘永之孙；唯他奔蜀，李雄封他为安乐公，奉后主之祀。
- 英文同键同步改：great-grandson of Emperor Zhaolie of Shu Han / grandson of Liu Yong, Prince of Ganling / Li Xiong made him Duke of Anle。

**#3、#4、#8 国号与年号**
- 新文件里有四个效果：
  - 入口 hd_j16_startup_346_flavor_effect，带 346 日期闸门；
  - 入口 hd_j16_startup_404_flavor_effect，带 404 日期闸门；
  - 国号子效果 hd_j16_346d_realm_names_346_effect、hd_j16_346d_realm_names_404_effect，各自带日期闸门，可以重复调用。
- 调用的是原开局同一批效果，人物解析写法也相同（`character:$WHO$ ?=` 加 `is_alive`）：
  - #3 成汉：`hd_nbc_realm_name_effect = { WHO = bacong_li_026 NAME = dynn_title_han FIXED = yes }`。dynn_title_han 是原版键。
  - #8 仇池：346 用 chouchi_yang_052，404 用 chouchi_yang_017，都是 `NAME = dynn_title_hd_nbc_chouchi FIXED = yes`。新键 dynn_title_hd_nbc_chouchi 和 _adj，中文「仇池」，英文 "Chouchi"。
  - #4 代国：`hd_nbc_set_era_effect = { WHO = tuoba_005 KEY = jianguo YEAR = 9 }`。SG_nianhao_jianguo 已在 zz_hd_370_l_simp_chinese.yml:44。
- 覆盖顺序：hd_nbc_after_lobby_effect 先跑 era 和 realm_display，末尾才调 hd_j16_startup_346/404_effect。本入口挂在那两个入口末尾，所以一定晚于原设置。
- FIXED 会写进王朝变量 hd_fixed_realm_name，继承人沿用新国号。
- 四个人物 ID 都是现行 ID，不在合并删除名单里。

**#5 书签立绘**
- 服装模板在本 mod 的 common/genes/05_genes_special_accessories_clothes.txt 和 06_genes_special_accessories_headgear.txt。HanJin 里的同名文件与本 mod 一致。
- 配件定义在依赖 HanJIn_Clothes 的 gfx/portraits/accessories/hd_frontier_equipment.txt、hd_eastern_han_clothes.txt、hd_huaxia_headgear.txt。

| 人物 | 衣 | 冠 |
|---|---|---|
| 张重华 | hd_eastern_han_official_robe_01 255 | hd_huaxia_jinxian_guan 255 |
| 石虎 | 80 → xiongnu_noble | 108 → xiongnu_crown |
| 杨初 | hd_liangdang_01 255 | hd_huaxia_pingjinze_wuguan 255 |
| 慕容皝 | 150 → xianbei_rider_disc | 121 → xianbei_cone |
| 苻坚 | 80 → xiongnu_noble（自拟） | 185 → xiongnu_noble_cap |
| 慕容垂 | 128 → xianbei_archer_lamellar_shoulder（自拟） | 198 → xianbei_iron（自拟） |
| 慕容暐 | 151 → xianbei_rider_disc（自拟） | 211 → xianbei_pattern（自拟） |
| 什翼犍 | 105 → xianbei_archer_panel_shoulder（自拟） | 19 → xianbei_braid_band（自拟，取「索头」辫发） |

**#6、#7、附 b**
- #6：hd_nbc.0902、0905、0911、0920 四条天下通报改为旁观者视角，`[hd_news_*]` 占位符都保留。
- #7：「称燕王于龙城」改为「慕容皝称燕王，都龙城」。依据：337 年在棘城称王，341–342 年迁龙城。
- 附 b：中文「才二十一岁」改为「年方弱冠」；英文本轮已同步改为 "barely twenty"。

**#20 西宁倭人文化**
- 共改 21 处，原值都是 rite = fusang_pagan、culture = wa。这些省都不是县治（holding = none），所以只是修数据源，游戏里各县的文化不会因此变化。
- F16 四省改 qiang：3566、4316 的 rite 改 xirongfangling；4053、4346 的 rite 改 tengri_pagan。
- 另外 17 处照抄本县县治省的文化与信仰：
  - 4107、4376 → tangut；
  - 4357、4429、2961、4456、4466 → shaodang；
  - 3542 → tangut；
  - 4381 → hd_xibei / jingxue；
  - 4441 → diren；4411、4421 → diren / jingxue；
  - 4451、4452、4446 → baima；4366、4371 → diren。
- 其余 63 处 culture = wa 都在 e_uuii_fusang（日本），没动。

## 三、自拟与偏差（已合并更新）
1. #20：F16 四省用 qiang，按拍板执行。其余 17 处用「照抄县治省」规则，所以同在青海的 4107、4376 落为 tangut，与那四省不同。
2. #20：rite 随文化一起改。任务原文只写了文化，但 fusang_pagan 出现在中国境内同样明显是错的。
3. #20：有 6 处只列不改。
   - emishi/yamatai 出现在日本以外的 5 处：4341（c_baishi1）、3561（c_uuii_p_1536）、4436（c_qishan1）、4402（c_gansong1）、4314（c_taz1）。这 5 处同属 ID 错位，建议另行处理，改法同样可以照抄县治省。
   - 3971 kunu 在弁韩。
4. #5：苻坚的衣，以及慕容垂、慕容暐、什翼犍的衣和冠，都是自拟数值。慕容暐原本与慕容皝完全相同，现在冠不同。
5. 附 b 英文：任务和 03 都只要求改中文。按审查意见，在暂存副本里把 "at twenty-one" 同步改为 "barely twenty"，让中英一致。这一条属于小幅越出原任务。
6. #17 偏差记录：库中石韬的凶手是 hd_j16_yang_bei，依据 05 覆盖表，不是 03 写的 shangdang_shi_012。这是第 2 期的决定，不改。
7. 已知局限：新国号只在大厅之后生效，选剧本大厅地图仍显示「成」「武都」。解决办法见第四节第 3 条。
8. 立绘须发行没改：第 112、113 行的 beards、hairstyles 仍用 mpo_mongol_*、steppe_*。涉及慕容皝、石虎、杨初、苻坚、慕容垂、慕容暐。原因是修法只要求改衣、冠两行，彻底去掉 DLC 依赖需要另开一项。

## 四、需汇总人处理（已合并更新）
1. **4-C**：在 common/scripted_effects/zz_hd_j16_startup_346_effects.txt 的 hd_j16_startup_346_effect 末尾加一行：
   `hd_j16_startup_346_flavor_effect = yes`
   - 这一行必须写在现有 `if = { limit = { hd_history_events_enabled_trigger = yes } … }` 的闭括号之后，不能写在 if 里面。否则关掉史实事件规则的玩家会没有国号和年号。
2. **6-B**：在 zz_hd_j16_startup_404_effects.txt 的 hd_j16_startup_404_effect 末尾加一行：
   `hd_j16_startup_404_flavor_effect = yes`
   - 位置要求同上。
3. **可选，大厅显示**：在冻结文件 zz_hd_nbc_startup_effects.txt 的 hd_nbc_game_start_effect 里，`hd_nbc_realm_display_effect = yes` 之后加两行：
   - `hd_j16_346d_realm_names_346_effect = yes`
   - `hd_j16_346d_realm_names_404_effect = yes`
   - 两者都带日期闸门，可以重复调用。年号不要放进 game_start。是否改冻结文件由汇总人定。
4. **三名虚构首领**：这是人物数据，不归 4-D。建议手改，不要重跑 nbc gen.py 或 304 生成器，以免冲掉第 2 期的改动。三处都把 `culture = wa` 改为 `culture = qiang`，`rite = fusang_pagan` 改为 `rite = tengri_pagan`（与西宁县治同信仰；如更想用 xirongfangling 也可以）。行号已更正：
   - history/characters/zz_hd_nbc_characters.txt:1422-1423，hd_nbc346_gov_longyou（键在 1420 行）；
   - 同文件 :3847-3848，hd_nbc404_gov_longyou；
   - history/characters/zz_hd_304_characters.txt:380-381，hd_304_chief_longyou。
5. （原第 5 条「英文附 b」本轮已在暂存副本里修好，撤销。）
6. **告知 4-C**：成汉开局用了原版键 dynn_title_han 之后，TGP 天朝循环取国号时会用 `is_title_localization_key_used = dynn_title_han` 排除已被占用的「汉」。请核实这是否影响刘玄「举汉帜」的取名。
7. 不需要重跑生成器。

## 五、新增事件号、变量名、效果与面板
- 事件号：无。
- 面板行（交 F-1）：无。
- 新变量：无。只沿用两个现有变量：
  - 王朝变量 hd_fixed_realm_name，写在 bacong_li、yang_2 上；
  - 年号变量 SG_*，由 hd_nbc_set_era_effect 设置。
- 新效果 4 个：hd_j16_startup_346_flavor_effect、hd_j16_startup_404_flavor_effect、hd_j16_346d_realm_names_346_effect、hd_j16_346d_realm_names_404_effect。
- 新本地化键（中英各一份）：dynn_title_hd_nbc_chouchi、dynn_title_hd_nbc_chouchi_adj。
- 日志：HD_J16 flavor_346 FIRE startup、HD_J16 flavor_404 FIRE startup。

## 六、只读核查：第 2 期是否已落实（结论不变）
#2、#9、#11、#12、#13、#14、#15、#16、#17、#18、附 a 都已落实，证据见上一轮报告第六节，审查方已抽查属实。

- #17 的凶手有偏差，见第三节第 6 条。
- #9 只覆盖 03 所列范围；00_* 等文件里仍有约 1026 个中文 name，不在 03 范围，仅作记录。

未落实项：无。

## 七、待实测
- 进大厅看 8 张立绘的变体效果；同时看没有 mpo 或草原 DLC 时须发怎么回退（第 112、113 行）。
- 346 开局后核对：成汉显示「汉」、仇池显示「仇池」、代国年号显示「建国九年」。
- 404 开局后核对仇池国号。
- 杨初的继承人沿用「仇池」。
- 英文书签：张重华简介显示 "barely twenty"。