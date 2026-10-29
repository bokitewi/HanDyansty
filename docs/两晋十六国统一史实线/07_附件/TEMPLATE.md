# j16 节点模板说明（p1-S 垂直切片产出，后续各期照抄）

依据：01_架构.md §2.2、§4、§6，08_实施约定.md §2–§6。样板文件（暂存区 p1-S）：
- 新节点完整样板：`common/scripted_effects/zz_hd_j16_e2_304_effects.txt`（E2-J10 司马睿称晋王）＋ `events/zz_hd_j16_304_events.txt` 的 hd_j16.0200
- 迁入的战争节点样板：`zz_hd_j16_e1_304_effects.txt`（E1-H10 大陵，含玩家 a/b、暂缓、旧档补存）、`zz_hd_j16_e3_370_effects.txt`（E3-Q60 洛阳，按位置解析）
- 卒年机制：`zz_hd_j16_death_core_effects.txt`；数据样例：`zz_hd_j16_deaths_effects.txt`

---

## 1. 节点骨架

```
# 入口：每个「时代×节」文件只有一个入口，里面一行一个节点
hd_j16_e2_304_effect = {
	hd_j16_node_<语义>_effect = yes     # E2-J10 中文名
}

############################################################
# E2-J10 名称【软/严】（出处：02 §2.1 J3a）
# 窗口 起 – 止；条件；当事人（ID / 按位置）；AI / 玩家；软摆位；变量清单
############################################################
hd_j16_node_<语义>_effect = {
	if = {
		limit = { NOT = { has_global_variable = hd_j16_<语义>_done } }
		# ① 自保护（只用于新节点；迁入的旧节点改登记到 hd_j16_mark_before_start_effect；四场 D9 开局战两样都不加）
		if = {
			limit = { global_var:hd_j16_start_year >= 346 }     # 开局晚于史实日期的那些开局
			set_global_variable = hd_j16_<语义>_done             # 只设 done，不设结果、不设 hd_hev_*
			debug_log = "HD_J16 e2_j10 SKIP prestart"
		}
		else_if = {
			limit = { current_date >= <窗口起> }
			# ② 截止跳过（止日用「>= 止日次日」写）
			if = {
				limit = { current_date >= <窗口止> }
				set_global_variable = hd_j16_<语义>_done
				set_global_variable = hd_j16_<语义>_skip
				debug_log = "HD_J16 e2_j10 SKIP window_closed"
			}
			# ③ 当事人已死：立即跳过（判断已死只用 hd_j16_dead_trigger）
			else_if = {
				limit = { hd_j16_dead_trigger = { ID = <ID> } }
				set_global_variable = hd_j16_<语义>_done
				set_global_variable = hd_j16_<语义>_skip
				debug_log = "HD_J16 e2_j10 SKIP actor_dead"
			}
			else = {
				# ④ 解析（先清 scope，再解析；见 §2）
				# ⑤ 条件：上游（读 done，必要时读 fire 结果）+ 局面 + 当事人
				if = {
					limit = { <上游> <局面> scope:<当事人> ?= { ... } }
					set_global_variable = hd_j16_<语义>_done
					scope:<当事人> = {
						if = { limit = { is_ai = yes } hd_j16_<语义>_effect = yes }   # AI：直接执行史实项
						else = { trigger_event = hd_j16.NNNN }                       # 玩家：a 史实 / b 拒绝
					}
				}
				# ⑥ 其余情况：等待，不写 done；等待日志只记一次
				else_if = {
					limit = { NOT = { has_global_variable = hd_j16_<语义>_wlog } }
					set_global_variable = hd_j16_<语义>_wlog
					debug_log = "HD_J16 e2_j10 WAIT not_ready"
				}
			}
		}
	}
}

# 执行体：AI 由节点直接调，玩家在事件选项 a 里调（选项里先 save_scope_as 当事人）
hd_j16_<语义>_effect = {
	set_global_variable = hd_j16_<语义>_result      # fire 结果：卒年表「前置节点」、下游节点读它
	set_global_variable = hd_hev_j16_<语义>          # 面板行（只在 fire 时设；行本身由 F-1 写）
	...软摆位...
	debug_log = "HD_J16 e2_j10 FIRE <语义>"
}
```

