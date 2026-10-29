# p6-S 最终报告（修正后合并版）

# p6-S 修正报告：南线刘裕 404–421（06 §2、§3.1 南线、§4.5；R5、R7）

审查意见共 6 条，全部为 minor，均已处理。只改了暂存区 p6-S：没有直接写 mod，没有跑生成器，没有开游戏，没有提交 git。

## 〇、审查意见逐条处理

### minor-1：J85 不认「J82 只授长安县」的镇守者（已修）
- 改法：J85 判定镇守者时，原先只认 `has_title = title:d_jingzhao`，现改为「持 d_jingzhao 或持长安县 c_uuii_p_867」（OR）。文首注释同步改了。
- qingni 的目标仍是 `title:d_jingzhao`。核过 `hd_wct_build_effect`：它按 `every_in_de_jure_hierarchy` 从法理县里筛出守方持有的县，所以京兆郡头衔没有持有者时，目标照样成立，不必再退到别的郡。
- 「J80 胜后 CB 的 on_victory 会不会留下无主京兆郡」须进游戏看，列入实测项第 10 条。

### minor-2：J76、J82 授郡后受郡者会改投天子（已修）
- 新增本路小工具 `hd_j16_395s_grant_duchy_liu_effect = { DUCHY TO LIU LOG }`，放在 reclaim 小工具之后，执行顺序如下：
  1. 先记下原持有者 `scope:hd_j16_395s_gl_from` 和刘裕 `scope:hd_j16_395s_gl_liu`（两者先清后存）；
  2. 调 370b 的 grant 授郡；
  3. 满足以下全部条件时，受郡者调 `hd_nbc_swear_fealty_effect` 改投刘裕：原持有者是刘裕本人或刘裕的下属；刘裕在世且有地；受郡者有地、不是刘裕本人，且刘裕不是他的主君或更上级（`NOT target_is_liege_or_above`）。
- 调用处有两个：
  - J82 授京兆：LIU 传 `scope:hd_j16_le_liu`；
  - J76 结局授蜀郡：结局效果里新解析 `scope:hd_j16_ps_liu` 后传入。
- J82 只授县那一支没有改：原逻辑本来就让受者改投原持有者。

### minor-3：桓玄之死缺凶手冯迁（已修）
- 位置：`hd_j16_restore_exec_effect` 的桓玄一段。改法：
  - 先用 `hd_j16_370b_res_effect`（先清后解析）把 `hd_j16_feng_qian` 存为 `scope:hd_j16_dk`；
  - 冯迁在世且不是桓玄本人时，传 `HAS_KILLER = yes`；
  - 取不到人时保持 `HAS_KILLER = no`。
- 死因仍用 death_battle。R7 要求 AI 照旧战死，06 E5-J51 只改了凶手（卒年表第 100 行写的是 death_execution，见第一节第 15 条）。

### minor-4：互读变量表漏项（已补）
见第五节「我设给别路的变量」。补了三项：`hd_j16_houqin_won/_lost`、`hd_j16_nanyan_won/_lost`，以及 J70、J80 出结局时清 `hd_nbc_nanyan_active` / `hd_nbc_houqin_active` 这一行为。

### minor-5：卒年 PRE 不该写成二选一（已改）
06 §2.1 已定 `hd_j16_*_won` 作 K 卒年前提，报告改为明确请汇总人改 tsv，见第三节第 2 条。

### minor-6：几处与 06 不一致却没写进报告
- **①（已改代码）**：J74 次步收回淮南时去掉了 `is_ai = yes`，刘毅是玩家也收（A6-F19 不豁免玩家）。
  - 5311 a 加了 `custom_tooltip = hd_j16.5311.a.tt`，提示淮南将收归朝廷；中英 yml 各加 1 键。
  - 文首注释改为「刘毅是玩家也收，5311 a 有提示」。
- **②、③**：写入第一节第 16、17 条。
- **④**：写入第三节第 7 条。

