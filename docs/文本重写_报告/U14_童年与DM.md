# U14_童年与DM 文本重写报告（2026-10-09）

## 1. 改动概览

| 文件 | 改写键 | 删除键 | 新增键 |
|---|---|---|---|
| `localization/simp_chinese/event_localization/hd_mcpe_l_simp_chinese.yml` | 351 | 0 | 0 |
| `localization/simp_chinese/replace/dm_obedience_l_simp_chinese.yml` | 7 | 0 | 0 |
| `localization/replace/simp_chinese/dm_tiger_visible_localization_l_simp_chinese.yml` | 25 | 0 | 0 |
| `localization/replace/simp_chinese/culture/traditions/DM_cultural_traditions_l_simp_chinese.yml` | 1 | 0 | 0 |
| `localization/simp_chinese/dm_house_aspirations_l_simp_chinese.yml` | 0 | 0 | 0 |
| `localization/simp_chinese/DM_map_items_l_simp_chinese.yml` | 0 | 0 | 0 |
| `localization/replace/simp_chinese/dm_compat_nomad_l_simp_chinese.yml` | 0 | 0 | 0 |
| 拥有的脚本（共 139 个） | 均未改 | — | — |

合计改写 384 键。所有文件的 UTF-8 BOM、CRLF 换行、键序、`:0` 有无均原样保留。

### 1.1 童年性格事件 hd_mcpe（mcpe.13–35 及监护人回应 mcpegr.131–353）

- **接收者与人称**
  - `mcpe.N` 的接收者是孩子本人：正文由"我"改为"你"，"你"指孩子。
  - `mcpegr.N` 由 `mcpe_inform_guardian_effect` 发给真正的监护人（玩家）：正文由"我"改为"你"，"你"指监护人，孩子用 `[child.…]` 指代。
  - 人物引语（`d_<trait>` 里加引号的孩子原话）照旧用"我"。
- **选项**
  - 孩子的选项 `.a/.b/.c` 改成浅近文言短句。
  - 监护人的 `confirm_*`（肯定原特质）和 `*_change`（改换特质）也改成文言短句。
  - `*_change` 键由两个事件共用（例如 `mcpegr.13.calm_change` 同时用于 .131 和 .132），因此只写"往目标性格引导"，不针对某一种具体经过。
- **标题**：翻译腔标题全部重拟，各 2–8 字：
  - 迷恋在城里 → 情窦初开
  - 强盗的苏醒 → 市中遭劫
  - 罪的工价 → 天谴之说
  - 判断 → 小贼入室
  - 八卦 → 流言蜚语
  - 只是一个孩子 → 人微言轻
  - 其余标题同样重拟。
- **时代用词**
  - 城堡 → 府中/府邸
  - 导师 → 师傅/经师/先生
  - 市场 → 市上
  - 士兵 → 士卒
  - 玩具 → 玩物
  - 外国美食 → 异域珍馐
  - 旅行商人 → 货郎
  - 护符 → 符箓/护身符
  - 神明 → 鬼神/神灵
  - 葬礼 → 丧礼
  - 餐具 → 箸
  - 园艺 → 学种花木
- **选项文案与 `add_trait` 不符的地方，已改文案贴合脚本**（叙事本是残留翻译腔，按 §3 以脚本为准，不改效果）：
  - `mcpe.33.c`（content）：原文"园艺很像统治一个国家"与知足无关，改为"侍弄花草，便已知足。"
  - `mcpe.35.c`（patient）：原文"我什至不应该担心这个"，改为"何必着急，待我长成，自然无事。"
  - `mcpe.26.c`（deceitful）：改为"去便去，暗中再叫护卫跟着。"，点明暗中欺瞒。
  - `mcpe.16.b`（lustful）："间谍活动"改为"且先暗中窥看一番……"
  - `mcpegr.16.shy_change`、`mcpegr.16.lustful_change`：原文分别是"应该住在房间！""刚刚传递了一个绝佳的间谍机会"，属乱译，已重写。
  - `mcpe.34`：原正文以"同他们说起了……"结尾，选项接续成句时读不通（"说起了别偷懒了"）。正文改为完整句，三个选项改成独立短句。
  - `mcpegr.20.d_greedy`：原文"反正最后付钱的人是我"暗示监护人花钱，而脚本没有任何花费。改为"专挑了最贵重的一件，眼都不眨一下"，以免文案许诺不存在的扣款。
- **修好的 bug**
  - `mcpe.17.d`：原文用 `[child.GetSheHe]` 指被抢的仆役之子，实际指向了玩家孩子本人。已改为"那孩子"，删去该 scope。
  - `mcpe.30.c`、`mcpe.35.b`：删去英文强调符号残留 `*敢*`、`*必须*`。
  - `mcpegr.22.d_humble`：删去残留词"真实"。
