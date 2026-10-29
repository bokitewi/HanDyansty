# p5-A2 最终报告（修正后合并版）

# p5-A2 修正报告：东晋 371–403 节点（审查意见逐条处理）

暂存任务名 **p5-A2**。本次只改了暂存区，没有直接写 mod，没有跑生成器，没有开游戏，没有提交 git。
- 本次改了 3 个已登记文件：`zz_hd_j16_370b_effects.txt`、`zz_hd_j16_370b_triggers.txt`、`zz_hd_j16_e5_370_effects.txt`。
- 事件、本地化、修正、好感文件本次没动。
- 8 个文件花括号都配平，都是 UTF-8 带 BOM、LF。

## 一、逐条处理结果

### 1. major：刘牢之是议员时 J97 搬不动，J20 断链 —— 已修
两种修法都做了，以放宽 E5-J20 为主。

**E4-J97 改用新触发器**
- 新触发器 `hd_j16_370b_can_employ_council_trigger`，配套效果 `hd_j16_370b_employ_council_effect`。
- 不再排除议会成员，改判 `is_ruler = no`。原因：天朝制议员多半持有 `e_minister_*`，这是无地型头衔，`is_landed` 拦不住；而持头衔就算统治者，`set_employer` 会失败（报错清单第 29 条）。
- E4-J60 仍用原触发器，排除议员是 04 的要求。
- 原触发器注释已改准：第 29 条原文只列了统治者和已在该宫廷两种失败情况，排除议员是设计要求。

**E5-J20 开战条件放宽**
- 开战时刘牢之那条改为「在世、且在晋天子政权内」。

**E5-J20 倒戈引信同步放宽**
- 判定条件：刘牢之在世、未被囚、在晋，且不是王恭本人。
- AI 刘牢之：不论归属都倒戈。
- 玩家刘牢之：只有属王恭一系（新触发器 `hd_j16_370b_liu_under_gong_trigger`）时才弹 5021；否则记 `_nodefect`。

**`defect_effect` 只在他属王恭一系时动归属**
- 封臣改投天子；廷臣改入天子宫廷（用不排除议员的新触发器）。
- 他若仍在谢玄或桓氏名下，归属不动。
- 「反覆」修正、王恭对他 −100、`end_war = defender`、`jk_pending` 照做。

### 2. minor：王坦之有地时不授中书令 —— 已修
- 去掉了 `is_landed = no` 的限制，有地无地都授。
- 有地者走第 6 条的有地分支。

### 3. minor：注释写「下一跳」与实际不符 —— 已修
- **E4-J40**：只改注释，入口、节点头、效果内三处都改了。改后的说法：AI 路径同一跳内先授官、后授郡；玩家经 4540 a 执行时，授郡在下一跳。
- **E5-J20**：改为真的隔一跳。倒戈时设 1 天计时 `hd_j16_wanggong2_jk_wait`，计时消失后才授毗陵，让清君侧 CB on_defeat 的囚禁、收地先跑完。注释同步改了。

### 4. minor：广陵空缺时 J60 不授郡 —— 不实现，列为自拟收窄
- 理由：空缺的郡头衔下没有随授的县，谢玄会持郡却没有 `capital_county`。
- 而 J80 的事件兵（`hd_j16_370b_army_effect`）和北伐开战都要 `capital_county`，做了反而把链条弄断。
- 现在的行为：空缺时等到窗口关闭跳过。理由已写进 J60 节点注释。

### 5. minor：4511 b 欲诛王谢收窄 —— 已补齐
- **开放篡位条件**：去掉桓温的 `hd_court_regent_tenure` 旗标（370 开局挂了 12 年，zz_hd_370_startup_effects.txt 第 262–264 行）。之后「废为礼仪君主」决议即可用，但仍需和平、威望等级 3、500 威望，不强制。
- **晋廷世族好感 −30**：
  - 谢安、王坦之、天子照旧各加一次；
  - 另对天子的 `every_courtier` 与 `every_vassal` 中的世族加一次。世族用 `hd_party_is_shizu_trigger` 判定，新触发器为 `hd_j16_370b_shaxin_shizu_trigger`；
  - 排除桓温本人、龙亢桓氏、谢安、王坦之，避免重复加好感；
  - 不铺全国（不用 `every_vassal_or_below`）。

### 6. minor：有地者授朝官走 granted、不占议会席位 —— 已修，另列实测
- 没有改照 nbc 先例调 `got_minister_position_effect`。原因：它第 153–179 行会把没有 WJ_rf 实封的人手下的封臣全部转给天子，道子若有下属会被拆掉。
- 有地分支改为三步：
  1. 仍用 granted 转头衔；
  2. 照 WJ 第 110–137 行补朝官继承法（大司马用 grand_marshal 那一版）；
  3. 只在他是天子的直属封臣或廷臣、且尚无该席位时，由天子 `assign_councillor_type` 占席（`remove_existing_councillor = yes`）。不满足时只持头衔。