## 〇·一、复跑闸门
- 结果文件：`D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p6-S_gate.txt`
- error 8，warn 53，相对基线消掉 6 条，与修改前一致。没有新增未定义引用，也没有缺失的本地化键。
  - error 的构成不变：5 条 `hd_nbc_{luxun,luxunbei,fanyu,pingshu,qingni}_active`，由 `$KIND$` 拼名设置，属误报；1 条 `hd_nbc_death_si_ma_de_wen_done`，由 `$ID$` 拼名设置，属误报；2 条 `hd_j16_e5_395n1_effect` / `n2_effect`，定义在 N1、N2 暂存区。
  - warn 都是只写不读：卒年 PRE、面板 `hd_hev_*`、记账变量。
- 7 个文件都是 UTF-8 带 BOM、0 个 CR，txt 花括号配平；中英 yml 各 118 键，一一对应（原 117 键 + `hd_j16.5311.a.tt`）。

## 〇·二、仍未解决项
- **阻塞（不在本路能力内）**：N1、N2 入口效果须与本路同批落盘。
- 以下等汇总人或实测：
  - tsv 的 PRE 修改（第三节第 2 条）；
  - 冻结文件 `zz_hd_nbc_startup_effects.txt:106` 的去留（第三节第 7 条）；
  - J80 胜后 on_victory 会不会留下无主京兆郡（实测第 10 条）。

---
（以下为合并更新后的完整实施报告）

# p6-S 报告：南线刘裕 404–421

