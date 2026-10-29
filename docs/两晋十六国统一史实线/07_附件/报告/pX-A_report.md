# pX-A 最终报告（修正后合并版）

## 审查意见处理结论

本轮审查意见已处理完：blocker 1 条、major 1 条已修；minor 3 条里 1 条改了代码，另 2 条只写进报告，理由见下。复跑闸门，结果和修前一样：相对基线新增 10 条 error，全是 gvar_read_never_set 误报；warn 0。改动全在暂存区，mod 没动，没跑生成器，没开游戏，没提交 git。

### 逐条处理

**1. blocker：yml 里 desc 跨行（已修）**
- hd_j16.0301.desc 和 hd_j16.0357.desc 在中英两份里都合成了一行，段落之间改写成转义的 `\n\n`。
- 改完后两份 yml 都是 234 行。我写了一个扫描脚本（scratchpad\fix_yml.py）核对：表头之后除空行和 # 注释外，全是单行「 key:N "…"」，没有别的行。
- 第 167、211 行确认是字面的反斜杠 n，不是真换行。BOM 保留，0 个 CR。
- 闸门的本地化检查拦不住跨行，这次的结论来自上面的脚本扫描，不是闸门。

**2. major：靳准拒之时的随机授郡可能抽到刘曜、石勒（已修）**
- 改动在 hd_j16_jinzhun_rebel_effect。授郡之前先解析下游当事人，存成 scope：
  - 刘曜 xiongnu_liu_041
  - 石勒 shangdang_shi_003
  - 石虎 shangdang_shi_010
  - 刘熙 liu_xi_2
  - 刘胤 xiongnu_liu_043
- 平阳那一支（看平阳郡持有者）和 random_vassal 那一支都加了 `NOT = { scope:x ?= this }`。这个写法有原版先例：coronation 里的 `NOT = { scope:coronation_anointment_authority ?= this }`。scope 没取到时 `?=` 为假，不会报错，也不会误排除。
- 两支都取不到人时照旧跳过，记 player_refused。这时 done 已设，并州仍归刘氏，E2-H20 等到关窗就跳过。
- 节点头注释的 D16 描述已同步。

**3. minor：靳准 318.12.15 卒年行导致拒之内战一律判负（不改代码）**
- 改法超出本轮范围（要把 _att 改指继承人）。
- 已写进「需要汇总人处理」，建议记入 07 已知局限，并在实测项里加了一条。

**4. minor：内战胜后只设 _result（不改代码，写进自拟与偏差）**
- 理由：b4 内战的 CB 目标是守方首府所在的郡。夺位者打赢只拿到这个郡，拿不到被宣称的王国头衔。
- 如果这时补调 hd_nbc_found_realm_effect，会把夺位者主头衔（一个郡）改名成「汉」或「赵」，并标上天王称谓。
- 石虎的情况更糟：会出现第二个「赵」，和玩家石弘手里的赵并存。
- 李城（e3_346 第 668 行）的写法也是只设 _result，这里保持一致，交汇总人确认。

**5. minor：res_yan 新加的昌黎分支顺序（已改代码）**
- d_changli 这一支挪到了广阳、魏郡两支之后，成为最后一支。函数上方注释同步补了「最后取昌黎郡的最高领主」。
- 304 局里慕容氏不持有广阳、魏郡，仍会落到昌黎这一支，Q2 的效果不变。
- 346、370 局：前三支能命中时行为不变；前三支都落空时，原先取不到燕主，现在会取到昌黎一系。

### 仍未解决
- 靳准死后（318.12.15）拒之内战一律判负。
- 内战胜后夺位者不定称谓、不改元。

两条都交汇总人。

### 闸门
- 复跑命令带 `--overlay pX-A --compare baseline.json --only-changed`，结果在 stage\pX-A_gate.txt。
- 相对基线新增 error 10 条，全是 gvar_read_never_set，涉及 hd_j16_jinzhun_ 和 hd_j16_shihu_fei_ 的 started、key、won、go、asked。原因是这些变量名由 `$KIND$` 拼出来，闸门认不出，属于误报。warn 0，已解决 0。
- 两份改动脚本的括号已核对平衡。
- 落盘前核对过：7 个文件的 base sha256 与 mod 现文件一致，没有被别的会话改过。

---

