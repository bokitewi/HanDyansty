# 天朝循环大修：战略区 AI 生成脚本。修改 ADJ（邻接表）后运行：python docs/tools/gen_strategic_ai.py
# 生成 common/scripted_effects/hd_strategic_ai_effects.txt 与 common/scripted_triggers/hd_strategic_ai_adjacency_triggers.txt
import pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]  # mod 根目录
R = "strategic_region_"
ADJ = {
    "guanzhong": ["xiliang", "bashu", "zhongyuan", "shanxi", "xia"],
    "zhongyuan": ["hebei", "guanzhong", "shanxi", "jiangnan", "bashu"],
    "hebei": ["zhongyuan", "shanxi", "xianbei"],
    "shanxi": ["hebei", "guanzhong", "zhongyuan", "xia", "xianbei"],
    "xia": ["xiliang", "guanzhong", "shanxi", "xianbei"],
    "xiliang": ["guanzhong", "xia", "bashu"],
    "bashu": ["guanzhong", "xiliang", "zhongyuan", "jiangnan", "lingnan"],
    "jiangnan": ["zhongyuan", "bashu", "lingnan"],
    "lingnan": ["jiangnan", "bashu"],
    "xianbei": ["hebei", "shanxi", "xia"],
}
# symmetry check
for a, ns in ADJ.items():
    for b in ns:
        assert a in ADJ[b], (a, b)
REGIONS = list(ADJ)

T = "\t"
out = []
w = out.append
w("\ufeff# 天朝循环大修：战略区 AI（统一派发器）。本文件由脚本生成邻接分支，邻接表：")
for a, ns in ADJ.items():
    w(f"#   {a} <-> {' / '.join(ns)}")
w("")
w("# 记录当前战略区（region 供地理判定，key 供邻接表分支）。Scope：发动者")
w("hd_strat_set_region_effect = {")
w("\tset_variable = { name = hd_strat_region value = geographical_region:$REGION$ }")
w("\tset_variable = { name = hd_strat_region_key value = flag:$REGION$ }")
w("}")
w("")
w("# 初始化：首都所在战略区（交叉地带随机一个，选定后不再重抽）+ 扩张/守成。Scope：发动者")
w("hd_strat_init_effect = {")
w("\tif = {")
w("\t\tlimit = { NOT = { has_variable = hd_strat_region } }")
w("\t\trandom_list = {")
for r in REGIONS:
    w(f"\t\t\t1 = {{")
    w(f"\t\t\t\ttrigger = {{ capital_province ?= {{ geographical_region = {R}{r} }} }}")
    w(f"\t\t\t\thd_strat_set_region_effect = {{ REGION = {R}{r} }}")
    w(f"\t\t\t}}")