## 二、仍未解决项
- 广陵空缺一支：按第 4 条理由刻意不做。
- 以下均需实测（见第九节）：新触发器下 `set_employer` 搬议员是否成功、有地朝官的席位与头衔能否保留、J20 授郡与 on_defeat 的先后、去掉旗标后礼仪君主决议能否出现。

## 三、闸门结果
结果文件：D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p5-A2_gate.txt

- 复跑后 error 3，warn 72，相对基线消掉 2 条，与修正前一致。新增的计时变量和触发器没有带来新告警。
- 3 条 error 仍是参数拼名造成的误报：
  - `hd_nbc_xiebeifa_active`、`hd_nbc_huanxuan_jing_active` 由 `hd_nbc_start_war_effect` 以 `hd_nbc_$KIND$_active` 设置；
  - `hd_hi_started_sunen` 由 `hd_hi_begin_effect` 以 `hd_hi_started_$KEY$` 设置。
- 72 条 warn 都是只写不读：fire 结果、`_skip`、`hd_hev_*`、`_att/_key` 等。
- 没有未定义引用，也没有缺失的本地化键。

## 四、文件清单（共 8 个）
**edit**
- `common/scripted_effects/zz_hd_j16_e5_370_effects.txt`：E5-J10～J42，入口名不变。

**new**
- `common/scripted_effects/zz_hd_j16_370b_effects.txt`
  - 入口 `hd_j16_e4_370b_effect`，放 E4 段 12 个节点；
  - 共用小工具：`hd_j16_370b_res/grant_duchy/office/employ/employ_council/army/news_effect`；
  - 5-A1 已在其暂存的 `hd_j16_e4_370_effect` 第 29 行加了调用。
- `common/scripted_triggers/zz_hd_j16_370b_triggers.txt`
- `common/modifiers/zz_hd_j16_370b_modifiers.txt`（7 个）
- `common/opinion_modifiers/zz_hd_j16_370b_opinion_modifiers.txt`（9 个）
- `events/zz_hd_j16_370b_events.txt`（`namespace = hd_j16`）
- 中英 yml 各 131 键，一一对应。

## 五、节点要点

**E4 段**
| 节点 | 名称 | 要点 |
|---|---|---|
| J15 | 简文崩·孝武立 | 软指定储君 |
| J20 | 新亭之会 | a 选项检定成功设 `hd_j16_xinting_calm`；4511 b 见第一节第 5 条 |
| J25 | 求九锡·拖延 | |
| J30 | 桓温卒·遗命 | 节点侧 |
| J40 | 谢王秉政·桓冲解扬州 | 删 `hd_j16_handoff_block` 兜底；谢安授尚书令，王坦之授中书令；随后广陵授王坦之 |
| J50 | 孝武亲政 | |
| J60 | 北府兵 | 广陵授谢玄，「北府兵」修正；刘牢之、何谦入谢玄宫廷（排除议员） |
| J80 | 谢玄北伐 | KIND=xiebeifa，设 `hd_j16_xiebeifa_won` |
| J90 | 谢安出镇广陵 | 广陵郡治 |
| J95 | 道子专政 | 只授朝官 |
| J97 | 王恭出镇京口 | 毗陵授王恭；刘牢之入王恭宫廷（不排除议员） |

谢安、王坦之、道子按 G4 只授朝官，不装 hd_court 权臣。

**E5 段**
| 节点 | 名称 | 要点 |
|---|---|---|
| J10 | 安帝立 | |
| J15 | 王恭初举 | |
| J20 | 王恭再举 | 清君侧；45 天倒戈引信；隔 1 天后毗陵授刘牢之；之后软授寻阳郡给桓玄 |
| J22 | 孙恩·节点侧 | 读 `hd_hi_started_sunen`，不重复起兵 |
| J25 | 桓玄据荆江 | KIND=huanxuan_jing；开不成战时走围城兜底 |
| J30 | 桓玄入建康 | 清君侧；刘牢之倒戈时 `end_war = attacker`；胜后装 hd_court 权臣 |
| J40 | 篡楚 | 经 5043 篡位，国号楚，改元永始 |
| J42 | 刘裕据京口 | |

404 线接口：J40 给出「桓玄持 h_china」，J42 给出「刘裕有地且 top_liege 是桓玄」，已与 e5_395 现行 E5-J50 的条件对过。06 §2.2 的 J45、J50 及以后不做。