# pX-A（A 路）报告：R1、Q1、Q3、P1、Q2 的 k_pingzhou 部分（修订版）

## 一、暂存任务与文件清单

暂存任务名为 pX-A，共 7 个文件，全部是 edit：
- common/scripted_effects/zz_hd_j16_e2_346_effects.txt（R1）
- common/scripted_effects/zz_hd_j16_e2_304_effects.txt（Q1）
- events/zz_hd_j16_304_events.txt（Q1）
- localization/simp_chinese/zz_hd_j16_304_l_simp_chinese.yml（Q1）
- localization/english/zz_hd_j16_304_l_english.yml（Q1）
- common/scripted_effects/zz_hd_j16_startup_304_effects.txt（Q3）
- common/scripted_effects/zz_hd_j16_e3_346_effects.txt（P1、Q2）

格式核对：
- 原文件都是 UTF-8 带 BOM、LF；暂存副本 BOM 保留，0 个 CR。
- 括号平衡已脚本核对。
- 两份 yml 现在都是单行键值，段落之间用 `\n\n`。各 234 行，表头之后只有单行键值、空行和注释，已用脚本扫过。
- 冻结文件一处未动；346 的 yml 不需要改。

## 二、逐条做法与证据

### R1 伐蜀兜底（e2_346）

**存攻守方。** 改在 hd_j16_fashu_war_effect 里：random_character_war 内，`set_global_variable = hd_nbc_fashu_active` 之后加两行，把攻方、守方分别存进 global_var:hd_j16_fashu_att 和 hd_j16_fashu_def。只在找到这场战争时才存。

**新建 hd_j16_fashu_check_effect，分两段。**

① 兜底收尾。条件：active 已设、尚未 done、四种结局标记都没有。在此基础上要求以下各方都已不在 kind=fashu 的战争里：
- 开战时存的攻方、守方（att、def）；
- 经 hd_j16_resolve_effect 解析出的桓温、李势；
- title:k_uuii_yizhou.holder；
- 旧效果原有的 k_uuii_jingzhou.holder 和 e_bashu.holder。

满足时清掉 active，再看成都 c_uuii_p_4282 是否归天子一系，补设 hd_nbc_fashu_won 或 _lost。

② 了结。有任一结局标记而未 done 时，设 hd_nbc_fashu_done。
- 赢了（_won）就再解析一次桓温，在世才发 hd_nbc.0110，记 FIRE reward_sent；
- 取不到桓温记 SKIP no_actor；
- 没赢记 SKIP not_won。

**入口。** e2_346 入口改调 hd_j16_fashu_check_effect。冻结的 hd_nbc_check_fashu_effect 没动，全库只剩已停用的 hd_nbc_pulse_effect 还调它。

**R2 回归（346 开局原生人物）。** 不退化，理由：
- 新兜底认作「仍在打」的人，包含了旧效果的全部四个对象，判定只会更严，不会提前收尾。
- done 和结局标记沿用旧名，下游读到的变量不变。
- 370 及以后的开局，done 照样挡住这两段。

### Q1 夺位给玩家选项（e2_304、304 事件、304 本地化）

依据 00 A3-F13★A、01 §7.2-3/§7.3，照 E3-Z20 李城节点和事件 1011 改写。

**H10 靳准之乱、Z50 石虎废弘两个节点，分支顺序：**
1. done 守卫
2. prestart
3. `_started`：判结局，不受窗口限制；只在 _won 时设 _result
4. 窗口
5. actor_dead
6. 解析当事人
7. `_go`：开内战，调 hd_j16_b1_usurp_civil_war_effect
8. 原摆位兜底和主条件：AI 汉主设 done 后调执行体；玩家汉主调 hd_j16_b4_ask_effect 发事件。

**执行体。** hd_j16_jinzhun_effect 和 hd_j16_shihu_fei_effect 都从原 fire 段原样抽出，开头自带守卫，条件不成立记 SKIP no_actor_exec。

