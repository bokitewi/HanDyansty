# p3-B2 最终报告（修正后合并版）

# p3-B2 修正报告：304 节外围节点（成汉、前凉、代、辽东三部与吐谷浑）

暂存任务名：`p3-B2`。只改了暂存副本：没有直接写 mod，没有跑生成器，没有开游戏，没有提交 git。

5 个文件仍全部为新建，都是 UTF-8 带 BOM、LF，花括号配平（逐个文件复核过）。暂存目录：`D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p3-B2\files\`

本轮实际改动三个文件：
- `zz_hd_j16_304b_effects.txt`
- `zz_hd_j16_304b_triggers.txt`、`zz_hd_j16_304b_events.txt`：只改 scope 名
- 中、英两个 yml：只改 0604 正文

## 零、审查意见逐条处理

| # | 问题 | 结果 |
|---|---|---|
| 1 | 吐谷浑→吐延的同王朝把关失效 | 已修 |
| 2 | 非直系储君可能不被引擎认可 | 已修 |
| 3 | 不杀夺位的效果会撞封臣层级限制 | 已修 |
| 4 | 末波杀涉复辰绕过卒年表 | 已修，需汇总人补表 |
| 5 | scope 前缀与他路撞车 | 已修 |
| 6 | actor_dead 分支不区分是否已 fire | 已修 |
| 7 | C3、C4 条件小缺 | 已修 |
| 8 | 0604 文案许诺改国号；玩家事件偏差未列 | 已修 |
| 9 | 报告第五节第 1 条已过时 | 已修 |

**1. 吐谷浑→吐延的同王朝把关失效（minor）**：两种修法都做了。
- 采用 (a)：`hd_j16_304b_rjt_effect` 的把关改为 `OR = { dynasty ?= 储君.dynasty ; 储君.father ?= 君主 }`，亲子不看王朝。
- (b) 也写进了第四节，交人物数据写入者处理：我已核实 `house_tuyuhun` 挂在 `zz_hd_oe_houses.txt` 的王朝 105818 下，是 murong 的 OE 重复。
- 引擎是否接受跨王朝的储君、本步是否依赖 3-C 开局立储，都列进了实测项。

**2. 非直系储君可能不被 `is_valid_designated_heir` 认可（minor）**：
- 加了独立分支：人已到位（有地、同王朝或亲子），但 `is_valid_designated_heir` 不成立时，单独记一次 `WAIT invalid_heir_<步>`。日志开关是 `hd_j16_<步>_ih_wlog`，与 `not_ready` 分开。
- 按代码里 17 个 R-继统调用逐个核对：7 对父子、10 对非直系（审查说 11 对，实为 10 对，清单见第五节）。

**3. 不杀夺位的效果会撞封臣层级限制（minor）**：`hd_j16_304b_seize_effect` 已调整顺序：
- 先转全部领地头衔；
- 再 `set_primary_title_to`；
- 最后收编旧主剩下的封臣，且只收 `highest_held_title_tier < 新主.highest_held_title_tier` 的。这个比较写法有原版先例。
- 副作用：不满足层级条件的封臣留在已无地的旧主名下，多半由引擎改为独立，列为实测项。

**4. 末波杀涉复辰绕过卒年表（minor）**：
- `hd_j16_mobo_li_effect` 改用本路的不杀夺位，并在 fire 时新设 `hd_j16_mobo_li_result`（原来没设）。
- 涉复辰之死请卒年表补 K 行，见第四节第 2 条。
- 我核对了 `hd_j16_death_kill_pre_effect`：它只查 PRE、凶手存在、凶手不是本人，**不查当事人是否在位**，所以涉复辰被夺位后变成无地，也不会让这一行一直顺延。
- 文件头注释已同步更新。

**5. scope 前缀与他路撞车（minor）**：前缀改为 `hd_j16_zsh_`、`hd_j16_lxw_`、`hd_j16_qhz_`。effects、triggers、events 三处已同步。已 grep mod 与各路暂存，没有他路使用这三个前缀。

**6. actor_dead 分支不区分是否已 fire（minor）**：E1-T10、E1-T20 的 actor_dead 分支改为：
- 已有 `hd_j16_zongshe_result`（T10）或 `hd_j16_daigong_result`（T20）时只设 done，记 `FIRE closed_actor_dead`；
- 否则才跳过。

**7. C3、C4 条件小缺（minor）**：
- C3 要求李越也满足 `hd_j16_304b_in_realm_trigger`（在成国内）。
- C4 的 actor_dead 改为李寿或李期（`bacong_li_016`）任一人已死即跳过。

**8. 0604 文案与玩家事件偏差（minor）**：
- 0604 中英正文已改，只说子孙以吐谷浑为氏、部众以此为号，不再提国号。
- 第二节新增第 18 条，说明 C3、C4、M2 的玩家事件偏离 02。

**9. 报告第五节第 1 条已过时（minor）**：已注明 3-B1 在暂存中加好了这两处调用，见第四节第 1 条。

**仍未解决（都需汇总人或实测）**：
- 涉复辰卒年行要补。不补的话，他的 history 卒日 318.1.1 属于未来日期，引擎不执行，他会一直活着；0600 的「袭杀」也会落空。
- `house_tuyuhun` 王朝重复。
- 非直系储君与跨王朝储君能否被引擎认可，要实测。

**闸门复跑**：命令照任务给定，结果在 `D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p3-B2_gate.txt`。
- **error 14**：与上次相同，全是 `gvar_read_never_set`，说明见第四节第 7 条。
- **warn 39**：比上次多 1 条，就是新加的 `hd_j16_mobo_li_result`，待卒年行读取。
- `resolved_vs_baseline` 1。
- 没有未定义引用，也没有缺失本地化键。

---

## 一、文件清单

| 文件 | 内容 |
|---|---|
| `common/scripted_effects/zz_hd_j16_304b_effects.txt` | 两个入口 `hd_j16_e1_304b_effect`、`hd_j16_e2_304b_effect`；18 个节点；本路小工具：R-继统一步 `hd_j16_304b_rjt_effect`、不杀夺位 `hd_j16_304b_seize_effect`、一郡宣称 `hd_j16_304b_claim_effect` |
| `events/zz_hd_j16_304b_events.txt` | `namespace = hd_j16`，15 个事件 |
| `localization/simp_chinese/zz_hd_j16_304b_l_simp_chinese.yml` | 59 键 |
| `localization/english/zz_hd_j16_304b_l_english.yml` | 59 键，与中文一一对应 |
| `common/scripted_triggers/zz_hd_j16_304b_triggers.txt` | `hd_j16_304b_tuoba_duchy_trigger`、`hd_j16_304b_zs_target_trigger`、`hd_j16_304b_in_realm_trigger` |

- 没有建 modifiers 文件。
- 复用了 3-A 的 `_res`、`_skip`、`_wait`、`_army` 四个小宏，以及 `hd_j16_304_war_result_effect`、`hd_j16_grant_duchy_effect`、本地化键 `hd_j16_xianbei_army_name`。
- 不依赖 3-B1、3-C 本轮的新定义。

节点总览不变：
- **E1 段**：C10、C20、L10、T10、T20、T30、M10；
- **E2 段**：C10、C20、C30、L10、L20、T10、M10、M20、M30、M40、X20；
- **E2-X10 美川王卒**：卒年表已有 `korean_go_goguryeo_18`（N 331.2.1），不设节点。

## 二、自拟与偏差（合并更新）

1. **R-继统只对 AI 君主做**。君主是玩家时记 `SKIP player_ruler`。
   - 储君须在世，且与君主同王朝或是君主亲子（本轮放宽，为吐谷浑三代）；还须满足 `is_valid_designated_heir`。
   - 不被认可为合法储君时，单独记 `WAIT invalid_heir_<步>`。
2. **R-继统起日一律取「卒年前 60 天」**：M2 由 333.10.1 提前到 333.4.13，M9 由 317.1.1 提前到 316.11.2。仁起兵一步仍从 333.10.1 起。
3. **夺位一律不杀**：C3、C4、T4③、M7③ 都用本路的 `hd_j16_304b_seize_effect`。
   - 顺序：先转头衔，再设主头衔，最后只收编层级低于新主的封臣。
   - 旧主之死交给卒年表：李班 K 334.12.5、李期 die 338.6.15、纥那 N 337.6.15；涉复辰待补 K 行，PRE = `hd_j16_mobo_li_result`。
   - C3 的夺位起日 334.12.5，与李班卒年同日。
   - 被夺者是玩家时跳过，记 `player_victim`。
4. **T4 的 335 年纥那复辟、337 年翳槐复位不做**，按 02「可略」。保留 329 年翳槐代纥那（窗口 329 年全年）。M7 中段牙一任略去，末波储君直接立段辽 `liaoxi_duan_011`。
5. **称号节点都直调 `hd_nbc_found_realm_effect`**。
   - L4 的 `STYLE = wang`。
   - 非郡国制的拓跋、慕容会因此改成 `celestial_government`。
   - FIXED：成、代、燕、汉为 yes，凉为 no。
6. **改元**：晏平、汉兴两个年号键未注册，本轮不改元（见第四节第 3 条）。什翼犍的「建国」照改，只对独立君主改。
7. **C2「罗尚原郡」取巴郡 `d_bajun`**。宣称只给 AI；玩家在 0451 选 a 才给。
8. **T1 每跳只授一郡**，顺序定襄、云中、拓跋，只从猗卢以外的拓跋族 AI 手里拿。起手条件：猗㐌已死、禄官不在世。援兵 AI 倾向不做。
9. **T2**：
   - 刘琨开局是无地冒险者，「刘琨为晋臣」只作结盟条件（在世、有地、是 AI、未与猗卢交战）；
   - 不做 10 年期满解盟；
   - 两跳都要求猗卢独立；
   - 第二跳起日 315.3.1 为自拟。
10. **M1 只给 AI**：不主动开战，只在廆作为守方身处战争时给 8000 兵。
11. **M2**：仁「持辽东县」按「持有任一法理属辽东郡的县」判；仁无地就一直等到关窗再跳过。8000 兵只在皝（AI）与仁交战时给一次。
12. **M6**：守方取逸豆归的最高领主；玩家在 0603 选 b 即了结；须在 344.6.15 逸豆归卒前开战，否则 `actor_dead`。
13. **C3「在国内」**：期的最高领主是成主，或其雇主是成主或成主的下属。成主按成都 `c_uuii_p_4282` 持有者的最高领主取，且须是巴賨李氏。本轮起李越也须在国内。C4 要求 C3 已 done；李期已死时 C4 以 `actor_dead` 跳过。
14. **T3 面板**：先在窗口内见到猗卢在世（`_seen`），他身死后才点面板。
15. **M9「以吐谷浑为氏」只做文案**：叶延是玩家时收 0604 通报，不改国号；文案已对齐。
16. **玩家答复后不补「迟答」处理**：照 TEMPLATE 的 0200 先例。
17. **L4 假凉王**：张骏有地、持凉州即可，不要求独立。
18. **C3、C4、M2 给玩家 a/b 事件**（0452、0453、0601）：依 01 §7.3 的玩家规则，偏离 02 表中「无分支」。
19. **T1、T2 在猗卢死于已 fire 之后**：只设 done，记 `FIRE closed_actor_dead`，不再设 `_skip`。

## 三、本期面板行清单（交 F-1，只列不写）

共 19 行，适用开局全部为 le304，变量都只在 fire 时设。其中 `zhangshi_heir`、`zhangmao_heir`、`lishi_heir` 三行经 R-继统宏以 `hd_hev_j16_$KEY$` 设置。

| 面板变量 | 节点 |
|---|---|
| `hd_hev_j16_lixiong_emperor` | E1-C10 李雄称帝 |
| `hd_hev_j16_qu_hanzhong` | E1-C20 罗尚死、成取汉中 |
| `hd_hev_j16_zhangshi_heir` | E1-L10 张轨卒、张寔嗣 |
| `hd_hev_j16_zongshe` | E1-T10 猗卢总摄三部 |
| `hd_hev_j16_daigong` | E1-T20 封代公 |
| `hd_hev_j16_daiwang` | E1-T20 进爵代王 |
| `hd_hev_j16_liuxiu` | E1-T30 六修之乱 |
| `hd_hev_j16_duanbu` | E1-M10 段部内争（末波自立） |
| `hd_hev_j16_liqi` | E2-C10 李期夺位 |
| `hd_hev_j16_lishou` | E2-C20 李寿废期、改国号汉 |
| `hd_hev_j16_lishi_heir` | E2-C30 李势立 |
| `hd_hev_j16_zhangmao_heir` | E2-L10 张寔被杀、张茂立 |
| `hd_hev_j16_liangwang` | E2-L20 张骏假凉王 |
| `hd_hev_j16_daitong` | E2-T10 什翼犍即代王、改元建国 |
| `hd_hev_j16_murong_jicheng` | E2-M10 棘城 |
| `hd_hev_j16_murongren` | E2-M20 慕容仁之乱 |
| `hd_hev_j16_yanwang` | E2-M30 慕容皝称燕王 |
| `hd_hev_j16_yuwen344` | E2-M40 灭宇文部 |
| `hd_hev_j16_tuyuhun3` | E2-X20 吐谷浑三代 |

## 四、需要汇总人处理的事项

1. **入口调用**：在 `hd_j16_e1_304_effect` 末尾加 `hd_j16_e1_304b_effect = yes`，在 `hd_j16_e2_304_effect` 末尾加 `hd_j16_e2_304b_effect = yes`。**这两处已由 3-B1 在暂存中加入（e1 第 44 行、e2 第 40 行），合并时核对即可，不要重复加。**
2. **【必须处理】卒年表补涉复辰 K 行**，各列如下：

   | ID | 类别 | DATE | DATE10 | 凶手 | REASON | PRE |
   |---|---|---|---|---|---|---|
   | `liaoxi_duan_004` | K | 318.6.15（本步窗口起点） | 328.6.15 | `liaoxi_duan_015`（末波） | death_murder | `hd_j16_mobo_li_result` |

   - 补完重跑 `gen_deaths_effects.py`，生成的应是 `hd_j16_death_kill_pre_effect`。
   - 末波若没有夺位，按 D15 到 328.6.15 改为病逝。
   - 不补的后果：涉复辰的 history 卒日 318.1.1 属于未来日期，引擎不执行，他不会死；0600 的「袭杀」也会与实际不符。
3. **年号**：
   - 在 `common/customizable_localization/WJ_tianjia_era_names.txt` 注册 `SG_nianhao_yanping`（晏平）、`SG_nianhao_hanxing`（汉兴），正文与 `_tt` 两处都要补，并补中英本地化。
   - 然后在 `hd_j16_lixiong_emperor_effect` 的 found_realm 之后加一行，包在 `is_independent_ruler = yes` 里：`hd_370_change_era_effect = { KEY = yanping YEAR = 1 }`。
   - `hd_j16_lishou_effect` 同样加一行：`hd_370_change_era_effect = { KEY = hanxing YEAR = 1 }`。
4. **人物数据：`house_tuyuhun` 王朝重复**。它挂在王朝 105818（`dynn_Murong`）下，这是 `dynasty:murong` 的 OE 重复，按 R6 应改挂到 murong。本路已用「亲子不看王朝」绕开，但改挂后更稳。
5. **交 3-C（头衔历史）**：E2-X20 依赖 `d_tuyuhun` 归 247346，并在开局立吐延为储君。3-C 暂存已衔接上，本路不需要别的头衔历史改动。
6. **人物数据（2-B 遗留）**：`tuoba_luguan` 的 `name = "禄官"` 仍是中文字面量，违反报错清单。
7. **闸门 error 14 条是误报**：都是 R-继统步的 `hd_j16_<步>_done`，在 `hd_j16_304b_rjt_effect` 或 `hd_j16_304_skip_effect` 里以 `hd_j16_$KEY$_done` 的带参数写法设置，闸门看不到。涉及的步：pugen_heir、yulv_heir、jiluojuan_heir、shefuchen_heir、duanliao_heir、ban_heir、jun_heir、zhonghua_heir、heru_heir、hena_heir、shiyijian_heir、huang_heir、tuyan_heir、yeyan_heir。
8. **闸门 warn 39 条**：只写不读，都是 fire 结果、`hd_hev_*`、`_skip`、`_att/_def`，以及本轮新增、待卒年行读取的 `hd_j16_mobo_li_result`。
9. 本期没有生成器需要重跑；第 2 条补表之后，除外。

## 五、实测项

**R-继统**：10 对非直系储君，首测在 HD_J16 日志里搜 `WAIT invalid_heir_<步>` 与 `SKIP actor_dead`：

| 步 | 君主 → 储君 | 关系 |
|---|---|---|
| ban_heir | 雄 `bacong_li_009` → 班 `bacong_li_013` | 侄 |
| pugen_heir | 猗卢 `tuoba_027` → 普根 `tuoba_032` | 侄 |
| yulv_heir | 普根 `tuoba_032` → 郁律 `tuoba_004` | 堂亲 |
| shefuchen_heir | 疾陆眷 `liaoxi_duan_005` → 涉复辰 `liaoxi_duan_004` | 叔父 |
| duanliao_heir | 末波 `liaoxi_duan_015` → 段辽 `liaoxi_duan_011` | 侄 |
| zhangmao_heir | 寔 `anding_zhang_005` → 茂 `anding_zhang_006` | 弟 |
| jun_heir | 茂 `anding_zhang_006` → 骏 `anding_zhang_007` | 侄 |
| heru_heir | 郁律 `tuoba_004` → 贺傉 `tuoba_029` | 侄 |
| hena_heir | 贺傉 `tuoba_029` → 纥那 `tuoba_028` | 弟 |
| shiyijian_heir | 翳槐 `tuoba_006` → 什翼犍 `tuoba_005` | 弟 |

其余 7 对是父子：轨→寔、务勿尘→疾陆眷、寿→势、骏→重华、廆→皝、吐谷浑→吐延、吐延→叶延。

**吐谷浑**：tuyan_heir 跨王朝，依赖亲子放宽与引擎认可；本步也依赖 3-C 开局立吐延为储君（走 already 分支）。

**不杀夺位**：
- 主头衔是否正确切换（`set_primary_title_to`）；
- 层级不低于新主的旧封臣留在无地旧主名下后是否自行独立、造成碎地；
- 末波夺位时，涉复辰若是晋臣的封臣，头衔归属是否正常。

**其他**：
- `create_alliance` 是否生效；
- 拓跋、慕容由 found_realm 改郡国制后的连锁影响；
- 三跳授郡之后猗卢能否独立（T2 依赖于此）；
- 慕容仁开局无地，M2 多半跳过；刘琨开局是冒险者，T2 结盟多半不成；
- yuwen344 战争的连通筛选能否命中宇文郡。

## 六、新增事件号与变量（合并更新）

**事件号**（15 个）：

| 段 | 事件号 |
|---|---|
| 成汉 C | `hd_j16.0450`–`0453` |
| 前凉 L | `0500` |
| 代 T | `0550`–`0554` |
| 辽东与吐谷浑 M | `0600`–`0604` |

**节点变量**：`hd_j16_<语义>_done/_result/_skip/_wlog`。语义名：lixiong_emperor、qu_hanzhong、zhangshi_heir、zongshe、daiguo（daigong、daiwang 各带 `_done/_result`）、liuxiu、duanbu、liqi、lishou、lishi_heir、zhangmao_heir、liangwang、daitong、murong_jicheng、murongren、yanwang、yuwen344、tuyuhun3。

**步骤变量**：
- **R-继统步**：pugen_heir、yulv_heir、jiluojuan_heir、shefuchen_heir、duanliao_heir、ban_heir、jun_heir、zhonghua_heir、heru_heir、hena_heir、shiyijian_heir、huang_heir、tuyan_heir、yeyan_heir，各带 `_done/_result/_skip/_wlog`。
  - 本轮新增 `hd_j16_<步>_ih_wlog`：invalid_heir 日志开关，带参数设置，闸门看不到。
- **其余步骤**：
  - mobo_li 带 `_done/_result/_skip/_wlog`，其中 `_result` 为本轮新设，兼作涉复辰 K 行的 PRE；
  - yihuai_li 带 `_done/_result/_skip/_wlog`；
  - 另有 liangwang_title_done、murongren_rebel_done、murongren_army_done。

**其他变量**：
- `hd_j16_zongshe_go/_asked`、`hd_j16_liuxiu_seen`；
- 战争 KIND yuwen344：`hd_j16_yuwen344_started/_won/_lost/_att/_def/_go/_asked/_wsf_wlog`，以及 `hd_nbc_yuwen344_active`。

**scope 名前缀**：`hd_j16_` 加以下后缀，其中 `zsh_`、`lxw_`、`qhz_` 是本轮改名后的：
`lxw_`、`qhz_`、`zsh_`、`dg_`、`db_`、`lq_`、`ls_`、`lw_`、`dt_`、`mj_`、`mr_`、`yw_`、`yw44_`、`ty_`、`rjt_`、`sz_`、`cl_`。

**02 编号式旧名 → 语义名**

| 02 原写 | 实际用名 |
|---|---|
| C1 | `hd_j16_lixiong_emperor_*`；3-D 卡读的 `_result` 只在选称帝时设 |
| C2 | `qu_hanzhong` |
| C3 | `liqi` |
| C4 | `lishou` |
| C5 | `lishi_heir` |
| L1 | `zhangshi_heir` |
| L2 | `zhangmao_heir` |
| L4 | `liangwang`；卡 `zgui_xizhou` 读主头衔 `hd_nbc_style = wang` |
| T1 | `zongshe` |
| T2 | `daiguo`、`daigong`、`daiwang` |
| T3 | `liuxiu` |
| T4 | `daitong` |
| M1 | `murong_jicheng` |
| M2 | `murongren` |
| M3 | `yanwang` |
| M6 | `yuwen344` |
| M7 | `duanbu` |
| M9 | `tuyuhun3` |

## 七、卒年表 PRE 变量的设置处

- 卒年表里与本路有关的 37 行，第 8 列 PRE 全空，本路不需要为现有行设 PRE。
- 本轮新增一个 PRE：`hd_j16_mobo_li_result`，只在 `hd_j16_mobo_li_effect` fire 时设（AI 末波直接执行，或玩家在 0600 选 a），供待补的涉复辰 K 行读取（第四节第 2 条）。
- 已 grep 暂存副本核对：这个变量只在该处设置；节点本身不再杀任何人。
- `gen_deaths.py` 读的是 mod，不读暂存：上轮它报的「PRE 无人设置」W 里没有本路的变量。涉复辰行补进卒年表后，它会以 PRE 为 `hd_j16_mobo_li_result` 出现，本路合并后这条 W 应当消失。