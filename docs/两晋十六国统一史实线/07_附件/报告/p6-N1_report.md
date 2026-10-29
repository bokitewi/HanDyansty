# p6-N1 最终报告（修正后合并版）

# p6-N1 修正报告：北线·后燕、北燕、南燕、北魏、后秦（E5）

审查意见共 7 条（1 major、6 minor）：5 条已修，2 条交汇总人裁定，不阻塞落盘。修后单路闸门仍是 **error 10、warn 54**，与修前相同，没有新增问题。只改了暂存区，没有直接写 mod，没有跑生成器，没有开游戏，没有提交 git。

## 〇、审查意见逐条处理

| # | 级别 | 内容 | 处理 |
|---|---|---|---|
| 1 | major | 燕位、龙城的回退解析可能把外国政权整个转给史实之人 | **已修**，见下 |
| 2 | minor | 不杀人的换主工具偏离 06 §0.4 | 不改代码，**交汇总人裁定，不阻塞** |
| 3 | minor | 5590 的逊位、拒之没有查节点是否已了结 | **已修**，a、b 都查 |
| 4 | minor | 授郡工具在「收回」方向也用 granted | **已修** |
| 5 | minor | 玩家慕容熙逊位后仍会死 | 改了文案，PRE 不动，**交汇总人裁定，不阻塞** |
| 6 | minor | 判胜里的同王朝项会把第三方算成攻方胜 | **已修** |
| 7 | minor | 西秦之主按 ID 解析，没有按位置 | **已修** |

**1（major）燕系认定，三层防护：**
- **燕系认定。** 新触发器 `hd_j16_n1_yan_system_trigger`（触发器文件），满足任一条即算燕系之主：
  - `dynasty:murong`；
  - `house:house_changle_feng`（冯跋 beiyan_0001，已核）；
  - `house:changli_lan`（兰汗 changli_lan_han，已核）；
  - 持有全局变量 `hd_j16_n1_yan_title` 所记的头衔。
- **为什么高云要按头衔认。** 高云 1415976 属 korean_go_goguryeo 王朝，与高句丽王同王朝同家族，按王朝或家族认会把高句丽王也放过。改为按头衔认：
  - 标记在 `hd_j16_gaoyun_after_effect` 里设，值为高云即位后的 `primary_title`。所有换主成功的路径（AI 转国、5590 a、5440 a）都会经过这个效果。
  - 按头衔认，高云死后由继承人接位时也能通过。
  - 标记没有放在 seat 里无条件写，以免 T60 与 M65 时间重叠时互相覆盖。
- **第一层：解析。** `hd_j16_n1_get_beiyan_ruler_effect` 的两档（扶黎、平州）都要求燕系；`get_yanwei` 第三档走它，同样受限。龙城落到外人手里时取不到，换主节点就等待，或到期跳过。
- **第二层：换主。** `hd_j16_n1_seat_effect` 新增对现任 CUR 的检查 `hd_j16_n1_seat_cur_ok_trigger`：须是燕系，或拓跋氏（T60 用）。不满足时只记一次日志 `WAIT seat_cur_foreign`（变量 `hd_j16_<TAG>_cwlog`）。
- **第三层：M45。** 燕主与高句丽王是同一人时，清掉燕主。

**3 5590 迟到。** 新触发器 `hd_j16_n1_abd_closed_trigger` 按 `var:hd_j16_n1_abd_tag` 分别查「已换主或已关窗」：

| TAG | 已换主 | 已关窗 |
|---|---|---|
| lanhan | lanhan_seated | lanhan_seat_skip |
| sheng | sheng_seated | lanhan_sheng_skip |
| xi | xi_seated | xi_done |
| gaoyun | gaoyun_seated | gaoyun_seat_skip |
| fengba | fengba_seated | beiyan_done |
| tuobasi | tuobasi_seated | mingyuan_done |

- 已逐个核过：xi_done、beiyan_done、mingyuan_done 只在换主完成或关窗时设，第一步 fire 时不设。
- `hd_j16_n1_abd_accept_effect`、`hd_j16_n1_abd_refuse_effect` 开头都加了这道检查。已了结时只记 `SKIP player_late_reply` 并清人物变量：不转国，不记 refused，也不让篡位者自立。

