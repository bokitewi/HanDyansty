# U03_quix刺杀 文本重写报告（2026-10-09）

## 1. 改动概览

| 文件 | 改写键 | 删除键 | 新增键 |
|---|---|---|---|
| `localization/simp_chinese/hd_quix_murder_outcome_events_l_simp_chinese.yml` | 480 | 194 | 0 |
| `localization/replace/simp_chinese/hd_quix_murder_ongoing_events_l_simp_chinese.yml` | 0 | 12 | 0 |
| `events/scheme_events/murder_scheme/hd_quix_murder_outcome_events.txt`（脚本） | 失败事件 40 处选项效果、2002 一行描述 | — | — |
| `common/on_action/schemes/hd_quix_scheme_on_actions.txt`（脚本） | 未改（只有英文注释和事件池，无中文文本） | — | — |

校验器计数：改写 480、删除 206、改脚本 1。BOM、CRLF 和 `:0` 写法都保留了。事件脚本原本就混用 CRLF/LF（共 219 行 LF），改动后没有统一换行，只换掉了相关的几段。

事件脚本里实际引用的 480 个键全部重写，按"布置（1001–1020）→ 成功（2001–2020）→ 失败（4001–4020）"三幕一组，共 20 种手法：
- **人称**：正文一律改为第二人称"你"（"你的同谋""你派去的人"）。原文全是"我/我们"。人物引语里保留原样（2014 的“别过了。”、2018 的“永别了……”）。
- **选项**：全部改为 4–16 字的文言短句。成功事件里"被识破"的那一句写成矢口否认（如"纵火者自是狂徒，与吾何干！"）。失败事件的 a、b 两项按新效果统一：a 收手，b 再图（见 §2）。
- **标题**：同一手法的三幕用同一个标题。原来 1007"一个鲁莽的刺杀计划"、2007"一个大胆的袭击"、4004"梦魇"、4005"石冷"等各说各的，现在统一。布置阶段的标题不透露成败。
- **时代置换**：把欧洲中世纪的器物和场景换成汉末的，见 §5。
- **原文错误一并修正**：
  - 2006.a.discovered 原是从毒酒那一幕抄来的（"我喝的那瓶酒有毒？"）。
  - 2011.no_awareness_2 原是从假面舞会抄来的。
  - 2020.opening_1 夹着一句没翻译的英文。
  - 2009/4009 标题"勇者血字"是 Bloodletter 的误译。
  - 1019 说刺客是哑巴，4019 却写他开口问对方的名字，现在改为比画。
  - 2004.opening_3 的代词指错了人。
  - 2003/2019 等处有多处语序错乱和重复句。
- **格式**：成功事件的 owner_is_known/no_awareness/heh，失败事件的 desc/exposed/not_exposed，一律以 `\n\n` 开段，原来时有时无。英文 `!` 和 `...` 改为全角。2018 里转义的英文引号 `\"` 改为中文引号“”。
- **数据函数**：只用了原文件里已有的 `[target.GetName]`、`[target.GetTitledFirstName]`、`[target.GetSheHe]`、`[target.GetHerHim]`、`[target.GetHerHis]`、`[target.GetFirstNameNoTooltip]`、`[target.GetTitledFirstNameNoTooltip]`。所有事件都在 scope:target 下，没有用 `dummy_assassin_gender`。刺客一律称"刺客/那人/他"，不涉及目标的性别。

## 2. 效果改动清单