战争节点的差别（照 E1-H10 / E2-J90 / E3-Q60 / E5-J50）：
- 宣战用 `hd_nbc_start_war_effect = { ATTACKER DEFENDER TARGET KIND }`（经连通筛选、在 D24 豁免内）；成功判据 `exists = scope:hd_nbc_war_<KIND>`。
- **开战成功才**设 `_started`、存攻守方（`set_global_variable = { name = hd_j16_<语义>_att value = scope:x }`）、生成事件兵；失败不设 done，记一次 `WAIT war_start_failed`，下一跳重试。
- 结局：`_started` 后每跳查「攻守双方都已没有 `var:hd_nbc_war_kind ?= flag:<KIND>` 的战争」，再按关键县归属判 `_won/_lost`，设 done；并清掉 `hd_nbc_<KIND>_active`。新 KIND 一律自判，不进 `hd_nbc_war_result_effect`。
- 玩家攻方要选项时：节点发事件前设 `_asked`（days = 60）防重复弹窗；选项 a 设 `_go` 并当场开战，b 设 `_wait`（days = 90）。
- 旧档兼容：旧开局效果已打响的战争只有 `hd_nbc_<KIND>_active`（或旧 started 变量），节点要先认它、补存攻守方，不能再开第二场。

## 2. 解析写法

```
# 按 ID（当事人必须是这个人时）
if = { limit = { exists = scope:hd_j16_xx_a } clear_saved_scope = hd_j16_xx_a }
hd_j16_resolve_effect = { ID = si_ma_rui AS = hd_j16_xx_a }
scope:hd_j16_xx_a ?= { ... }                     # 取不到时不报错

# 按位置（「秦主」「燕主」「天子」）
title:c_uuii_p_867.holder.top_liege ?= {
	if = { limit = { is_independent_ruler = yes dynasty ?= dynasty:fu_1 } save_scope_as = hd_j16_xx_qin }
}
```
- 宏参数名一律写 `ID`（卒年还有 `KILLER`，指凶手 ID；死亡核心内部的 yes/no 开关叫 `HAS_KILLER`，不是人物），生成器正则据此给 hbirth 人物写指针。
- scope 名前缀 `hd_j16_<节点缩写>_`，全线不重名；同一跳里存过的 scope 会一直留着，所以解析前必须先 `clear_saved_scope`。
- 在世判断：`hd_j16_alive_trigger = { ID }`；已死判断：`hd_j16_dead_trigger = { ID }`（没出场的人既不算活也不算死）。
- 王朝、家族一律用 `dynasty ?= dynasty:<键>`、`house ?= house:<键>`（慕容一律 `dynasty:murong`，R6）。

## 3. 卒年调用写法（只写进 zz_hd_j16_deaths_effects.txt，第 2 期起由生成器写）

```
hd_j16_death_effect = { ID = si_ma_zhong DATE = 307.1.8 DATE10 = 317.1.8 }                                   # N
hd_j16_death_kill_effect = { ID = taiyuan_wang_005 DATE = 314.4.1 DATE10 = 324.4.1 REASON = death_execution KILLER = shangdang_shi_003 }   # K
hd_j16_death_kill_pre_effect = { ID = ... DATE = ... DATE10 = ... REASON = ... KILLER = ... PRE = hd_j16_<语义>_result }  # K + 前置节点 fire 结果
hd_j16_death_die_effect = { ID = ... DATE = ... DATE10 = ... REASON = death_suicide }                         # 史实无凶手（自缢、投水、部众所杀）
hd_j16_death_die_pre_effect = { ID = ... DATE = ... DATE10 = ... REASON = ... PRE = ... }
if = { limit = { global_var:hd_j16_start_year = 370 } hd_370_yuanzhen_death_effect = yes }                    # X：调用各自的独立效果（D11）；袁真第 5 期前只在 370 局
```
- `DATE10` = 史料日期加 10 年（生成器算好写入，N 类也必须带）：K 类前提不成立顺延到 DATE10 后转 N；取不到人且已过 DATE10 当即设 done。
- 外层按十年分段：`OR = { AND = { current_date >= 段起 current_date < 段止+11年 } NOT = { has_global_variable = hd_j16_dNNN_swept } }`，段内首行 `set_global_variable = hd_j16_dNNN_swept`。
- done 变量 `hd_nbc_death_<ID>_done`；死因键以原版 `common/deathreasons` 为准：`death_natural_causes`、`death_murder`、`death_murder_known`、`death_execution`、`death_battle`、`death_suicide`、`death_drowned`。大限事件只认这几个，用别的键要先扩 `hd_j16_doom_die_effect`。
- 玩家：N 弹 hd_nbc.0100，K 弹 hd_j16.0001；强撑共用 `hd_j16_endured`，每人一次。

## 4. 日志写法