**0301、0357 的两个选项：**
- a 逊位：执行原 take_realm 等。只有当 root 恰是刘粲（xiongnu_liu_027）或石弘（shangdang_shi_005）本人时，才预设其卒年 done，让他以无地之身续命。
- b 拒之：调 hd_j16_b1_usurp_rebel_effect。夺位者独立，得 root 主头衔的宣称（存进 _claim），设 _go。
- 靳准无地时先授郡（D16）。平阳郡由汉主的 AI 封臣持有就授平阳；否则从汉主的 AI 直属郡级封臣里随机抽一人，授其主头衔郡。两支都排除刘曜、石勒、石虎、刘熙、刘胤；抽不到就跳过，记 player_refused。

**内战。** 守方是 _claim 头衔的现持有者，被夺者死后由继承人接着当守方。目标是守方首府所在的郡，经 4-B 的 hd_j16_b4_civil_war_go_effect 处理接壤。开战成功给夺位者事件兵：靳准 1 万，用新键 hd_j16_jinzhun_army_name；石虎 2 万。

**卒年 PRE 核对。** _result 只在三种情形下设：AI 执行、玩家选 a、夺位者打赢内战。玩家拒之而夺位者没赢时，PRE 不设，刘粲、石弘等按 D15 顺延。

**下游。**
- E2-H20：拒之后内战未了结时，H20 等到 319.3.2 关窗跳过；靳准打赢就照常触发。
- E2-Z60：不读本节点，不受影响。

**本地化。** 中英两份：0301、0357 的 desc 改写（已改成单行），a 选项改为逊位的意思，新增 b 选项和 hd_j16_jinzhun_army_name，中英键一一对应。节点里已不再直接 trigger_event 0301/0357。

### Q3 颖失邺对玩家（startup_304）

主 if 之前插一层：`scope:hd_j16_yl_ying ?= { is_ai = no }` 时只记 `HD_J16 startup_304 SKIP player_ruler`，原主体改成 else_if。

### P1 层级护栏（e3_346）

- **Z50：** 石祗改投的过滤改为 `highest_held_title_tier < scope:hd_j16_sze_zhi.highest_held_title_tier`。
- **Z60：** take_realm 之后比较刘显与魏主的层级，分三种情况：
  - 刘显低于魏主：照旧 swear_fealty，记 FIRE swear_wei。
  - 否则双方都独立有地、未结盟：照 4-C 刘群附魏的写法 create_alliance，记 FIRE ally_wei_tier_low。
  - 再不满足：只记 SKIP wei_tier_low_no_ally。
- 第二跳宣战时，hd_nbc_start_war_effect 会先断盟，所以结盟后仍能开战。

### Q2 之 k_pingzhou（e3_346）

- **E3-M10：** 加兜底。scope 没取到，且平州王国持有者不是独立的慕容氏时，取 title:d_changli.holder.top_liege，要求在世、独立、属 dynasty:murong、不在战中。
- **hd_j16_b4_res_yan_effect：** 加了 d_changli 一支，放在平州、广阳、魏郡三支之后作为最后一支，按审查意见调了顺序。
- 不转平州王国头衔。
- 346、370 局：前三支能命中时行为不变；前三支都落空时，原先取不到燕主，现在会取到昌黎一系。

## 三、自拟与偏差

1. **靳准拒之时授郡（D16）。**
   - 平阳郡由汉主的 AI 封臣持有就授平阳；否则从汉主的 AI 直属郡级封臣里随机抽一人，授其主头衔郡。
   - 两支都排除下游当事人：刘曜 041、石勒 003、石虎 010、刘熙 liu_xi_2、刘胤 xiongnu_liu_043。
   - 抽不到就跳过（player_refused）。原郡守会因此失地。
   - 某个 ID 取不到人时，对应的排除自然失效，没有害处。
2. **事件兵与新键。** 靳准 1 万、石虎 2 万是自拟数字。新键中文「靳氏禁兵」，英文 Jin Clan Guards。
3. **面板提前亮。** 内战开打时面板就亮，早于分出胜负，与李城相同。
4. **拒之后的内战只在窗口内开。** 一直开不成战就关窗跳过，夺位者保持独立并带着宣称，记 window_closed。
5. **逊位续命只限刘粲、石弘本人。** 被夺者是他们的继承人时，不预设卒年。
6. **Q3 给保底县高邑 c_uuii_p_4258 的持有者也加了 `is_ai = yes`。** 魏郡里玩家持有的下属县只改主君，不失地。
7. **工具依赖。** e2_304 用到了 e3_346 里的 4-B 工具，运行时是全局效果，没有问题。
8. **Z60 结盟对象可能是玩家。** 魏主是玩家时，结盟对象就是玩家，与 4-C 刘群先例相同。
9. **R1 新日志前缀用 e2_j91。**
10. **（新增）夺位者打赢内战后只设 _result。** 不调执行体，所以不 take_realm、不定称谓、不改元、不迁邺。
    - 理由：CB 只把目标郡给胜方，拿不到王国。在郡级主头衔上调 found_realm，会把郡改名成「汉」或「赵」并标天王，石虎还会造出第二个「赵」。
    - 李城节点的写法也是如此。交汇总人确认。