| # | 文件 / 位置 | 改前 → 改后 | 理由 |
|---|---|---|---|
| 1 | `hd_quix_murder_outcome_events.txt` · 4001–4020 选项 a（含 a.discovered 文案），共 20 处 | `show_as_tooltip = { scope:scheme = { end_scheme = yes }  if 被识破 { add_dread = minor_dread_gain } }` → `scope:scheme = { end_scheme = yes }` | 原来只"显示"阴谋结束，选项本身没有任何实际效果。我核对过 1.19 的 `generic_scheme_process_ending_effect`，它不会替选项结束阴谋；原版 `murder_outcome_reworked.0003` 也是在选项里真正 `end_scheme`。a 的文案是收手（"此事作罢""吾倦矣"），效果改为与之一致，写法照原版。去掉的 `add_dread` 只是提示上的重复：`immediate` 里的 `show_as_tooltip = { murder_failure_effect = yes }` 已经显示威慑，`after` 触发的 `murder_outcome_reworked.0004` 会真正施加，**威慑的实际数值没有变化**。 |
| 2 | 同上 · 4001–4020 选项 b，共 20 处 | `show_as_tooltip = { add_dread…; start_scheme = { type = murder … } }` + `hidden_effect = { save_scope_value_as = { name = restart_scheme value = yes } }` → `restart_murder_scheme_effect = yes` | 原来只显示"重新开始阴谋"。`scope:restart_scheme` 在本 mod 和 1.19 原版里都没有任何地方读取（原版只剩注释），所以选了也不会重来。b 的文案是再图之，按原版 0003 换成原版重启效果：提示里显示 start_scheme，实际重置阴谋进度。 |
| 3 | 同上 · `quix_murder_outcome.2002` 描述 | `random_valid` 只有 opening_1、opening_2 → 加上 `desc = quix_murder_outcome.2002.opening_3`，顺带把错位的 `}` 缩进理正 | 其余 19 个成功事件都是三选一，2002 的第三句（腹部中箭）定义了却从未接入。只影响显示哪一句，没有效果变化。 |
| 4 | 4007 选项 a/b 文案语义对调（脚本未动） | 原 a"这只是时间问题，[目标]！"（再来的意思）、b"我已经厌倦了这一切"（收手的意思）→ a"吾倦矣，此事作罢。"、b"早晚之事，[目标]且等着！" | 原文两项与 a=结束、b=重启正好配反。同类的 4008.a"你总有一天会付出代价"、4012.a 等也改成收手的口吻。4008.b"不过马的事很遗憾"补上"再图之"。 |
| 5 | 成功事件中暗示另有所得的选项（脚本未动） | 2017.a"把武器拿过来……我想留着它"→"此物之妙，名不虚传。"；2020.a"我们能不能让他们继续留用？"→"此辈来去无踪，可畏可畏。"；2007.a"男人们今晚吃得好！"→"诸君辛苦，今夜可安枕矣。" | 这些选项都没有宝物、雇佣或花费之类的效果。它们只是一句俏皮话，不是这一幕的叙事意图，所以按 §3 末条改文案，不加效果。 |

文案仍然描述正确、因而未动的脚本：
- 布置事件 1001–1020 的 a 继续执行，b 走 `hd_quix_defer_murder_setup_effect`，即原版 `restart_murder_scheme_effect`，加上原版键 `do_not_execute_murder_tooltip`"不尝试进行谋杀"。所有 b 的文案都写成"此计不妥/另作打算"，与重启对得上。
- 成功事件的 `scheme_owner_pov_murder_success_effect`、6001 击杀、死因 `death_mysterious`、压力 `stress_impact` 都没动。

## 3. 删除 / 新增的本地化键