- **scope**：只用各键或各事件原有的数据函数（child、guardian、bully、crush），未引入新 scope。新增的两处（`mcpegr.23.confirm_arbitrary` 的 `[child.GetFirstNameNoTooltip|U]`、`mcpegr.31.d_arrogant` 的 `[child.GetSheHe]`）都是 mcpegr 事件中必然存在的 `scope:child`。
- **未改**：`tradition_hd_mcpe_dummy_name/_desc`。这是隐藏传统（`is_shown = { always = no }`），按传统命名约定引用，不在界面出现。

### 1.2 DM 服从（dm_obedience）

- 3 个 send_option 描述 `DM_OBEDIENCE_*_OPTION_DESC`：
  - 删掉"消耗 60 影响力""接受意愿增加 #P 100#!""双倍的中等金钱"等数值复述，以及与 is_valid 提示重复的"仅可用于同一最高领地"。
  - 各改成一句用途说明。重金选项保留一句非数值的叙事，说明应允后须如数付金（扣款实际发生在 on_accept）。
- 4 个接受度明细 `DM_OBEDIENCE_*_ACCEPTANCE` 补上原版格式 `：$VALUE|=+0$`。原来这几行只有标签、没有数字，删掉描述里的数值后，玩家就只能在这里看到加成。依据：原版 `AI_BRIBE_REASON`、`PIETY_INTERACTION_ACCEPTANCE_SEND_OPTION` 等都带这一段。
- 未改：
  - `game_concept_obedience_threshold_desc`：§0 规定不改百科概念。
  - 各 `*_government_realm`、选项名、`*_COST`：cost 块的 desc 由引擎自带数值。

### 1.3 DM 可见本地化覆盖（dm_tiger_visible）

逐键与原版 1.20.0.4 对比：3 键与原版相同，12 键改动过原版，105 键为原版缺失后补写的键。只处理有问题的部分。

- **接受度明细缺 `$VALUE$`**（4 键）
  - `ach_host_intent_imprison_reason`：mod 版写作"东道主打算在活动中将你监禁"，人称错了（行动方是玩家），也丢了数值。现按原版逐字恢复为 `[GetModifier('ach_intent_imprisonment_modifier').GetNameWithTooltip]：$VALUE|=+0$`。该修正在原版 `common/modifiers/10_ach_modifiers.txt` 中存在，mod 未覆盖。
  - `AI_CLOSE_HOUSE_REASON` → "近支同宗：$VALUE|=+0$"
  - `AI_HOUSE_RELATION_ALL_MEMBERS_REASON` → "与集团各家的交谊恩怨：$VALUE|=+0$"
  - `AI_LOYAL_TRAIT_REASON` → "生性忠诚：$VALUE|=+0$"
  - 这三键原版本身缺失，由 DM 补写，补写时没带数值。
- **建筑描述**（5 键）：mozu 古坟群、特罗斯基城堡、博多港改成汉末时人视角，名称未改，另见第 5 节。
- **民众领袖特质三档 desc**：去掉"统治秩序""民众领袖"一类现代口吻，改写为"出身草野……振臂一呼""名号传遍数县""深得黔首之心，一呼万应，足以撼动州郡"。
- **春秋战国局势 desc**：去掉"新秩序""长期角力"。
- **大工程提示**（12 键：7 个 contribution、5 个 tooltip）：
  - 去掉"工程人员""建筑师""体系""动员能力"等现代词，改为"匠人""匠师""以备征发"。
  - 涉及山海关、曼荼罗都城的键只改了用词，未改所指，另见第 5 节。
- **未改**：
  - 名称、按钮、debug（`kns_debug_interaction`）。
  - 隐藏决议 `convert_to_meritocratic_decision_*`：已被 `zzz_dm_disabled_government_conversion_decisions.txt` 设为 `is_shown = no`。
  - 律令效果短句、`rf_*_desc`。
  - `CONVERSION_REFORMER_BONUS_VALUE`：script value 明细，原版同类键也不带 `$VALUE$`。

### 1.4 DM 文化传统（DM_cultural_traditions，replace）

- 全文件 1455 键中，1414 键与原版逐字相同，未动。35 键改动过原版，6 键为新增。
- 叙事键中只有 `tradition_tgp_art_of_war_desc`（汉传兵法）需要改：
  - 原文"汇为体系""兵站"是现代口吻。
  - 改为"自孙、吴、司马之法传世，此地兵书代代不绝。将帅自幼诵习，知奇正之变、攻守之宜，亦晓粮道转输、营垒器械之要，故能临阵不乱，远征不匮。"
  - 对应脚本 `zz_hd_auh_art_of_war.txt` 的参数：反制、攻城、补给时长、行军速度、统兵特质传授。