**4 授郡方向。** `hd_j16_n1_grant_duchy_effect` 加了 `$TYPE$` 参数。CK3 宏参数没有默认值，所以 6 个调用处全部显式传入：

| 调用处 | 方向 | TYPE |
|---|---|---|
| M25 第①档 | 封臣交还燕主 | revoked |
| Y30 乙段收姑臧 | 吕隆交还秦主 | revoked |
| M20 | 主君授出 | granted |
| Y10 | 主君授出 | granted |
| Y30 授王尚 | 主君授出 | granted |
| Y40 | 秦主或王尚把郡交给秦的封臣秃发傉檀 | granted |

- Y40 按主君授出处理。
- 原版 holy_order 效果里有 `type = revoked` 的用例，写法成立。

**5 熙逊位。** 不改 tsv。在 hd_j16.5440 选项 a 加 `custom_tooltip = hd_j16.5440.a.tt`，中英各一条，说明逊位亦难免一死。另起 PRE 的方案交汇总人定。

**6 判胜。** 7 处战争结局（canhe、pingcheng、weiye、chaibi、yaoluo、qifu、houliang）都删掉了「top_liege 同王朝」一项。
- 改为：关键县持有者或其 top_liege 是攻方本人，或者是按位置重新解析出的本方之主（exists 保护）。后者处理攻方战中身故、由继承人接战的情形，同王朝的第三方（例如西燕残部）不再算攻方胜。
- 判胜前补调的解析效果：
  - pingcheng：get_houyan；
  - weiye：get_wei；
  - chaibi：get_wei，从魏胜分支挪到判胜之前；
  - yaoluo、qifu、houliang：get_houqin；
  - canhe 原本就先调了 sides。

**7 西秦按位置解析。** 新增本路内联工具 `hd_j16_n1_xiqin_try_effect`。`hd_j16_qifu_sides_effect` 改为：
- 先按位置：枹罕 c_uuii_p_3062 → 金城郡首府 → 陇西郡首府，取其 top_liege，须有地、独立、乞伏氏；
- 取不到再退回乾归 qifu_008，再炽磐 qifu_010。
- 所用头衔与 6-N2 一致，但顺序不同：N2 是 ID 优先。

**2 换主工具（交汇总人）。** 代码不变。理由：
- 避免二次处死；
- 避免凶手记错（M60 用 seize 会记成高云，tsv 写的是冯跋）；
- 保留玩家的「大限」。

连带后果：旧主转出后无地，仍活在新主宫廷，直到卒年行到日。需要汇总人签字。

## 一、暂存任务名与文件清单