## 六、自拟与偏差（合并更新）
1. **清君侧取代 KIND。** 王恭两举、桓玄入建康改用清君侧 CB（`hd_dc_kit_ten_start_qingjunce_effect`，照王敦 E2-J20 的先例），不用 KIND=wanggong/huanxuan。胜负判定看攻方是否持终身辅政（`hd_dc_ten_qjc_regent`）或是 hd_court 权臣，战争结束后隔一跳再判。
2. **倒戈时间。** 固定取 45 天，用全局计时变量。
3. **【本次】J20 刘牢之条件放宽。**
   - 开战只要求刘牢之在世、在晋，不再要求他已在王恭一系。
   - 倒戈：AI 不论归属都倒戈；玩家只有属王恭一系时才问，否则记 `_nodefect`。
   - 归属只在他属王恭一系时才改。
4. **【本次】J97 召刘牢之不排除议员**，改判 `is_ruler = no`（04 只写「AI 且无郡」）。J60 仍排除议员。
5. **【本次】J20 倒戈后隔 1 天再授毗陵**，计时变量 `hd_j16_wanggong2_jk_wait`。
6. **【本次】J60 广陵空缺一支收窄不做。** 空郡没有县，谢玄会没有 `capital_county`，J80 的事件兵和开战都会断。
7. **【本次】4511 b 的处理。**
   - 「关押、谋杀便利」用修正「杀心」（谋略 +2，2 年）近似，没有改交互。
   - 世族好感只覆盖天子的廷臣与直属封臣，另加谢安、王坦之、天子。
   - 篡位条件以去掉 `hd_court_regent_tenure` 旗标开放。
8. **【本次】有地者授朝官：** granted 转头衔 + 补继承法 + 资格内占议会席位，不调 `got_minister_position_effect`。
9. **J30 主体改为桓玄**，传檄讨元显；加事件 5032；「持荆州或江州王国级头衔」放宽为「持郡」。
10. **J25 放宽与兜底。** 「殷仲堪持荆州 / 杨佺期持雍州」放宽为「有地、在晋、与桓玄不是上下级」；第一次开战失败就走「被围自尽」兜底，按胜论。
11. **改投天子。** J30 中桓玄不是直属、而其主君是 AI 时，先改投天子；J20 不改投。
12. **储君。** J15、J10 只给 AI 天子 `set_designated_heir`。
13. **九锡。** 只设人物变量 `hd_j16_jiuxi`，加修正「九锡」，不建头衔。
14. **广陵来源放宽**为任何同一政权的 AI 持有者。
15. **其他自拟。**
    - 新亭检定：权重 20 加外交加谋略，对 30（失败）。
    - 4560、4561 双玩家连环（谢安荐，天子准）。
    - 北府兵只给修正，不给兵团。
    - 桓熙「流徙」只做修正。
16. **PRE 设置时机。** 本节 PRE 只在史实结果出现时设，不在开战时设（见第八节）。

## 七、面板行清单（交 F-1，只列不写）
| 变量 | 内容 | 组与范围 |
|---|---|---|
| `hd_hev_j16_huanwen_dead` | 桓温卒（04 §1.5 第 09 行） | le370 |
| `hd_hev_j16_beifu` | 北府兵（第 10 行） | le370 |
| `hd_hev_j16_wanggong1` / `hd_hev_j16_wanggong2` | 王恭两次举兵，建议并成一行、读任一 | `hd_hev_grp_j16_e5j`，le370 |
| `hd_hev_j16_huanxuan` | 桓玄入建康 | 同上 |
| `hd_hev_j16_cuanchu` | 桓玄篡楚 | 同上 |

- 孙恩行 `hd_hev_j16_sunen` 由 p5-C 设置，不归本路。
- 以下只设变量、不建议建行（都带 `hd_hev_j16_` 前缀）：`xiaowu_li`、`xinting`、`jiuxi`、`xiewang`、`qinzheng`、`xiebeifa`、`xiean_chuzhen`、`daozi`、`wanggong_jingkou`、`andi`、`huanxuan_jing`、`liuyu_jingkou`。

## 八、卒年表 PRE 的设置位置
tsv 的名字与本路一致，**不需要改 tsv**。杨佺期一行已是 `hd_j16_huanxuan_jing_result`，任务说明里的 `_done` 已过时。

| PRE | 对应人物 | 设置位置 |
|---|---|---|
| `hd_j16_wanggong1_result` | 王国宝 | 史实支 `hd_j16_wanggong1_effect`（AI 默认、5010 a、5011 a）；进兵后王恭获胜时，在 `hd_j16_wanggong1_judge_effect` 补设 |
| `hd_j16_wanggong2_result` | 王恭 | 王恭战败时，在 `hd_j16_wanggong2_judge_effect` 设；选「不举」或王恭获胜时不设 |
| `hd_j16_huanxuan_jing_result` | 殷仲堪、杨佺期 | 桓玄获胜时在 `hd_j16_huanxuan_jing_judge_effect` 设；围城兜底支也设 |
| `hd_j16_huanxuan_won` | 元显、道子 | J30 获胜时在 `hd_j16_huanxuan_judge_effect` 设；和平秉政支不设 |