- `tradition_tgp_bushido_desc`：mod 只把原版的"主君"改成"主公"，属纯叙事，保留。
- 其余差异键都是条件或参数文本（C 类），有意改动的包括：
  - `uuii_disabled_out_of_map_region` 屏蔽地图外区域；
  - 政体条件去掉 celestial/meritocratic；
  - 熊猎描述删去长矛/弓细节。
  - 以上均保留。

### 1.5 家族志向、地图物件、游牧兼容

- **dm_house_aspirations**
  - 全部是名称（尚武、将门世家……）和参数标签，文件里没有任何 `_desc` 键，未新建。
  - `house_power_parameter_*` 共 73 键，在 `common/`、`gui/` 中均无引用。原版的志向参数标签用的是 `house_aspiration_parameter_*`，所以这批键疑似 DM 遗留的死键。原样保留，未删。
- **DM_map_items**：均为地名标签，按 §0 不改。问题见第 6 节。
- **dm_compat_nomad**：`nomad_title_name: "游牧营地"` 是名称，不改。

## 2. 效果改动清单

无。139 个拥有的脚本一个都没改。

童年事件每个选项的效果只有 `add_trait`（外加通知监护人），监护人回应的效果只有"保留特质"或"压力 + 换特质"。文案与效果的不符都属于翻译腔残留，按 §3 第 4 条改文案贴合脚本，没有改效果（见 1.1）。

## 3. 删除 / 新增的本地化键

无。

## 4. 跨单元请求

无。

`common/character_interactions/00_prison_interactions.txt`（只读相关脚本）通过 `desc = ach_host_intent_imprison_reason` 引用本单元的键。键名未变，不需要改脚本。

## 5. 超时代 / 域外内容清单（交用户决定去留）

以下建筑或工程位于汉末地图之外，或晚于汉末。名称都未改；描述按 §1F 写成汉末时人的视角。

| 键 | 原型 | 处理 |
|---|---|---|
| `building_mozu_tombs*`（百舌鸟古坟群） | 倭国古坟，4–6 世纪 | 写成"东海之外的倭地，相传葬着上古的君长"；原版有更好的叙事，DM 换成了泛泛之词 |
| `building_trosky_castle_01*`（特罗斯基城堡） | 波希米亚城堡，14 世纪 | 写成"极西之地"两座黑石孤峰远望如倾颓的城垣，即原版所说死火山玄武岩的意象 |
| `building_type_hakata_port_02`（博多港） | 倭国港口；"博多"之名晚出 | 写倭奴国津港与光武帝赐金印（57 年）一事，与汉末同时代 |
| `building_type_swahili_port_pemba`（奔巴港） | 东非港口 | 只有名称键，未改 |
| `great_project_type_*_shanhai_pass*`（山海关） | 明代关城 | 只改用词，未改所指 |
| `great_project_type_tooltip_mandala_capital_01–05`（曼荼罗都城） | 东南亚曼荼罗政体 | 未改 |
| `great_project_type_*grand_canals*`（大运河） | 隋代 | 提示改为"开凿并疏浚运河"，淡化"大运河"专名 |
| `situation_type_spring_and_autumn_situation*`（春秋战国） | 汉以前；来自 saas 子 mod | 改写 desc；是否在本 mod 中可见，交用户确认 |

## 6. 自拟项与不确定处（需用户拍板的标 ★）

1. ★ **BASHIQI_01"八十骑 / 八十骑营"名实不符**
   - 文件：`common/buildings/dm_preserved_buildings.txt`。
   - 名称和描述写的是精锐骑兵营，脚本效果却是 `monthly_piety`、`epidemic_resistance`、少量税收、曼荼罗虔诚，图标是 `icon_building_hospice.dds`，实为施舍院模板。
   - 它没有 `type = special`，而 `can_construct` 只要求城堡/城市/寺庙一级，很可能出现在所有封地的建造列表里。
   - 有三种处理：①把效果改成骑兵向，需定数值；②删除该建筑；③改名改描述去贴合施舍院效果，但名称按 §0 锁定。三者都超出文本重写的范围，未动，请用户决定。