暂存任务名：**p6-N1**。暂存目录：`D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p6-N1\files\`

本路只新建文件，没有 stage edit 任何现有文件。6 个文件都是 UTF-8 带 BOM、LF，括号配平（已用脚本复核）。

| 文件 | 内容 |
|---|---|
| `common/scripted_effects/zz_hd_j16_395n1_effects.txt` | 入口 `hd_j16_e5_395n1_effect`、23 个节点、本路工具、按位置解析，3958 行 |
| `common/scripted_triggers/zz_hd_j16_395n1_triggers.txt` | 接壤、开战条件、西燕已不存在；本轮新增燕系认定、换主现任检查、5590 已了结检查，221 行 |
| `common/modifiers/zz_hd_j16_395n1_modifiers.txt` | 参合之殇、挫锋 |
| `events/zz_hd_j16_395n1_events.txt` | `namespace = hd_j16`，25 个事件 |
| `localization/simp_chinese/zz_hd_j16_395n1_l_simp_chinese.yml` | 110 键 |
| `localization/english/zz_hd_j16_395n1_l_english.yml` | 110 键，与中文完全一致 |

旧报告写的「108 键」是数错了，现以脚本实数为准；本轮只新增 `hd_j16.5440.a.tt` 一键。本轮新增的 4 个定义（3 个触发器、`hd_j16_n1_xiqin_try_effect`）已查过，与 mod 和另外四路暂存都不重名。

**范围（23 个节点）：**
- 后燕、北燕：M10、M15、M20、M25、M35、M45、M50、M60、M65
- 南燕：M30（开闸 murongde）、M40、M55
- 北魏：T10（闸门 tuobagui_2、tuobagui_3）、T20、T30、T40、T50（柴壁，用边境工具）、T60
- 后秦：Y10、Y20、Y30、Y40、Y50

**写法：**
- 立国一律交给入侵：M30 只开闸；节点不凭空建国（D2）。
- 404 开局：早于 404.3.24 的节点前标，即 M10–M50（M45 只前标 400 年那条）、T10–T50、Y10–Y30；只设 done，不设结果变量和面板变量。
- M55、M60、M65、T60、Y40、Y50 以及 M45 的 405 年那条，四个开局都走心跳。

## 二、自拟与偏差

1. **换主不杀人（偏离 06 §0.4，待汇总人签字）。**
   - 节点 fire 只设卒年 PRE；卒年行到日杀人，玩家走 hd_j16.0001。
   - 史实受害者死后，主头衔若在非史实之人手里，由 `hd_j16_n1_seat_effect` 换主：
     - 现任是 AI：经 `hd_j16_n1_take_realm_effect` 转出（照 seize 的写法，删去 death；头衔逐个以 usurped 转出，再让封臣改投）。
     - 现任是玩家：弹 hd_j16.5590「逊位 / 拒之」。
   - 换主须同时满足：
     - 现任是燕系之主或拓跋氏（本轮新增）；
     - 史实之人在现任一系之内。
2. **燕系认定（本轮新增）。** 认慕容氏、长乐冯氏、昌黎兰氏，或持有高云即位时所记的主头衔（`hd_j16_n1_yan_title`）。高云与高句丽王同王朝同家族，所以只能按头衔认。龙城落入外人之手时，解析取不到燕主，换主节点等待，或到期跳过。
3. **判胜（本轮改）。** 关键县持有者或其 top_liege 是攻方本人，或者是按位置重新解析出的本方之主，才算攻方胜；同王朝的第三方不算。
4. **授郡 TYPE（本轮新增）。** 收回用 revoked（M25 第①档、Y30 乙段收姑臧），授出用 granted（M20、Y10、Y30 授王尚、Y40）。
5. **西秦解析顺序（本轮改）。** Y20 先按位置（枹罕 → 金城首府 → 陇西首府），再按 ID（乾归 → 炽磐）。这与 6-N2 的 ID 优先顺序不同。
6. **5590 迟到（本轮新增）。** 逊位、拒之都先查节点是否已了结（已换主或已关窗），已了结则只记日志。
7. **5440.a 文案（本轮新增）。** 写明逊位亦难免一死；PRE 不变。
8. **玩家选 b 当即 done 加 `_skip`**，不走 TEMPLATE 的 `_wait` 90 天；06 原文是「到期跳过」，结果相同。选 a 设 `_go`，开战失败时下一跳由心跳重试，不再弹窗。
9. **命名。**
   - 06 §0.2 的 `hd_j16_get_<线>_ruler_effect` 改为 `hd_j16_n1_get_houyan / beiyan / yanwei / nanyan / wei / houqin_ruler_effect`，因为 6-N2、6-E4 各有自己前缀的同类效果，原名会冲突。
   - scope 名统一写成 `hd_j16_e5<节点号>_*`，避免与 E4 补遗的同号节点撞名。
   - 本路小工具一律以 `hd_j16_n1_*` 开头。
10. **燕主的解析。**
    - 「燕位」：先取龙城（扶黎）之主，须为慕容氏或冯氏且独立；再取后燕（中山一线）；最后取龙城或平州的燕系独立之主。
    - 后燕解析会先解析南燕之主，与之相同者不取。
    - 404 开局核过：中山、冀州归魏，e_youyan 归拓跋珪，扶黎归慕容熙。
11. **M10：** 1.2 万事件兵归燕主，没有指定慕容宝统领（spawn_army 不能指定将领）。
12. **M25：**
    - 第 ② 档只给昌黎宣称；「3 年 AI 宣战倾向」没有现成写法，未做。
    - 第 ③ 档「最北之县」按固定的郡序取燕主直辖的第一县（昌黎、辽西、辽东、玄菟、右北平、渔阳、东乌桓、宇文）。
    - 慕容详称帝的新闻未做。
    - 「中山被围」用 `county_controller = 魏主` 判断。
13. **M35 的时间线：**
    - 第一步 fire 设 `lanhan_s1_result`，并开始 90 天计时；
    - 宝 398.4.26 由卒年行处死后，兰汗换主；
    - 兰汗在位且计时到期，设 `lanhan_result`；
    - 兰汗 398.8.15 由卒年行处死后，慕容盛换主；
    - 后续各步都止于 399.6.1。
14. **M45：**
    - 去掉了「辽东接壤」条件，只看燕主与高句丽王是否都在世；二者为同一人时不算。
    - 06 写的 `hd_nbc_gjl_gao_tan_de` 第 2 期已并入 `korean_go_goguryeo_13`，改用后者。
    - 两条新闻的子窗口：400.2.1–401.10.1，405.1.1–406.1.1。
15. **修正：** 引擎没有「士气」修正，以 `advantage −5` 代替。「挫锋」的数值是自拟的：补员 −15%，advantage −3。
16. **T10：** 拓跋仪只入魏主宫廷，「任将」没有现成写法，未做。另向全体玩家发「晋阳之失」新闻 5500。
17. **T20：** 06 只写「威望 +、一笔金」，自拟为威望 +300、金 +200。
18. **议政：** 魏、北燕不是 h_china 政权，没有朝官，崔宏「尚书」、冯跋「首席议政」改授 councillor_chancellor，冯素弗授 councillor_marshal。
19. **只对 AI 生效的部分：**
    - M40、T40：迁都只对 AI 做；称谓和改元对玩家也做。
    - M55：慕容德是 AI 才立慕容超为储。
    - T60：拓跋珪是 AI 才立储。
20. **M20：** 慕容德已有县时 done 加 `_skip`，不设结果变量。
21. **M30：** 404 前标不设 go。404 局 `hd_hi_done_murongde` 由 6-B 预设（p6-B 暂存第 14 行）；若设了 go，年度块会在 404 局补试起兵。
22. **M60 与 5590 的「拒之」：** 篡位者若是 AI、有地、在玩家治下，就当场自立，作为 A3-F13「拒之即内战」的软化（已了结时不生效）。
23. **Y30：**
    - 上游：E5-X42 已 done（`hd_j16_lvlong_done`），或已过 401.12.1。
    - 甲段 done 为 `hd_j16_houliang_done`（战或降）；乙段沿用 `hd_j16_houliang_end_done`。
24. **Y20、Y30：**
    - 战后玩家选「不从」（5562 b、5572 b）只记日志。
    - Y20 不给事件兵。
    - 称藩须秦主的头衔等级高于对方，否则记 `SKIP vassal_tier`。
25. **Y50：** `hd_j16_yaohong_heir` 是卒年 PRE，只在 fire 设；done 另起 `hd_j16_yaohong_done`。玩家姚兴给 5580 a / b 两个选项。
26. **T50：** 魏主是 AI、秦主是玩家时，给秦主发 5521（a 迎战 / b 求和）。双方各 0.8 万事件兵，在平阳一带的前线县生成。

## 三、本期面板行清单（交 F-1，只列不写）

组：`hd_hev_grp_j16_e5`。

| 变量 | 含义 | 设置处 |
|---|---|---|
| `hd_hev_j16_canhe` | 参合陂之战 | M10 开战成功时 |
| `hd_hev_j16_zhongshan` | 魏取中山 | T20 fire |
| `hd_hev_j16_nanyan_di` | 南燕称帝 | M40 fire |
| `hd_hev_j16_chaibi` | 柴壁之战 | T50 开战成功时 |

06 §4.4 规定一律用 le404，但这四件事都早于 404.3.24，404 局是前标、不会亮。建议改用 le370，由 F-1 决定。

## 四、需要汇总人处理的事项

1. **入口挂接：** p6-S 暂存的 `zz_hd_j16_e5_395_effects.txt` 第 35 行已有 `hd_j16_e5_395n1_effect = yes`。两路必须同批落盘。
2. **6-B 的 404 预设：** `hd_hi_done_murongde` 在 p6-B 暂存里，请确认一同落盘。
3. **换主工具签字（审查 minor 2，不阻塞）：** `hd_j16_n1_take_realm_effect` 不杀人，偏离 06 §0.4。若 6-N2、6-E4 也有同类换主，建议统一口径，写进实施记录。
4. **熙逊位仍死（审查 minor 5，不阻塞）：** 现行做法是接受，并在 5440.a 加文案说明。另一个选项是在 tsv 里给熙另起 PRE（如 `hd_j16_gaoyun_xi_killed`），逊位时不设，由汇总人定。
5. **西秦解析顺序：** 本路是位置优先，N2 的 `hd_j16_n2_get_xiqin_ruler_effect` 是 ID 优先，请对账。
6. **新依赖：** 本路依赖两个家族键 `house:changli_lan`、`house:house_changle_feng`，以及兰汗 changli_lan_han、冯跋 beiyan_0001 的 `dynasty_house`。日后人物合并或重跑生成器时，这两处不能动。
7. **跨路变量请对账**（见第六节两张表）。
8. **解析效果命名：** 06 §0.2 的统一名没有被任何一路采用，日后可合并；眼下互不冲突。
9. **生成器（F-3）：** 本路新引用的人物需要重跑 gen_hbirth，其中 06 §4.2「仅 D」名单里有 `shaodang_yao_016`、`gong_sun_wu_lou`。本路没有改 tsv，也没有改人物数据。
10. **tsv：** 9 个 PRE 与第 8 列完全一致，都符合 TEMPLATE §5-15，不需要改。

## 五、新增事件号

全部为 hd_j16 命名空间，共 25 个（本轮没有新增事件）：

| 线 | 事件号 |
|---|---|
| 后燕、北燕 | 5400、5401（魏主预警，M10 和 M15 共用）、5405、5410、5420、5430、5431、5440、5450 |
| 南燕 | 5470 |
| 北魏 | 5500、5510、5520、5521、5540 |
| 后秦 | 5550、5551（晋天子预警）、5560、5561、5562、5570、5571、5572、5580 |
| 通用 | 5590（换主：逊位 / 拒之） |

M30 不另发事件：玩家慕容德由入侵的 hd_hi.0200 处理。

## 六、变量名

**各节点的 done 与结果**（另有 `_skip`、`_wlog`；有玩家选项的另有 `_asked`、`_go`；战争节点另有 `_started`、`_won` 或 `_lost`、`_att`、`_def`、`_wsf_wlog`）：
- M10：`hd_j16_canhe_done`、`_started`、`_won`；燕败设 `hd_j16_canhe_yan_lost`
- M15：`hd_j16_pingcheng_*`
- M20：`hd_j16_de_ye_*`
- M25：`hd_j16_longcheng_*`
- M30：`hd_j16_nanyan_open_*`
- M35：`hd_j16_lanhan_done`、`hd_j16_lanhan_s1_result`、`hd_j16_lanhan_result`、`_s2_wait`、`_s2_skip`、`_seat_skip`、`hd_j16_lanhan_sheng_skip`
- M40：`hd_j16_nanyan_di_*`
- M45：`hd_j16_liaodong_400_done`、`_405_done`、`hd_j16_liaodong_done`
- M50：`hd_j16_xi_*`
- M55：`hd_j16_chao_heir_*`
- M60：`hd_j16_gaoyun_*`（另有 `_seat_skip`、`_after`）
- M65：`hd_j16_beiyan_*`（另有 `hd_j16_beiyan_after`）
- T10：`hd_j16_wei_bing_*`（另有 `_jwlog`）
- T20：`hd_j16_zhongshan_*`
- T30：`hd_j16_weiye_*`
- T40：`hd_j16_wei_di_*`
- T50：`hd_j16_chaibi_*`，魏胜设 `hd_j16_chaibi_wei_won`
- T60：`hd_j16_mingyuan_*`（另有 `_heir_set`）
- Y10：`hd_j16_yaoluo_*`
- Y20：`hd_j16_qifu_*`（另有 `_vassal`、`_tgt`）
- Y30：`hd_j16_houliang_*`（另有 `_vassal`、`_tgt`、`_b1`、`_end_done`、`_end_result`、`_end_skip`、`_end_wlog`）
- Y40：`hd_j16_guzang_tufa_*`
- Y50：`hd_j16_yaohong_done`、`hd_j16_yaohong_heir`

**换主：**
- `hd_j16_<TAG>_seated`、`_refused`、`_abd_asked`、`_swlog`，以及本轮新增的 `_cwlog`（现任不是燕系或拓跋氏，只记一次日志）。TAG 为 lanhan、sheng、xi、gaoyun、fengba、tuobasi。
- 人物变量 `hd_j16_n1_abd_tag`、`hd_j16_n1_abd_new`。
- 本轮新增全局变量 `hd_j16_n1_yan_title`：值为头衔，在 `hd_j16_gaoyun_after_effect` 里设，由 `hd_j16_n1_yan_system_trigger` 读。

**入侵接口：**
- `hd_j16_hi_gate_tuobagui_2`：M10 结局、玩家 b、截止、前标都设；T10 也设。
- `hd_j16_hi_gate_tuobagui_3`：T10 设，晋阳归魏时；截止和前标也设。
- `hd_j16_hi_go_murongde`、`hd_j16_hi_go_murongde_late`：M30 设。

**06 原名 → 本路名：**

| 06 原名 | 本路名 |
|---|---|
| `hd_j16_yaohong_heir`（当 done） | `hd_j16_yaohong_done` 作 done；`hd_j16_yaohong_heir` 只在 fire 设（PRE） |
| Y30 的 `hd_j16_houliang_end_done` | 保留作乙段 done；甲段新增 `hd_j16_houliang_done` |
| M10 燕胜（06 未命名） | `hd_j16_canhe_won` |
| §0.2 `hd_j16_get_<线>_ruler_effect` | `hd_j16_n1_get_<线>_ruler_effect` |

本路没有编号式变量名。

**我读别路的变量：**

| 变量 | 设置方 | 本路读处 |
|---|---|---|
| `hd_j16_xiyan_done` | 6-E4（E4-M55），已核 | M10 上游（也接受「西燕已不存在」） |
| `hd_j16_lvlong_done` | 6-N2（E5-X42），已核 | Y30 甲段上游（也接受 ≥ 401.12.2） |
| `hd_j16_pulse_started`、`hd_j16_start_year`、`hd_hi_done_murongde` | 核心 / p5-C / 6-B | 各处 |
| `hd_j16_border_chaibi_target`、`hd_nbc_<KIND>_active` | 边境工具 / `hd_nbc_start_war_effect`（参数名） | 各战争结局 |

**我设给别路的变量：**

| 变量 | 读取方 | 说明 |
|---|---|---|
| `hd_j16_qifu_done` | 6-N2 E5-X62 | 已核其读取；降附、未降、到期、前标都设 |
| `hd_j16_qifu_vassal` | 暂无 | 备用 |
| `hd_j16_guzang_tufa_done` | 6-N2 E5-X66 | 已核 |
| `hd_j16_houliang_end_done`、`hd_j16_houliang_done` | 暂无 | 备用 |
| `hd_j16_nanyan_di_done`、`hd_j16_chao_heir_done` | 6-S J70 | 供对账 |
| `hd_j16_yaoluo_done`、`hd_j16_yaohong_done` / `_heir` | 6-S J80 | 供对账 |
| 两道 tuobagui 闸门、两个 murongde go 变量 | p5-C 入侵侧 | 已落盘 |
| 4 个 hev 变量 | F-1 | 面板 |

## 七、卒年表 PRE 的设置处

tsv 第 8 列归本路的 9 个 PRE，全部只在 fire 时设；前标、跳过、到期、玩家拒绝、迟到回复时都不设。本轮判胜的改动会影响 `canhe_yan_lost`、`chaibi_wei_won` 的设置条件，但设置位置不变。

| PRE | 卒年行 | 设置位置 |
|---|---|---|
| `hd_j16_canhe_yan_lost` | 慕容绍 | M10 `hd_j16_canhe_result_effect`，燕败分支 |
| `hd_j16_pingcheng_started` | 拓跋虔 | M15 `hd_j16_pingcheng_war_effect`，开战成功时 |
| `hd_j16_lanhan_s1_result` | 慕容宝、段速骨 | M35 `hd_j16_lanhan_s1_effect`（AI 宝，或 5420 a） |
| `hd_j16_lanhan_result` | 兰汗 | M35 节点第二步分支 |
| `hd_j16_nanyan_di_result` | 辟闾浑 | M40 节点 fire 分支 |
| `hd_j16_gaoyun_result` | 慕容熙、高云 | M60 节点第一步（AI 熙），或 `hd_j16_gaoyun_abdicate_effect`（5440 a） |
| `hd_j16_mingyuan_result` | 拓跋绍 | T60 `hd_j16_mingyuan_fire_effect`（AI 嗣，或 5540 a） |
| `hd_j16_chaibi_wei_won` | 姚平 | T50 `hd_j16_chaibi_result_effect`，魏胜分支 |
| `hd_j16_yaohong_heir` | 姚弼 | Y50 `hd_j16_yaohong_effect`（AI 姚兴，或 5580 a） |

不归本路的 PRE：
- 乾归、吕弘、吕纂：6-N2
- 慕容超、公孙五楼、姚泓、姚赞（`hd_nbc_*_won`）：6-S
- 拓跋觚、窟咄、刘卫辰：6-E4

## 八、闸门

**单路（修后复跑）：** `gate.py --overlay p6-N1 --compare baseline.json --only-changed`
- 输出：`D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p6-N1_gate.txt`
- 结果：error 10、warn 54，与修前相同。没有 ref_scripted、ref_event、loc_missing 类问题。新变量 `hd_j16_n1_yan_title`、`_cwlog` 没有进 warn。

| 条数 | 变量 | 原因 |
|---|---|---|
| 7 | `hd_nbc_canhe / pingcheng / weiye / chaibi / yaoluo / xiqin / houliang_active` | 开战工具以 `hd_nbc_$KIND$_active` 设置，参数名误报（TEMPLATE §5-14） |
| 1 | `hd_j16_border_chaibi_target` | 边境工具以 `$KIND$` 拼名，参数名误报 |
| 1 | `hd_j16_xiyan_done` | 6-E4 设，已核 |
| 1 | `hd_j16_lvlong_done` | 6-N2 设，已核 |

54 条 warn 都是「只写不读」：
- 各节点的 `_skip`、`_result`、`_won`、`_lost`；
- 4 个面板变量，由 F-1 读；
- `chaibi_wei_won`、`yaohong_heir`：卒年文件以 PRE 宏参数读取，属误报。

**五路合跑：** `--overlay p6-S p6-N1 p6-N2 p6-E4 p6-B`
- 输出：`D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p6-N1_fix_all5.txt`
- 结果：本路只剩上面 8 条参数拼名误报，与审查时的合跑相同，没有新条目。
- 其余 error 属别路：N2、E4、S 各自的 `_active` 拼名误报，以及 `hd_hi_started_tuobagui`、`hd_hi_started_tufawugu`、`hd_nbc_death_si_ma_de_wen_done`。

## 九、回归（08 §10）

- R6：慕容一律用 `dynasty:murong`。
- R7：本路只新增文件，没碰 H 线、京口、入侵预设和 nbc 文件；404 局 H 线行为不变。
- R1–R5 与本路无关。

## 十、实测项

1. `hd_j16_n1_take_realm_effect` 的新主是无地廷臣时的表现：慕容熙、高云、拓跋嗣、慕容盛、兰汗、冯跋。预期新主接收全部头衔后独立，原封臣改投新主。
2. `set_designated_heir` 立侄子（慕容超）、立子（拓跋嗣、姚泓），在当前继承法下是否生效。
3. M25：
   - `county_controller = 魏主` 能否判出中山被占；
   - `set_realm_capital` 迁到扶黎是否成功；
   - `type = revoked` 收回昌黎郡时，封臣的意见惩罚是否过重。
4. Y30 乙段：用 revoked 把姑臧从吕隆收回给秦主，是否成功；意见惩罚如何。
5. 柴壁：边境 CB 能否开战（脚本 start_war 是否绕过 valid_to_start）；两支事件兵的位置。
6. 5590：
   - triggered_desc 读人物变量的写法是否生效；
   - 玩家逊位后是否就此结束游戏；
   - 关窗后才点选项，是否只记 `player_late_reply`。
7. 404 局：M60 能否经龙城解析到慕容熙；M55 慕容超能否入南燕宫廷。
8. Y20、Y30：
   - 后秦为帝国级、西秦或后凉为王国级时，称藩能否成功；
   - Y20 能否按枹罕或金城首府位置解析到西秦之主。
9. 高云死后，其继承人能否凭 `has_title = global_var:hd_j16_n1_yan_title` 通过 M65 的现任检查。
10. 龙城归北魏或高句丽的偏离局里，M50、M60、M65 能否只记 `seat_cur_foreign` 或不解析，最后到期跳过，不转外国。