`debug_log = "HD_J16 <节点号> FIRE|WAIT|SKIP <原因>"`
- 节点号小写下划线：`e2_j10`；卒年 `death_<ID>`；导演 `dir_s<N>`；启动 `boot`。
- 原因：`prestart`、`window_closed`、`actor_dead`、`no_actor`、`not_ready`、`player_asked`、`player_refused`、`player_deferred`、`war_started`、`war_start_failed`、`result_won`/`result_lost`、`oldsave_*`、`missing`、`d15_defer`、`d15_to_N`、`player_no_reply`（玩家没点事件、窗口已过）、`player_late_reply`（玩家在节点截止后才点）。
- 第 1 期定稿要点：节点自保护比较 `global_var:hd_j16_start_year`；按位置解析的执行体开头自己重新解析（事件里也能用）；玩家事件期限变量选项内清除；宣战成功才给事件兵；新 KIND 按关键县自判、结局时清 `_active`。
- WAIT 只在首次进入等待时记一次（`hd_j16_<语义>_wlog`）；FIRE、SKIP 各记一次。

## 5. 常见坑

1. **自保护**只比较 `global_var:hd_j16_start_year`（值 304/346/370/404），不写 `game_start_date > X`。窗口跨某开局日的新节点，按「开局年 ≥ 下一个开局」判。
2. 迁入的旧节点**不加**自保护，在 `hd_j16_mark_before_start_effect` 登记 done/started/checked；**不设**结果变量和 `hd_hev_*`。四场 D9 战争（大陵、伐蜀、洛阳、京口）在自己的开局里不标。
3. 前标与自保护只设 done，下游判上游只读 done；确需结果的写「结果成立，或开局晚于上游」。
4. 跨开局的当事人：开局时未出生的人要靠 hbirth 指针，`character:ID` 取不到；所以一律经 `hd_j16_resolve_effect`。旧工具效果（`hd_nbc_add_attacker_effect`、`hd_370_*`）仍写 `character:$WHO$`，新节点不要再调它们取人，自己解析后传 scope。
5. 对已死角色不加减 flag/变量（报错清单第 28 条）；死亡前先 `set_global_variable` done，再 `death`。
6. 取不到人的地方一律 `?=`；global_var 里存的人可能已死，`global_var:x ?= { any_character_war = ... }` 对死人为假，正好用于「战争已结束」。
7. 不用 `every_living_character`；不在时代段外做 `any_neighboring_*`、`realm_size`。
8. `tier = tier_county` 写在 limit/AND/OR 里；`title_tier = county` 只能直接写在 any/every_held_title 里（清单第 26 条）。
9. `save_scope_value_as` 只收数值，旗标要比较就直接 `var:x ?= flag:y`（清单第 24 条）。
10. 本节触发器写进 `zz_hd_j16_<节>_triggers.txt`（由该节的链上任务首建）；不要在效果文件里引用还不存在的触发器——一次性的条件直接内联在 limit 里。
11. 新事件文件开头都要写 `namespace = hd_j16`；号段只用本节的（08 §2）。
12. 宣战是 `start_war`（独立战争）时，成功判据改为 `any_character_war = { primary_attacker = <人> using_cb = <cb> }`。
13. 新建 txt/yml：UTF-8 带 BOM、LF；yml 首行 `l_simp_chinese:` / `l_english:`，键 `hd_j16.NNNN.t/.desc/.a/.b`，中英一一对应。
14. 闸门 `gvar_read_never_set` 会把 `hd_nbc_<KIND>_active`（由 `hd_nbc_start_war_effect` 以 `hd_nbc_$KIND$_active` 设置）误报为只读不写，属误报，在报告里说明即可。
15. **卒年前置变量（第 2 期末汇总人定，10-27）**：`docs/两晋十六国_卒年表.tsv` 的 PRE 列是节点 **fire** 的结果变量，名字以 tsv 为准（原 06 设计名 `hd_j16_<x>_done` 的 21 个已改为 `hd_j16_<x>_result`；其余如 `*_result`、`*_won`、`*_started`、`hd_j16_yanwei_broken` 等照旧）。实施节点时：
    - 节点真正 fire（照史实推进）时 `set_global_variable = { name = <PRE> value = yes }`；
    - 节点跳过、作废、自保护前标、`hd_j16_mark_before_start_effect` 登记时一律**不设**；跳过另设 `hd_j16_<x>_skip`；
    - 节点自身防重入仍用 `_done`（跳过时也设 `_done`），下游节点判上游仍读 `_done`；
    - 查本节涉及哪些 PRE：`grep` tsv 第 8 列，或 `python -I -B tools/hd_j16/gen_deaths.py`（会报「PRE 目前 mod 里无人设置」）。实施完本节后，本节的 PRE 应从这条 W 中消失，写进报告。
16. **人物 ID**：第 2 期已合并 98 对重复人物，删除的 ID 见 `docs/人物审查/合并记录_2026-10-27.csv`，不得再引用；新建人物见 `history/characters/zz_hd_j16_characters.txt`（前缀 hd_j16_）。早出场幼主名单 `tools/hd_j16/early_spawn.tsv`。