w("\t\t}")
w("\t}")
w("\thd_strat_assign_mode_effect = yes")
w("}")
w("")
w("# 只看性格：扩张分 > 守成分则扩张（两者皆 0 时扩张）。Scope：发动者")
w("hd_strat_assign_mode_effect = {")
w("\tif = {")
w("\t\tlimit = {")
w("\t\t\tOR = {")
w("\t\t\t\thd_strat_expand_score_value > hd_strat_hold_score_value")
w("\t\t\t\tAND = {")
w("\t\t\t\t\thd_strat_expand_score_value = 0")
w("\t\t\t\t\thd_strat_hold_score_value = 0")
w("\t\t\t\t}")
w("\t\t\t}")
w("\t\t}")
w("\t\tset_variable = { name = hd_strat_mode value = flag:expand }")
w("\t\tif = {")
w("\t\t\tlimit = { NOT = { has_character_modifier = hd_strat_expander_modifier } }")
w("\t\t\tadd_character_modifier = hd_strat_expander_modifier")
w("\t\t}")
w("\t}")
w("\telse = {")
w("\t\tset_variable = { name = hd_strat_mode value = flag:hold }")
w("\t\tremove_character_modifier = hd_strat_expander_modifier")
w("\t}")
w("}")
w("")
w("# story 结束时清理。Scope：发动者")
w("hd_strat_cleanup_effect = {")
w("\tremove_variable = hd_strat_region")
w("\tremove_variable = hd_strat_region_key")
w("\tremove_variable = hd_strat_mode")
w("\tremove_character_modifier = hd_strat_expander_modifier")
w("}")
w("")
w("""# 脉冲。Scope：发动者
hd_strat_pulse_effect = {
	if = {
		limit = {
			hd_strat_pulse_ready_trigger = yes
			var:hd_strat_mode ?= flag:expand
			has_variable = hd_strat_region
		}
		save_scope_as = hd_strat_actor
		var:hd_strat_region = { save_scope_as = hd_strat_region }
		hd_strat_find_target_effect = yes
		if = {
			limit = { exists = scope:hd_strat_target }
			hd_strat_engage_target_effect = yes
		}
		else = {
			hd_strat_next_region_effect = yes
		}
	}
}

# 选目标：1) 相邻且非挚友 2) 区内兜底扫描（每年最多一次）3) 相邻挚友（最后才打）
hd_strat_find_target_effect = {
	clear_saved_scope = hd_strat_target
	ordered_neighboring_top_liege_realm_owner = {
		limit = {
			hd_strat_region_target_trigger = yes
			hd_strat_friendly_target_trigger = no
		}
		order_by = hd_strat_target_priority_value
		save_scope_as = hd_strat_target
	}
	if = {
		limit = {
			NOT = { exists = scope:hd_strat_target }
			NOT = { has_character_flag = hd_strat_scan_cooldown }
		}
		add_character_flag = { flag = hd_strat_scan_cooldown days = 365 }
		every_county_in_region = {
			region = scope:hd_strat_region
			limit = { exists = holder }
			holder.top_liege = {
				if = {
					limit = {
						NOT = { is_in_list = hd_strat_candidates }
						hd_strat_region_target_trigger = yes
						hd_strat_friendly_target_trigger = no
					}
					add_to_list = hd_strat_candidates
				}
			}
		}
		ordered_in_list = {
			list = hd_strat_candidates
			order_by = hd_strat_target_priority_value
			save_scope_as = hd_strat_target
		}
	}
	if = {
		limit = { NOT = { exists = scope:hd_strat_target } }
		ordered_neighboring_top_liege_realm_owner = {
			limit = { hd_strat_region_target_trigger = yes }
			order_by = hd_strat_target_priority_value
			save_scope_as = hd_strat_target
		}
	}
}

# 先招降（仁义性格或挚友目标），被拒后下次脉冲直接宣战
hd_strat_engage_target_effect = {
	if = {
		limit = {
			OR = {
				hd_strat_offers_first_trigger = yes
				scope:hd_strat_target = { hd_strat_friendly_target_trigger = yes }
			}
			scope:hd_strat_target = {
				NOT = { var:hd_strat_offer_from ?= scope:hd_strat_actor }
				highest_held_title_tier < scope:hd_strat_actor.highest_held_title_tier
				hd_submission_recipient_legal_trigger = { LIEGE = scope:hd_strat_actor }
			}
			hd_submission_liege_trigger = yes
		}
		scope:hd_strat_target = {
			set_variable = { name = hd_strat_offer_from value = scope:hd_strat_actor days = 120 }
		}
		run_interaction = {
			interaction = hd_warlord_offer_vassalization_interaction
			actor = scope:hd_strat_actor
			recipient = scope:hd_strat_target
			send_threshold = decline
		}
	}
	else = {
		hd_strat_declare_war_effect = yes
	}
}

# 按阶段选 CB：斗争=兼并；对峙且帝国级=统一战争；否则逐鹿中原（区内、与本国相邻的公国）
hd_strat_declare_war_effect = {
	clear_saved_scope = hd_strat_war_title
	if = {
		limit = {
			hd_cycle_phase_is_struggle_trigger = yes
			can_declare_war = {
				defender = scope:hd_strat_target
				casus_belli = hd_strategic_annex_cb
			}
		}
		start_war = {
			cb = hd_strategic_annex_cb
			target = scope:hd_strat_target
		}
	}
	else_if = {
		limit = {
			hd_cycle_phase_is_standoff_trigger = yes
			highest_held_title_tier >= tier_empire
			can_declare_war = {
				defender = scope:hd_strat_target
				casus_belli = hd_unification_cb
			}
		}
		start_war = {
			cb = hd_unification_cb
			target = scope:hd_strat_target
		}
	}
	else = {
		scope:hd_strat_target = {
			random_realm_county = {
				limit = {
					title_province = { geographical_region = scope:hd_strat_region }
					any_neighboring_county = { holder.top_liege ?= scope:hd_strat_actor }
				}
				duchy ?= { save_scope_as = hd_strat_war_title }
			}
		}
		if = {
			limit = {
				exists = scope:hd_strat_war_title
				can_declare_war = {
					defender = scope:hd_strat_target
					casus_belli = chinese_consolidation_cb
					target_titles = { scope:hd_strat_war_title }
				}
			}
			start_war = {
				cb = chinese_consolidation_cb
				target = scope:hd_strat_target
				target_title = scope:hd_strat_war_title
			}
		}
	}
	add_character_flag = { flag = hd_strat_war_cooldown days = 30 }
}

# 本区无目标：在邻接区中找"有合法目标且最弱"的相邻势力，转向其所在的邻区
hd_strat_next_region_effect = {
	clear_saved_scope = hd_strat_next_owner
	ordered_neighboring_top_liege_realm_owner = {
		limit = {
			hd_strat_base_target_trigger = yes
			any_realm_county = { hd_strat_county_in_adjacent_region_trigger = yes }
		}
		order_by = { value = current_military_strength multiply = -1 }
		save_scope_as = hd_strat_next_owner
	}
	if = {
		limit = { exists = scope:hd_strat_next_owner }""")