2. ★ **童年事件链人称不一致**
   - 本单元 23 个新事件（mcpe.13–35）已按规范改为第二人称"你"。
   - 同一随机池里的 mcpe.1–12、36–47 以及基础游戏监护人回应，用的是原版 `child_personality.*` 键（第一人称"我"，属原版文本，不在本单元范围）。
   - 因此玩家会在同一条童年事件链里看到两种人称混用。若要统一，需另行覆盖原版键，请用户决定。
3. **补 `$VALUE|=+0$`（共 8 键）**
   - 4 个 DM_OBEDIENCE 接受度键、3 个家族集团 AI 理由键，各补了这一段；`ach_host_intent_imprison_reason` 恢复原版。
   - 这属于界面数值行的修复，不是文风改写。理由是原版同类键一律带 `$VALUE$`，缺了就只显示标签、不显示加减值。
4. **疑似失效的数据函数，只报告不修**
   - `DM_cultural_traditions` 有 9 键使用 `GetFaithDoctrine(...)`，原版 1.20.0.4 中文本地化里出现 0 次，原版对应键全部用 `GetDoctrineType(...)`。
   - 这 9 键是：`ACCEPTANCE_BASELINE_CLOSE_PLURALISTS`、`tradition_female_only_inheritance_requirements`、`culture_not_female_only_tt`、`culture_not_male_only_tt`、`female_only_law_faith_or_culture_trigger`、`male_only_law_faith_or_culture_trigger`、`female_preference_law_faith_or_culture_trigger`、`male_preference_law_faith_or_culture_trigger`、`equal_law_culture_faith_or_innovation_trigger`。
   - 它们可能是 1.19 时代的旧函数名，显示时可能报错或出现空白。
   - 另外，`culture_not_male_only_tt` 与它包裹的条件不符：
     - DM 文本写的是"文化须有启用男性专属继承的传统，且信仰不能是女性主导"。
     - `common/laws/00_succession_laws.txt` 第 1674 行的实际条件是：信仰为男性主导，或者文化没有 `female_only_inheritance` 参数。
     - 原版文本是"信仰须有男性主导教义，而文化不能有启用女性专属继承的传统"。它把条件里的"或"写成了"而"，但所指的两项与条件相同，比 DM 版贴近得多。
   - 以上都是条件文本，未改。建议由主控或用户确认后，把这 9 键整体恢复为原版写法（与原版只差函数名，`culture_not_male_only_tt` 另有语义差异）。
5. **DM_map_items 占位名**
   - 29 个山名标签为"无人区"，20 个湖/河标签只有一个"湖"或"水"字，如 `lake_juyeze`（巨野泽）、`river_hanshui`（汉水）。
   - 这是地图上的地名，按 §0 不改，但看起来像未完成的占位。请用户确认是否有意为之。
6. **`ceremony_house_power`（"崇礼"）**：在 `00_marriage_scripted_modifiers.txt` 中作为联姻接受度理由使用，同样缺 `$VALUE$`。但它同时是志向名称，按 §0 未改，请主控确认后可改为"崇礼家风：$VALUE|=+0$"。
7. **`mpo_siberian_permafrost_modifier_desc`**：末尾 `#weak` 段的"该修正可通过……移除"是原版自带的说明（mod 只删去了一个不可用的互动）。西伯利亚不在本 mod 地图内，保留未改。
8. **用字**
   - 小贼入室（mcpe.19.a/b）的选项是孩子对小贼说话，用"汝"，以免与正文中指称玩家的"你"混淆。
   - 监护人回应中直接对孩子说话的少数选项（如 `mcpegr.35.temperate_change`"你也该有个大人样了！"）保留"你"，属人物引语。

## 7. 校验结果

`python -X utf8 docs/tools/text_rewrite_check.py --unit U14_童年与DM --audit`：

- **ERROR 0**
- **WARN 6**，逐条复核如下：
  - `NEWSCOPE ach_host_intent_imprison_reason`：`[GetModifier('ach_intent_imprisonment_modifier').GetNameWithTooltip]` 与原版该键逐字相同，修正在原版中存在，有效。
  - `UNTOUCHED culture_in_roman_empire_desc`、`sahara_percentage_desc`、`rulers_with_scholar_desc`、`culture_in_himalaya_desc`（数字）：均为条件文本（C 类），允许写阈值，与原版同构，保留。
  - `UNTOUCHED mpo_siberian_permafrost_modifier_desc`（"修正"）：见第 6 节第 7 条，原版自带的说明，地图外内容，保留。
- **人工补查**：校验器的 `NARR_KEY` 匹配不到 `mcpe.N.d.bully`、`mcpegr.N.d_xxx`、`confirm_*`、`*_change`。已另写脚本对本单元全部改写值扫描残留词、数字、`*`、"城堡/导师/士兵/玩具"等词，结果为 0。