本节没有在节点内直接处死任何人。

## 九、新增事件号与变量

**事件**
- E4 段：4500、4501、4510、4511、4520、4521、4530、4540、4541、4550、4560、4561、4580、4590、4595。
- E5 段：5000、5010、5011、5012、5020、5021、5022、5025、5026、5030、5031、5032、5033、5034、5040、5041、5043（隐藏）。

**新 KIND**：`xiebeifa`、`huanxuan_jing`。

**旧名 → 语义名**
| 04 写法 | 本路实施 |
|---|---|
| `hd_j16_wanggong_jingkou` | `hd_j16_wanggong_jingkou_result` |
| `hd_j16_huanxuan_usurp_done` | 节点用 `hd_j16_cuanchu_done/_result`；旧名在 fire 时照设，作兼容别名 |
| E5-J30（04 未命名） | `hd_j16_huanxuan_*` |
| E5-J42（04 未命名） | `hd_j16_liuyu_jingkou_*` |
| `hd_j16_xinting_done`、`hd_j16_huanwen_dead_done`、`hd_j16_beifu_done`、`hd_j16_xiebeifa_done`、`hd_j16_daozi_done`、`hd_j16_andi_done`、`hd_j16_wanggong1/2_done`、`hd_j16_huanxuan_jing_done` | 沿用原名 |

**其他变量**
- 全局：`hd_j16_xiaowu_heir_set`、`hd_j16_xinting_early`、`hd_j16_jiuxi_granted`、`hd_j16_huanwen_dead_open`、`hd_j16_xiewang_gl_pending`、`hd_j16_beifu_refused`、`hd_j16_andi_heir_set`、`hd_j16_xunyang_checked`、`hd_j16_huanxuan_peace`、`hd_j16_huanxuan_regent_set`、`hd_j16_huanxuan_regent_cd`，以及本次新增的 `hd_j16_wanggong2_jk_wait`。
- 各节点另有 `_fuse`、`_defected`、`_defect_asked`、`_nodefect`、`_over`、`_ended`、`_jk_pending`、`_asked`、`_go`、`_wsf_wlog`。
- 人物变量：`hd_j16_jiuxi`、`hd_j16_xiean_chuzhen`。
- 本次新增触发器：`hd_j16_370b_can_employ_council_trigger`、`hd_j16_370b_liu_under_gong_trigger`、`hd_j16_370b_shaxin_shizu_trigger`。
- 本次新增效果：`hd_j16_370b_employ_council_effect`。

**接口变量已设齐**：`hd_j16_xinting_calm`（E4-J20）、`hd_j16_xiebeifa_won`（E4-J80）。

## 十、需汇总人处理
1. **3-D 写入者**：`hd_asp_jiuxi_or_peer_trigger` 加一支 `has_variable = hd_j16_jiuxi`。
2. **6-A**：E5-J45 ①「桓玄从未篡位」应读「`hd_j16_cuanchu_done` 已设而 `hd_j16_cuanchu_result` 未设」；读兼容别名 `hd_j16_huanxuan_usurp_done` 也等价。
3. **5-A1**：入口调用已在其暂存中，同批落盘即可。
4. **p5-C 的 sunen**：本路只读不改。
5. 本任务不需要重跑生成器，也不需要改 tsv。

## 十一、实测项
- 清君侧战争：
  - 脚本 `start_war` 能否用清君侧 CB 开战；
  - `end_war` 是否会跑 CB 的 on_victory / on_defeat；
  - 盟友 `add_attacker` 能否加入打天子的一方。
- J25 封臣对封臣经 wct 能否开战。
- 篡位：
  - 隐藏事件 5043 能否正常篡位；
  - 篡位后 h_china 上残留的 `hd_dc_ten_qjc_regent` 是否干扰。
- J30 的一年计时与 J40 窗口（403.9–404.3）很近，晚胜的局可能来不及篡位。
- J97 王恭授郡后是否成为天子的直属封臣。
- 【本次新增】
  - 刘牢之若是议员，J97 的 `set_employer` 能否搬动（他原议席是否自动出缺）；
  - 有地的道子、王坦之授官后头衔与席位能否保留，`assign_councillor_type` 对直属封臣是否生效；
  - J20 倒戈后隔 1 天授毗陵与 CB on_defeat 收地的先后；
  - 4511 b 去掉旗标后，玩家桓温能否看到「废为礼仪君主」决议。