- **删除 194 键**（`hd_quix_murder_outcome_events_l_simp_chinese.yml`）：儿童谋杀 1201–1206、2201–2206、4201–4206，囚禁谋杀 1301–1304、2301–2304、4301–4304，以及 5001.generic、5002.generic。这些事件在 HanDyansty 里从未移植，全仓 events/common/gui/localization 都 grep 不到引用（只剩英文文件里的同名键），校验器的"删除键仍被引用"检查也是 0。
- **删除 12 键**（`replace/…/hd_quix_murder_ongoing_events_l_simp_chinese.yml`）：`quix_murder_ongoing.3010.*`、`quix_murder_ongoing.3301.*`。mod 里不存在 quix_murder_ongoing 事件，这些键没有引用。
- **保留** `murder_event_title:0 "谋杀："`。它是原版键，原版谋杀进行中事件的标题还在用（`$murder_event_title$酒鬼同谋`），本文件是覆盖。
- 原文都在备份里：`docs/文本重写_备份_20261009/localization/simp_chinese/hd_quix_murder_outcome_events_l_simp_chinese.yml` 和 `…/replace/simp_chinese/hd_quix_murder_ongoing_events_l_simp_chinese.yml`。以后若移植儿童/囚禁场景，可从备份或英文文件取回。
- **调整（未新增）**：原 `quix_murder_outcome.4017.exposed_scheme` 那一行写的其实是亲自行刺（4018）的情节，又被放在 4018 段里。所以 4017（吹箭）真正显示的一直是"亲自翻窗撞梁"这段错文。现在这一行移回 4017 段，改写为吹箭的败露情节。4018 的败露文本另行处理，见 §4。
- **新增**：无。英文本地化未动。英文 `4017.exposed_scheme` 也还是错放的 DIY 文本，按规定不改，仅在此记录。

## 4. 跨单元请求

1. **U04_quix诱惑与zgrc · `localization/simp_chinese/hd_quix_missing_l_simp_chinese.yml`**
   - 该文件定义了 `quix_murder_outcome.4018.exposed_scheme`（原文"不幸的是，我撞上了[target.GetTitledFirstName]的守卫，身份已经暴露。"）。我的文件里没有这个键，所以它就是 4018（亲操匕首）被识破时实际显示的文本。为避免重复键，我没有在本单元文件里另写一份。
   - 请 U04 或主控把该行改为下面的文本。改后与本单元 4018.desc 衔接，并与 2018/4018 的第二人称和 `\n\n` 分段一致。所用 scope 在谋杀事件中有效。
   ```
    quix_murder_outcome.4018.exposed_scheme:0 "\n\n不巧你一转身，一头撞在了房梁上！你被撞得眼冒金星，坐在地上发愣。[target.GetName]在榻上坐起，难以置信地瞪着你，你们四目相对了好一阵，直到外头传来杂乱的脚步声，你才回过神来，跌跌撞撞地翻窗而逃。那一眼，[target.GetSheHe]已认清了你的脸。对方放出猎犬追你，你只好在泥沼里躲了一夜！"
   ```
   - 如果 U04 想按自己的文风重写，至少要做到三点：用第二人称，以 `\n\n` 开头，情节接得上"侍婢尖叫、你翻窗逃走"之后被认出。
   - **过渡期接缝**：U04 改好之前，亲操匕首被识破时显示的仍是 U04 那句第一人称旧文，而且它不以 `\n\n` 开头，会直接接在本单元第二人称的 4018.desc 后面。同一段里"你……我……"混用，读者看得出来，不只是外观上的小瑕疵。

## 5. 时代置换清单

原文场景属中世纪欧洲或近世风格，按汉末改写。手法本身和成败结构都不变：