## 四、需要汇总人处理

1. **玩家颖保留邺。** 玩家颖局里，B 段链条会回到沉睡、等截止的状态，建议记入 07 已知局限。
2. **设计文字待改。** 02 的 H3、Z12「只能认」已被 A3-F13 推翻，需要改 02 或在 07 记一笔；p3-B1 报告里对应的偏差随之作废。
3. **旧档无法补救。** 已经被 R1 误判的 304 旧档补不回来。
4. **旧档里挂着的旧 0301/0357 是安全的。** 那些档里 done 已设，点 a 或 b 都只记 player_late_reply。
5. **闸门 10 条 gvar_read_never_set 都是 `$KIND$` 拼名造成的误报。**
6. **（新增）建议记入 07 已知局限：** 靳准按卒年表在 318.12.15 被靳康所杀，之后拒之内战一律判负。原因是结局只认 _att（靳准本人）是否持有关键县，即使其继承人随后拿下也判 _lost。PRE 不会被误设，H20 关窗跳过。
7. **（新增）内战胜后只设 _result 这一取舍，请确认**（第三节第 10 条）。

## 五、实测项（game.log 搜 HD_J16）

**R1（304 开局一路跑到伐蜀）：**
- `e2_j90 FIRE war_started`；
- 战后出现 `e2_j91 FIRE fallback_won` 或 `fallback_lost`（也可能由 CB 正常给出结局）；
- 接着 `e2_j91 FIRE reward_sent`，或 `SKIP no_actor`、`SKIP not_won`；
- 开战当跳不应出现 fallback。

**R2 回归（346 开局）：** 同上，0110 照常发出。

**Q1（玩家刘粲或石弘）：**
- e2_h10 / e2_z50 下依次可能出现：`WAIT player_asked`、`FIRE player_abdicated`、`WAIT player_refused_civil_war`、`FIRE rebel_granted_duchy`、`FIRE war_started`、`FIRE civil_war_border_target`、`WAIT rebel_not_ready`、`WAIT war_start_failed`、`FIRE result_won`、`FIRE result_lost`、`FIRE jinzhun_civil_war_won`、`FIRE shihu_fei_civil_war_won`、`SKIP no_actor_exec`、`SKIP player_late_reply`；
- 逊位后应出现 `death_xiongnu_liu_027 SKIP spared_by_player`（石弘为 `death_shangdang_shi_005`）；
- 拒之后应出现 `e2_h20 SKIP window_closed`，或靳准打赢后 H20 FIRE。
- （新增）出现 `FIRE rebel_granted_duchy` 时，核对授出的郡不是刘曜、石勒等人的。
- （新增）拒之内战跨过 318.12.15 时，看 `e2_h10 FIRE result_lost` 出现的时点。
- （新增）事件 0301、0357 的说明文字应完整显示两段。

**Q3（选颖开局）：** `startup_304 SKIP player_ruler`，邺仍归颖。

**P1：**
- `e3_z60 FIRE ally_wei_tier_low`、`FIRE swear_wei`、`SKIP wei_tier_low_no_ally`；
- error.log 里不应再有同级改投的报错。

**Q2（304 局约 350 年）：** E3-M10 能取到慕容皝一系，出现 `FIRE war_started` 或 `player_event_sent`，不应一直 `WAIT not_ready`。

**error.log 里要留意的写法：**
- `scope:x ?= root`、`scope:x ?= this`
- `capital_county.duchy ?= {}`
- `global_var:hd_j16_<KIND>_claim.holder ?= {}`
- `set_global_variable value = root.primary_title`
- create_alliance
- random_vassal 里的 `primary_title = { tier = tier_duchy }`