first = True
for a, ns in ADJ.items():
    kw = "if" if first else "else_if"
    first = False
    w(f"\t\t{kw} = {{")
    w(f"\t\t\tlimit = {{ var:hd_strat_region_key = flag:{R}{a} }}")
    inner_first = True
    for b in ns:
        ikw = "if" if inner_first else "else_if"
        inner_first = False
        w(f"\t\t\t{ikw} = {{")
        w(f"\t\t\t\tlimit = {{ scope:hd_strat_next_owner = {{ any_realm_county = {{ title_province = {{ geographical_region = {R}{b} }} }} }} }}")
        w(f"\t\t\t\thd_strat_set_region_effect = {{ REGION = {R}{b} }}")
        w(f"\t\t\t}}")
    w(f"\t\t}}")
w("\t}")
w("}")
(ROOT / "common/scripted_effects/hd_strategic_ai_effects.txt").write_text("\n".join(out) + "\n", encoding="utf-8")

# adjacency trigger
t = []
a_ = t.append
a_("\ufeff# 天朝循环大修：战略区邻接判定（脚本生成）。Scope：伯爵领；需要 scope:hd_strat_actor")
a_("hd_strat_county_in_adjacent_region_trigger = {")
a_("\tOR = {")
for a, ns in ADJ.items():
    a_("\t\tAND = {")
    a_(f"\t\t\tscope:hd_strat_actor.var:hd_strat_region_key = flag:{R}{a}")
    a_("\t\t\ttitle_province = {")
    a_("\t\t\t\tOR = {")
    for b in ns:
        a_(f"\t\t\t\t\tgeographical_region = {R}{b}")
    a_("\t\t\t\t}")
    a_("\t\t\t}")
    a_("\t\t}")
a_("\t}")
a_("}")
(ROOT / "common/scripted_triggers/hd_strategic_ai_adjacency_triggers.txt").write_text("\n".join(t) + "\n", encoding="utf-8")
print("generated")