| 手法（flag） | 原文 | 改为 |
|---|---|---|
| hired_arsonist | 木制旅馆/客栈 | 道旁逆旅、客舍 |
| archery_balcony | 阳台、街对面酒馆、马车 | 楼台凭栏、酒肆楼上、辎车 |
| poisoned_wine | 葡萄酒/美酒、酒瓶 | 醇醪佳酿、酒坛、鸩酒 |
| night_murder | 守卫 | 巡夜亭卒 |
| traitor_guard | 疏忽职守 | 仆役开门（标题"开门揖盗"） |
| daring_raid | 隧道突袭 | 穴地夜袭 |
| horseman_ambush | 骑士、长枪 | 骑手、长矛/刀 |
| imposter_healer | 放血医师（"血字""血书"误译） | 以砭石刺血的医工（标题"假医"） |
| masked_men | 化装舞会、舞池、"在球中被杀"（误译 ball） | 大傩/傩戏宴集、傩面舞者 |
| foreign_warrior | 异国战士、"洋大侠" | 西域胡客、弯刀、西去商队 |
| dog_attack | 战犬、狮子、奇美拉 | 猛犬（标题"嗾獒"，取晋灵公嗾獒），豺狼虎豹 |
| bath_house | 浴场、疗养池 | 城外汤泉、浴堂 |
| pushed_off_ledge | 冲出海 | 冲入大江 |
| market_murder | 市场 | 市集、市人 |
| captive_kill | 不存在的逮捕令、地牢 | 伪造文书、假称收捕，囚室 |
| poison_dart | 奇怪武器（吹管） | 南中蛮夷的竹管吹箭 |
| diy_murder | 壁炉、露台 | 火盆、楼台 |
| hired_brawler | 冠军斗士、拳手、坑道战士 | 外乡哑角抵力士 |
| assassins_guild | 秘密组织、契约 | 闾里少年"探丸"之党（典出《汉书·尹赏传》）、约书 |

另有两处时间说法：
- 1010 原拟"岁末驱傩"，因事件全年都可能触发，改为"城中将行大傩"。
- 1013 原拟"每逢休沐"，因目标未必是官员，改为"常独自去城外的汤泉"。

## 6. 自拟项与不确定处

1. **失败选项真正结束或重启阴谋（§2 第 1、2 条）**会改变实际玩法。原先两个选项都没有实际效果（之后阴谋处于什么状态，我没有验证），现在与原版谋杀失败事件 `murder_outcome_reworked.0003` 一致。失败选项没有 `ai_chance`，所以 **AI 阴谋者**失败后也会真正结束或重启阴谋，与原版相同；此前对 AI 同样不起作用。这是"效果以文案为准"下我对文案意图的理解，请用户确认。
2. **删除 206 个孤立键**（§3）。如果打算日后移植 quix 的儿童/囚禁谋杀场景，也可以改为保留，从备份恢复即可。
3. **典故与时代置换**是自拟的："探丸之党""大傩""嗾獒""南中吹箭""角抵力士""汤泉"，选项里还有"竖子不足与谋""彼等恨我何妨，畏我足矣"等。
4. **只报告、未修的脚本问题**：布置事件 1001–1020 的 b"另作打算"走的是重启。成败在布置事件之前就已掷定，所以玩家可以在失败已成定局时选 b，躲开失败后果（被识破、威慑、好感惩罚等），换来一次重新开始。这是原 quix 整合时的设计，与文案无关，按 §3 只报告不修。
5. 2016"矫令收捕"的成功文本写目标被押到"你面前"，与原文一致。若目标与你相距很远，这一幕略显牵强，但原文就是这么写的，没有改动。

## 7. 校验结果

- `python -X utf8 docs/tools/text_rewrite_check.py --unit U03_quix刺杀 --audit --verbose` 的结果：**ERROR 0，WARN 0**（改写 480、删除 206、改脚本 1）。
- 校验器的叙事键正则匹配不到 `opening_N`、`owner_is_known_N`、`no_awareness_N`、`exposed_scheme`、`failure_declaration_N`、`.a.discovered`、`.heh`，所以另写脚本对全部 480 键做了逐条检查，结果如下：
  - 每个键都与备份不同。
  - `[...]` 之外没有阿拉伯数字、ASCII 字母或英文标点。
  - 没有残留词，也没有城堡、骑士、教堂、葡萄、舞会、合同、契约、警卫等词。
  - 叙事里没有"我"（引语除外）。
  - 选项都在 4–16 字之间，且不含"你"。
  - 开段的 `\n\n` 规则一致。
  - 剩下 2 条是误报："支吾"里的"吾"，以及侍婢的"她"。
- 事件脚本：花括号平衡；20 个失败事件改后结构完全一致（逐块对比）；LF 行数仍是 219，与改前相同。