## 一、暂存任务与文件
暂存任务名：**p6-S**。暂存目录：`D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p6-S\files\`

**改动的现有文件（edit）**
- `common/scripted_effects/zz_hd_j16_e5_395_effects.txt`
  - 入口末尾加两行北线调用：`hd_j16_e5_395n1_effect = yes`、`hd_j16_e5_395n2_effect = yes`；
  - 7 个旧 H 线节点按 06 §2.1 改造；
  - 新增南线 16 个节点、J79 子步、J52 结局钩子、J75 次步；
  - 本路小工具，前缀 `hd_j16_395s_`（本次新增 `hd_j16_395s_grant_duchy_liu_effect`）。
- `events/zz_hd_nbc_events.txt`
  - 只改 0150、0210、0220、0221、0230、0240、0250、0260，不新增事件号；
  - 汇总人在 0161 加的那一行没动。

**新建文件（new）**
- `events/zz_hd_j16_395_events.txt`（`namespace = hd_j16`）
- `common/scripted_triggers/zz_hd_j16_395_triggers.txt`
- `common/modifiers/zz_hd_j16_395_modifiers.txt`
- `localization/simp_chinese/zz_hd_j16_395_l_simp_chinese.yml`
- `localization/english/zz_hd_j16_395_l_english.yml`

**复用的已落盘工具（只调用，不改）**
- 370b：`res`、`grant_duchy`、`employ`、`army`、`news` 五个效果；`jin_sima`、`in_jin`、`grantable`、`can_employ` 四个触发器。
- hd_court：`install_regency`、`usurp_common`、`is_regent`、`has_regent`、`regent_eligible`。
- 卒年：death_core 的 `kill_pre`、`violent`。
- 其他：`hd_nbc_start_war_effect`、`hd_370_change_era_effect`，以及 263 S5/S6 的 WJ_rf 写法。

节点实施要点同前次报告第二节，本次修正只动了 J51/J52 执行体、J74、J76、J82、J85，内容见第〇节。

## 二、自拟与偏差
1. **冻结文件不改**：执行体全部改用 e5_395 里的 `hd_j16_*` 复制版。旧的 `hd_nbc_fuzhoushan/restore/song_effect` 已无调用者，但保留定义。
2. **收回郡交给天子**：用自写的 `hd_j16_395s_reclaim_duchy_effect`（`type = revoked`、不改投），不用 370b 的 grant。原因：370b grant 会让受领者改投原持有者的主君，用在天子身上，天子会去做封臣。
3. **06 §0.4「无地」收紧**：J45、J53–J55、J82 一律加 `is_landed = no`。
4. **J61 选 b 由 J73 接管 fanyu 战，不开第二场**（00 §7-12 未定）。此时 J73 自 405.4.1 起可开打，刘裕只需在晋、有地。
5. **休战天数分档**：没有日期差运算，按开战年份分两档（406 年前 1460 天，之后 1095 天），保证在 410.1.1 前到期。
6. **补充玩家事件**：J74 刘毅为玩家时加 5311，J75 刘裕为玩家时加 5316。依据 06 §0.1-5，06 表里没写这两项。
7. **J85 中勃勃是玩家时**不替他开战，只走①分支。
8. **J86** 只给 AI 天子 `set_designated_heir`。
9. **宋国显示名**：`wj_rf_name_code = 0`，`wj_rf_stem_capital` 指头衔自身（名「宋」），避免显示成「彭城公」。
10. **J84、J88 玩家辞让**：发事件时只设 `_asked`。第一次辞，设一年的 `_declined` 和 `_declined_once`；第二次辞，节点了结。
11. **恭帝之死**：由 5360 每 30 天自查一次，调 K 宏：DATE 421.10.15，凶手褚淡之，PRE 为 `hd_j16_song_result`。只在旧天子是德文时排程。
12. **J82 授地不成**：只记 SKIP，不设 PRE。
13. **J86 改元**：用 `hd_370_change_era_effect`（06 原写 `hd_nbc_set_era_effect`）。J52 奉迎改元义熙时，对象改为被奉迎者本人。
14. **J50 不加上游 done 读取**：J40、J42 已由「桓玄持 h_china、刘裕 top_liege 是桓玄」两条蕴含，符合 R7 条件逐字不变。
15. **（新）桓玄之死**：凶手按 06 E5-J51 改为冯迁（在世才带）。死因保留现状 death_battle（R7：AI 照旧战死）。卒年表第 100 行写的是 death_execution，用于 404 之前的开局；两者共用 done，先到者生效。
16. **（新，审查 6-②）J85**
    - 弃城只 `set_location`、不 `set_employer`：镇守者持郡，是统治者。
    - ①支用「勃勃与镇守者之主已交战（任意战争）」代替 06 的「第 3 阶段闸门已开且有对应战争」。理由：交战关系是可直接判定的事实，闸门开了但战争已结束或未开时，用闸门判反而会漏发或错发。只给 0.8 万兵，不重复开战。
17. **（新，审查 6-③）北线上游**：06 表列的 M40（J70）、Y50（J80）、X86（J85）没有直接读，由位置条件代替。
    - J70：广县或 d_qiguo 的 top_liege 是慕容氏、独立；
    - J80：长安的 top_liege 是姚氏、独立；
    - J85：镇守者持京兆或长安县，且勃勃独立、接壤。
    - 理由：北线变量由并行的 N1、N2 设置，本路不读别路当期变量（汇总人 10-27 定，避免对账依赖）；位置条件已覆盖这些上游想表达的局面。
    - X86 与 J85 窗口重叠：J85 的①支在已交战时不再开战，X86 先开战时 J85 只补兵，不双开。
18. **（新，审查 6-①）J74**：刘毅是玩家选 5311 a 后，次日也收回淮南（A6-F19 不豁免玩家），5311 a 有提示。
19. **（新，审查 minor-2）J76、J82 授郡在刘裕一系内**：用本路的 `hd_j16_395s_grant_duchy_liu_effect` 包一层 370b grant，授完后若受者不在刘裕一系内，改投刘裕。
20. **（新，审查 minor-1）J85 镇守者判定**：「持 d_jingzhao 或持 c_uuii_p_867」。qingni 的目标仍是 d_jingzhao，郡头衔无主也可（wct 按法理县筛选）。

## 三、需要汇总人处理
1. **阻塞**：入口已调 `hd_j16_e5_395n1_effect` / `n2_effect`，定义在 p6-N1 / N2 暂存区。**必须同批落盘**。
2. **卒年表 PRE（按 06 §2.1 已定，不是二选一）**：
   - 请把 `docs/两晋十六国_卒年表.tsv` 第 274、275 行（慕容超、公孙五楼）的 PRE 改为 `hd_j16_nanyan_won`；
   - 第 304、305 行（姚泓、姚赞）改为 `hd_j16_houqin_won`；
   - 改完重跑 `gen_deaths_effects.py`。
   - 理由：J70、J80 自判结局（白和但已据关键县也算成立）。原 `hd_nbc_*_won` 只在 CB 判胜时才设，口径与 06 不一致。
3. **落盘后重跑 hbirth、popclean**：新出现了 `ID =` / `KILLER =` 引用，包括：
   - 魏咏之、韩范、孙处、毛德祖、刘穆之、冯迁 `hd_j16_feng_qian`（本次新增引用）；
   - 刘义真 1800917、沈田子 1802134、沈林子 1802135；
   - beidi_fu_054、peixian_liu_008、congtingli_liu_044、suiyuli_liu_015、chu_dan_zhi、si_ma_de_wen 等。
4. **hd_nbc.0110（E2-J91 灭蜀封赏）**仍写死 `character:bacong_li_026`、`lujiang_zhou_004`，不在 06 §2.1 范围，本次未改。
5. **docs 同步**：01 §2.3 与 A1 表中 J70 上游、J90 窗口已在文首覆盖表里写明。00 §7-12 按第二节第 4 条落实。
6. **收尾清理**：nbc 冻结文件里三个旧执行体已无人调用。
7. **（新，审查 6-④）冻结文件 `common/scripted_effects/zz_hd_nbc_startup_effects.txt:106`** 仍在 404 开局调用 `hd_nbc404_court_effect`（随从入帐）。06 要求把它「搬进节点」，本路已在 J50 里另做一份，所以 404 局里两处各跑一次。
   - 两次都只对 AI、无地、未入帐者生效，重复跑无害。
   - 本路不改冻结文件。建议汇总人删掉这一行；若按 R7 保留现状，请在记录里写明。
8. **跨路重名已核**：本次新增的 saved scope `hd_j16_395s_gl_from/_liu` 已在 mod 全库和各路暂存区 grep，无冲突。只有公共新闻 scope `hd_news_a/_b` 共用，这是约定写法。

## 四、本期面板行清单（交 F-1，只列不写；组 `hd_hev_grp_j16_e5`，le404）
| 变量 | 内容 | 设置处 |
|---|---|---|
| `hd_hev_j16_liuyu_regent` | 刘裕秉政 | J45 exec |
| `hd_hev_j16_luxun_north` | 卢循北上 | J72 开战 |
| `hd_hev_j16_tao_liuyi` | 讨刘毅 | J75 exec |
| `hd_hev_j16_pingshu` | 平蜀 | J76 开战 |
| `hd_hev_j16_tao_xiuzhi` | 讨司马休之 | J78 exec |
| `hd_hev_j16_changan_lost` | 长安失陷 | J85 fire |
| `hd_hev_j16_songgong` | 宋公九锡 | J84 exec |
| `hd_hev_j16_gongdi` | 恭帝立 | J86 fire |
| `hd_hev_j16_songwang` | 宋王 | J88 exec |

给 F-1 的建议：
- 404_05、404_06 可加读 `hd_j16_nanyan_won/_lost`、`hd_j16_houqin_won/_lost`：节点自判后会清掉 `hd_nbc_*_active`。
- `liuyu_regent` 一行在 404 正常路径（由 J52 装权臣）不会亮，可加读 `hd_hev_404_restore`。

## 五、新增事件号与变量

**事件**：hd_j16.5245、5246、5253、5261、5262、5263、5270、5300、5301、5302、5305、5306、5310、5311、5315、5316、5317、5320、5321、5325、5326、5327、5329、5330、5331、5335、5336、5340、5341、5345、5346、5350、5355、5356、5360（隐藏），共 35 个，都在 5200–5399 内。

**新 KIND**：luxunbei、fanyu、pingshu、qingni。一律自判结局，不进分发表。

**旧名 → 语义名对照**
| 06 原名 | 现用名 |
|---|---|
| `hd_j16_jingkou_fired` | `hd_j16_jingkou_started` |
| `hd_j16_liuyu_regent_done`（作前提） | `hd_j16_liuyu_regent_result` |
| `hd_j16_fanyu_done`（作前提） | `hd_j16_fanyu_result` |
| `hd_j16_tao_liuyi_done`（作前提） | `hd_j16_tao_liuyi_result` |
| `hd_j16_pingshu_done`（作前提） | `hd_j16_pingshu_result` |
| `hd_j16_tao_xiuzhi_done`（作前提） | `hd_j16_tao_xiuzhi_result` |
| `hd_j16_liuyu_east_done`（作前提） | `hd_j16_liuyu_east_result` |
| `hd_j16_changan_lost_done`（作前提） | `hd_j16_changan_lost_result` |
| `hd_j16_songgong_done`（作前提） | `hd_j16_songgong_result` |
| `hd_j16_luxun_north_done` | 节点 done 沿用；开战另设 `hd_j16_luxunbei_started` |

上表各行的 `_done` 仍是节点防重入变量，跳过时也会设。

**其余变量**
- 各节点：`_done`、`_skip`、`_wlog`、`_asked`、`_started`、`_won`、`_lost`、`_att`、`_def`。
- 其他全局：`hd_j16_restore_hooked`、`hd_j16_liuyu_regent_granted`、`hd_j16_fanyu_go`、`hd_j16_luxun_jiankang`、`hd_j16_houqin_luoyang`、`hd_j16_liuyi_jingzhou_reclaim`、`hd_j16_tao_liuyi_war`、`hd_j16_tao_liuyi_after_done`、`hd_j16_lu_zongzhi_wait`、`hd_j16_gongdi_heir_set`、`hd_j16_songgong_declined/_declined_once`、`hd_j16_songwang_declined/_declined_once`、`hd_j16_song_result`、`hd_j16_song_asked`、`hd_j16_guanzhong_holder`（人物）、`hd_j16_song_fief`（头衔）、`hd_j16_song_wang`（头衔）。
- 沿用：`hd_hi_done_luxun`、`hd_j16_hi_gate_helianbobo_3`、`hd_hev_404_*`。

**新键**
- 零陵 `hd_j16_lingling_title_name`、宋 `hd_j16_song_fief_name`、休战名 `hd_j16_luxun_truce_name`、4 个事件兵名；
- 修正 `hd_j16_guangzhou_cishi_modifier`、`hd_j16_liuyi_xiezui_modifier`；
- 本次新增 `hd_j16.5311.a.tt`。

**我读别路的变量**
| 变量或触发器 | 来源 | 读处 |
|---|---|---|
| `hd_j16_cuanchu_done` / `hd_j16_cuanchu_result` | 5-A2（已落盘） | J45 ①支 |
| `hd_j16_hi_mode_trigger`、`hd_hi_try_start_<KEY>_effect`（只调用） | p5-C（已落盘） | 南线入侵分工 |

不读 N1、N2 当期的变量；北线上游改用位置条件代替，见第二节第 17 条。

**我设给别路的变量**
| 变量或行为 | 设置处 | 读者 |
|---|---|---|
| `hd_j16_hi_gate_helianbobo_3` | J80 所有出口（won、lost、window_closed、actor_dead、玩家 b） | N2 X86 也设，先到先设；p5-C 入侵阶段闸门读 |
| `hd_hi_done_luxun` | J60 的 0230 a；J72 开战或 b | 入侵系统 |
| `hd_j16_liuyu_regent_result` | J45 fire | 3-D 刘裕卡（zz_hd_asp_effects.txt:2660） |
| **`hd_j16_houqin_won` / `hd_j16_houqin_lost`** | J80 按长安归属自判 | N2 X86（zz_hd_j16_395n2_triggers.txt 约 97–105 行）；卒年表 304、305 行（待改） |
| **`hd_j16_nanyan_won` / `hd_j16_nanyan_lost`** | J70 按广县归属自判 | N1 南燕局面；卒年表 274、275 行（待改） |
| **行为：J70、J80 出结局时 `remove_global_variable` `hd_nbc_nanyan_active` / `hd_nbc_houqin_active`** | J70、J80 结局分支 | N2、N1 用来判断「没有进行中的场次」 |
| `hd_j16_guanzhong_holder` | J82 | 本路 J85；如北线要读关中镇守者也可用 |

## 六、卒年表 PRE 的设置处
| tsv PRE | 人物 | 设置处 |
|---|---|---|
| `hd_j16_jingkou_started` | 桓修、桓弘、刁弘、檀凭之 | `hd_j16_jingkou_war_effect`（开战成功） |
| `hd_j16_luxunbei_started` | 何无忌、孟昶、桓谦 | `hd_j16_luxun_north_go_effect`（开战成功） |
| `hd_j16_fanyu_result` | 徐道覆、卢循 | `hd_j16_fanyu_result_effect`（胜） |
| `hd_j16_tao_liuyi_result` | 刘毅、刘藩、谢混、郗僧施、诸葛长民 | `hd_j16_tao_liuyi_exec_effect`（AI 路径或 5316 a） |
| `hd_j16_pingshu_result` | 谯纵、谯道福 | `hd_j16_pingshu_result_effect`（胜） |
| `hd_j16_tao_xiuzhi_result` | 徐逵之 | `hd_j16_tao_xiuzhi_exec_effect` |
| `hd_j16_liuyu_east_result` | 王镇恶、沈田子、王修 | `hd_j16_liuyu_east_exec_effect`（授地成） |
| `hd_j16_changan_lost_result` | 朱龄石、傅弘之 | `hd_j16_changan_lost_fire_effect`（J85 ①②支都调） |
| `hd_j16_songgong_result` | 安帝 | `hd_j16_songgong_exec_effect` |
| `hd_j16_nanyan_won`（请汇总人把 tsv 274、275 行改成它） | 慕容超、公孙五楼 | J70 结局自判（广县归属） |
| `hd_j16_houqin_won`（请汇总人把 tsv 304、305 行改成它） | 姚泓、姚赞 | J80 结局自判（长安归属） |
| （不在表中）`hd_j16_song_result` | 恭帝 | `hd_j16_song_exec_effect`；由 5360 调 K 宏 |
| （表第 100 行，无 PRE）桓玄 | 桓玄 | 404 H 线由 `hd_j16_restore_exec_effect` 调 `hd_j16_death_violent_effect`，凶手冯迁（在世才带），与表行共用 done |

跳过、前标、玩家拒绝时一律不设 PRE。`hd_hev_404_qiaozong`（毛璩）由入侵设置，不归本路。

## 七、闸门
- 结果文件：`D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p6-S_gate.txt`
- error 8，warn 53，相对基线消掉 6 条。

**error 逐条解释**
- 5 条 `hd_nbc_*_active` 只读不写：由 `$KIND$` 拼名设置，属误报（TEMPLATE §5-14）。
- 1 条 `hd_nbc_death_si_ma_de_wen_done`：由 `$ID$` 拼名设置，属误报。
- 2 条 N1、N2 入口效果未定义：须同批落盘。

**warn 都是只写不读，分三类**
- PRE：由卒年宏参数读取，闸门不认；
- 面板 `hd_hev_*`：交 F-1；
- `_skip`、`_att`、`_def`、`_result` 等记账变量。

## 八、回归
- **R5（304 永嘉衣冠南渡）**：304 节文件、衣冠南渡局势与兜底入口全部未动。
- **R7（404 H 线）**：
  - J50 条件不变，首跳开打，兵数与覆舟山排程不变。
  - J51、J52、J60 只把人物改为解析，并加 06 写明的钩子和补设。本次补齐 06 E5-J51 的冯迁凶手；死因不变。
  - J70、J80、J90 只按 06 写明的项目改。
  - `hd_hi_done_liuyu`、`juqumengxun`、`tande` 三个预设所在文件未动；谯纵入侵不受影响。

## 九、实测项
1. 延迟 5 天的 0210 能否带上 scope；同一跳内三个出镇节点都问玩家天子时，5253 携带的 scope 是否各自正确。
2. J45 授毗陵后，刘裕的政体能否通过 `hd_court_regent_eligible_trigger`。
3. `add_truce_both_ways` 不带 war 参数能否成立。
4. J72 从番禺攻江州时，wct 连通筛选是否放行。
5. `type = revoked` 收回郡；J74 刘毅为玩家时次日收淮南。
6. 郡国制下 `set_designated_heir` 是否生效。
7. 宋国、宋王两个 WJ_rf 头衔的建立、显示（「宋公」「宋王」）与销毁，以及 WJ_rf.4。
8. 0150 改为 root 后，E3-J30 玩家北伐能否正常开战。
9. 5360 的 30 天轮询，以及恭帝为玩家时的大限事件。
10. **（新）** J80 胜后 CB 的 on_victory 会不会留下无主京兆郡（会走 J82 只授县那一支）；只授县时，J85 能否认出镇守者并以 d_jingzhao 为目标开战。
11. **（新）** J82、J76 授郡后，义真（或王镇恶）、朱龄石是否成为刘裕的封臣，而不是天子的直属封臣。
12. **（新）** 404 局覆舟山胜后桓玄之死：AI 时战死、凶手冯迁；冯迁未出场时无凶手。