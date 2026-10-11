# -*- coding: utf-8 -*-
# 生成朋党系统：scripted_effects / modifiers / opinion_modifiers
import re, os
MOD = r"E:\documents\Paradox Interactive\Crusader Kings III\mod\HanDyansty"
G = ['huanguan', 'waiqi', 'wuxun', 'shizu', 'hanmen']
KEY = {'huanguan': 'undecided_movement', 'waiqi': 'pro_hegemon_movement', 'wuxun': 'expansion_movement',
       'shizu': 'conservative_movement', 'hanmen': 'advancement_movement'}
FLAG = {'huanguan': 'undecided', 'waiqi': 'pro_hegemon', 'wuxun': 'expansion', 'shizu': 'conservative', 'hanmen': 'advancement'}
CN = {'huanguan': '宦官', 'waiqi': '外戚', 'wuxun': '武勋', 'shizu': '世族', 'hanmen': '寒门'}
STANCES = ['zunwang', 'kaituo', 'jinqu', 'shoujiu', 'zhongli']
PHASES = ['stability_expansion', 'stability_advancement', 'instability_conquest', 'instability', 'chaos',
          'hd_recovery', 'hd_collapse', 'hd_standoff']
PAIRS = [(a, b) for i, a in enumerate(G) for b in G[i+1:]]

def w(path, text):
    p = os.path.join(MOD, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w', encoding='utf-8-sig', newline='\r\n').write(text.replace('\r\n', '\n'))

def grp(g):
    return 'situation:dynastic_cycle.situation_participant_group:%s' % KEY[g]

E = []
E.append('''# 天朝循环大修·朋党：核心效果（由 docs/tools/gen_party_effects.py 生成，勿手改）
# 数据统一存放在"朝廷君主"身上：var:hd_party_<组>_*；天子朝廷的领袖/势力/青睐同步写回原版全局组。
# 成员身上：var:hd_party_my_court / hd_party_my_group / hd_party_my_stance（400 天过期，年度刷新）

############################################################
# 年度总流程（Scope：dynastic_cycle 局势，局势 on_yearly 调用）
############################################################
hd_party_yearly_effect = {
	# 1. 收集朝廷
	situation:dynastic_cycle.situation_participant_group:hegemon_ruler = {
		every_situation_group_participant = {
			limit = { hd_party_court_ruler_trigger = yes }
			add_to_list = hd_party_courts
		}
	}
	situation:dynastic_cycle.situation_participant_group:other_rulers = {
		every_situation_group_participant = {
			limit = {
				has_variable = hd_party_court
				hd_party_court_ruler_trigger = no
			}
			hd_party_clear_court_effect = yes
		}
		every_situation_group_participant = {
			limit = { hd_party_court_ruler_trigger = yes }
			add_to_list = hd_party_courts
		}
	}
	every_in_list = {
		list = hd_party_courts
		if = {
			limit = { NOT = { has_variable = hd_party_court } }
			hd_party_init_court_effect = yes
		}
		set_variable = { name = hd_party_my_court value = this days = 400 }
''')
for g in G:
    E.append('\t\tclear_variable_list = hd_party_%s_members\n' % g)
E.append('''		save_scope_as = hd_party_court
		hd_party_add_manual_participants_effect = yes
	}
	# 2. 按身份组归入各朝廷的成员列表
''')
for g in G:
    E.append('''	%(grp)s = {
		every_situation_group_participant = {
			hd_party_member_pass_effect = { G = %(g)s }
		}
	}
''' % {'grp': grp(g), 'g': g})
E.append('''	# 3. 各朝廷分散到 60 天内结算
	every_in_list = {
		list = hd_party_courts
		trigger_event = {
			id = hd_party.0001
			days = { 1 60 }
		}
	}
}

# Scope：成员角色。归入所在朝廷 $G$ 党的成员列表
hd_party_member_pass_effect = {
	if = {
		limit = { is_alive = yes }
		hd_party_member_pass_alive_effect = { G = $G$ }
	}
}

hd_party_member_pass_alive_effect = {
	if = {
		limit = { has_variable = hd_party_court }
		hd_party_clear_court_effect = yes
	}
	if = {
		limit = {
			has_variable = hd_party_manual
			NOT = { hd_party_manual_participant_valid_trigger = yes }
		}
		remove_variable = hd_party_manual
		situation:dynastic_cycle = { remove_manual_participant = prev }
	}
	else = {
		clear_saved_scope = hd_party_mc
		hd_party_save_member_court_effect = yes
		if = {
			limit = {
				exists = scope:hd_party_mc
				scope:hd_party_mc = { is_in_list = hd_party_courts }
			}
			scope:hd_party_mc = {
				add_to_variable_list = { name = hd_party_$G$_members target = prev }
			}
			set_variable = { name = hd_party_my_court value = scope:hd_party_mc days = 400 }
			set_variable = { name = hd_party_my_group value = flag:$G$ days = 400 }
			if = {
				limit = { exists = scope:hd_party_mc.var:hd_party_$G$_stance }
				set_variable = { name = hd_party_my_stance value = scope:hd_party_mc.var:hd_party_$G$_stance days = 400 }
			}
		}
	}
}

# Scope：角色。把所在朝廷的君主存为 scope:hd_party_mc（没有朝廷则不存）
hd_party_save_member_court_effect = {
	if = {
		limit = {
			exists = title:h_china.holder
			OR = {
				top_liege = title:h_china.holder
				is_tributary_of = title:h_china.holder
			}
		}
		title:h_china.holder = { save_scope_as = hd_party_mc }
	}
	else_if = {
		limit = {
			exists = top_liege
			top_liege != this
		}
		top_liege = { save_scope_as = hd_party_mc }
	}
	# 2026-10-10：离宫在野的后族成员仍归原朝廷
	else_if = {
		limit = { hd_party_is_wandering_waiqi_trigger = yes }
		var:hd_party_waiqi_court = { save_scope_as = hd_party_mc }
	}
}

# Scope：君主（scope:hd_party_court）。把有政治分量的无地廷臣加入局势
hd_party_add_manual_participants_effect = {
	every_courtier = {
		limit = {
			is_adult = yes
			NOT = { has_variable = hd_party_manual }
			hd_party_manual_participant_valid_trigger = yes
			NOT = { any_character_situation = { situation_type = dynastic_cycle } }
		}
		set_variable = hd_party_manual
		situation:dynastic_cycle = { add_manual_participant = prev }
		recalculate_participant_group = situation:dynastic_cycle
	}
}

############################################################
# 朝廷初始化 / 清除 / 继承
############################################################
# Scope：君主
hd_party_init_court_effect = {
	set_variable = { name = hd_party_court value = this }
''')
for g in G:
    E.append('\tset_variable = { name = hd_party_%s_attitude value = flag:neutral }\n' % g)
E.append('}\n\n# Scope：君主。清除全部朋党数据与 modifier\nhd_party_clear_court_effect = {\n\tremove_variable = hd_party_court\n\tremove_variable = hd_party_favored\n\tremove_variable = hd_party_favor_cd\n\tremove_variable = hd_party_favor_years\n\tremove_variable = hd_party_chain_tick\n')
GV = ['leader', 'power', 'power_mod', 'share', 'stance', 'attitude', 'policy', 'policy_cd', 'satisfaction', 'score',
      'disgrace', 'sat_mod', 'loyalty_lock', 'loyalty_cd', 'oppose_lock', 'oppose_years', 'debate_lock', 'debating',
      'chain_stage', 'chain_paused']
for g in G:
    for v in GV:
        E.append('\tremove_variable = hd_party_%s_%s\n' % (g, v))
    E.append('\tclear_variable_list = hd_party_%s_members\n\tclear_variable_list = hd_party_%s_top\n' % (g, g))
E.append('\thd_party_remove_ruler_modifiers_effect = yes\n}\n\n')

# inheritance copy
E.append('''# Scope：继承人；$OLD$ = 将死的前任（on_death 时仍可读变量）。继承时沿用前任的朋党数据（Q58）
hd_party_inherit_court_effect = {
	set_variable = { name = hd_party_court value = this }
''')
for g in G:
    for v in ['leader', 'power', 'power_mod', 'share', 'stance', 'attitude', 'satisfaction', 'disgrace', 'sat_mod', 'debate_lock', 'oppose_years']:
        E.append('\tif = { limit = { exists = $OLD$.var:hd_party_%(g)s_%(v)s } set_variable = { name = hd_party_%(g)s_%(v)s value = $OLD$.var:hd_party_%(g)s_%(v)s } }\n' % {'g': g, 'v': v})
E.append('''	# 君主更替：青睐清空、政策回到中立、要求效忠锁定解除（拥护/对抗随后重算）
	$OLD$ = { hd_party_clear_court_effect = yes }
	trigger_event = { id = hd_party.0001 days = 1 }
}

# Scope：君主。移除君主身上所有朋党 modifier
hd_party_remove_ruler_modifiers_effect = {
''')
for g in G:
    for a in ['support', 'oppose']:
        E.append('\tremove_character_modifier = hd_party_attitude_%s_%s_modifier\n' % (g, a))
    for c in ['inf_low', 'inf_high', 'pre_low', 'pre_high']:
        E.append('\tremove_character_modifier = hd_party_policy_cost_%s_%s_modifier\n' % (g, c))
E.append('\thd_party_remove_favor_copy_effect = yes\n}\n\n# Scope：君主。移除青睐复制 modifier\nhd_party_remove_favor_copy_effect = {\n')
for g in G:
    for p in PHASES:
        E.append('\tremove_character_modifier = hd_party_favor_%s_%s_modifier\n' % (g, p))
E.append('}\n\n')

# favor copy add
E.append('# Scope：君主。按当前时代给被青睐朋党的组效果复制件\nhd_party_apply_favor_copy_effect = {\n\thd_party_remove_favor_copy_effect = yes\n')
for g in G:
    E.append('\tif = {\n\t\tlimit = { var:hd_party_favored ?= flag:%s }\n' % g)
    for p in PHASES:
        E.append('\t\tif = { limit = { situation:dynastic_cycle ?= { situation_current_phase = situation_dynastic_cycle_phase_%s } } add_character_modifier = hd_party_favor_%s_%s_modifier }\n' % (p, g, p))
    E.append('\t}\n')
E.append('}\n\n')

# waiqi list
E.append('''# Scope：君主。重建后族宗族列表（母亲、正妻与嫔妃、子女配偶的宗族；不含本宗族）
# 2026-10-10：另建后妃兄弟姐妹列表 hd_party_waiqi_kin（母亲、正妻、嫔妃的兄弟姐妹，含同父异母/同母异父；不含本宗族）
hd_party_refresh_waiqi_list_effect = {
	clear_variable_list = hd_party_waiqi_dynasties
	clear_variable_list = hd_party_waiqi_kin
	save_temporary_scope_as = hd_party_wq_ruler
	mother ?= {
		if = {
			limit = { exists = dynasty dynasty != scope:hd_party_wq_ruler.dynasty }
			scope:hd_party_wq_ruler = { add_to_variable_list = { name = hd_party_waiqi_dynasties target = prev.dynasty } }
		}
	}
	every_spouse = {
		limit = { exists = dynasty dynasty != scope:hd_party_wq_ruler.dynasty }
		scope:hd_party_wq_ruler = { add_to_variable_list = { name = hd_party_waiqi_dynasties target = prev.dynasty } }
	}
	every_consort = {
		limit = { exists = dynasty dynasty != scope:hd_party_wq_ruler.dynasty }
		scope:hd_party_wq_ruler = { add_to_variable_list = { name = hd_party_waiqi_dynasties target = prev.dynasty } }
	}
	every_child = {
		every_spouse = {
			limit = { exists = dynasty dynasty != scope:hd_party_wq_ruler.dynasty }
			scope:hd_party_wq_ruler = { add_to_variable_list = { name = hd_party_waiqi_dynasties target = prev.dynasty } }
		}
	}
	mother ?= { hd_party_add_waiqi_kin_effect = yes }
	every_spouse = { hd_party_add_waiqi_kin_effect = yes }
	every_consort = { hd_party_add_waiqi_kin_effect = yes }
	# 2026-10-08：后族全宗族强制入外戚、失势外戚解除（手工维护：hd_party_waiqi_sweep_effects.txt）
	hd_party_waiqi_sweep_effect = yes
}

# Scope：后妃或君主母亲；scope:hd_party_wq_ruler = 君主。把其兄弟姐妹加入 hd_party_waiqi_kin
# 用父亲、母亲各自的子女来找，同父异母、同母异父都能找到（2026-10-10）
hd_party_add_waiqi_kin_effect = {
	save_temporary_scope_as = hd_party_wq_consort
	father ?= {
		every_child = {
			limit = {
				NOT = { this = scope:hd_party_wq_consort }
				hd_party_waiqi_kin_valid_trigger = { RULER = scope:hd_party_wq_ruler }
			}
			scope:hd_party_wq_ruler = { add_to_variable_list = { name = hd_party_waiqi_kin target = prev } }
		}
	}
	mother ?= {
		every_child = {
			limit = {
				NOT = { this = scope:hd_party_wq_consort }
				hd_party_waiqi_kin_valid_trigger = { RULER = scope:hd_party_wq_ruler }
			}
			scope:hd_party_wq_ruler = { add_to_variable_list = { name = hd_party_waiqi_kin target = prev } }
		}
	}
}

############################################################
# 朝廷结算（Scope：君主；事件 hd_party.0001 调用）
############################################################
hd_party_court_refresh_effect = {
	save_scope_as = hd_party_court
	if = {
		limit = { NOT = { has_variable = hd_party_court } }
		hd_party_init_court_effect = yes
	}
	# 界面用：君主自身也指向本朝廷
	set_variable = { name = hd_party_my_court value = this days = 400 }
	# 记录战争、饥荒
	if = {
		limit = { is_at_war = yes }
		set_variable = { name = hd_party_recent_war days = 3650 }
	}
	if = {
		limit = { any_sub_realm_county = { has_county_modifier = hd_famine_county_modifier } }
		set_variable = { name = hd_party_famine_flag days = 400 }
	}
	else = {
		remove_variable = hd_party_famine_flag
	}
	hd_party_refresh_waiqi_list_effect = yes
	# 第一轮：领袖、前三名、势力
''')
for g in G:
    E.append('\thd_party_refresh_leader_and_power_effect = { G = %s KEY = %s }\n' % (g, KEY[g]))
E.append('\t# 第二轮：占比、满意度、拥护/对抗、成员效果\n\tset_variable = { name = hd_party_total_power value = hd_party_total_power_value }\n')
for g in G:
    E.append('\thd_party_refresh_party_effect = { G = %s }\n' % g)
E.append('''	hd_party_refresh_policy_cost_effect = yes
	hd_party_apply_favor_copy_effect = yes
	hd_party_refresh_relations_effect = yes
	hd_party_favor_chain_tick_effect = yes
	if = {
		limit = { is_ai = yes }
		hd_party_ai_ruler_effect = yes
	}
	hd_party_ai_leader_debate_effect = yes
}

# Scope：君主。$G$ 党领袖、前三名与势力
hd_party_refresh_leader_and_power_effect = {
	# 领袖失效：死亡、离开、被禁
	if = {
		limit = {
			exists = var:hd_party_$G$_leader
			var:hd_party_$G$_leader = {
				OR = {
					is_alive = no
					has_variable = hd_party_leader_ban
					NOT = { scope:hd_party_court = { is_target_in_variable_list = { name = hd_party_$G$_members target = prev } } }
				}
			}
		}
		remove_variable = hd_party_$G$_leader
	}
	if = {
		limit = { NOT = { exists = var:hd_party_$G$_leader } }
		clear_saved_scope = hd_party_new_leader
		# 天子朝廷：优先沿用原版组领袖
		if = {
			limit = { has_title = title:h_china }
			situation:dynastic_cycle.situation_participant_group:$KEY$.var:movement_leader ?= {
				if = {
					limit = {
						is_alive = yes
						NOT = { has_variable = hd_party_leader_ban }
						scope:hd_party_court = { is_target_in_variable_list = { name = hd_party_$G$_members target = prev } }
					}
					save_scope_as = hd_party_new_leader
				}
			}
		}
		if = {
			limit = { NOT = { exists = scope:hd_party_new_leader } }
			ordered_in_list = {
				variable = hd_party_$G$_members
				limit = {
					is_alive = yes
					exists = var:movement_power
					NOT = { has_variable = hd_party_leader_ban }
				}
				order_by = var:movement_power
				save_scope_as = hd_party_new_leader
			}
		}
		if = {
			limit = { exists = scope:hd_party_new_leader }
			set_variable = { name = hd_party_$G$_leader value = scope:hd_party_new_leader }
			hd_party_on_new_leader_effect = { G = $G$ KEY = $KEY$ }
		}
	}
	# 前三名
	clear_variable_list = hd_party_$G$_top
	ordered_in_list = {
		variable = hd_party_$G$_members
		limit = {
			is_alive = yes
			exists = var:movement_power
		}
		order_by = var:movement_power
		max = 3
		check_range_bounds = no
		scope:hd_party_court = { add_to_variable_list = { name = hd_party_$G$_top target = prev } }
	}
	# 势力：一律只计本朝廷成员（乱世中天子与诸侯各自独立计算）
	if = {
		limit = { always = yes }
		set_variable = { name = hd_party_$G$_power value = 0 }
		every_in_list = {
			variable = hd_party_$G$_members
			limit = {
				is_alive = yes
				exists = var:movement_power
			}
			scope:hd_party_court = { hd_party_add_var_effect = { NAME = hd_party_$G$_power VALUE = prev.var:movement_power } }
		}
		if = {
			limit = { var:hd_party_favored ?= flag:$G$ }
			hd_party_add_var_effect = { NAME = hd_party_$G$_power VALUE = hd_party_favored_power_bonus }
		}
	}
	if = {
		limit = { exists = var:hd_party_$G$_power_mod }
		hd_party_add_var_effect = { NAME = hd_party_$G$_power VALUE = var:hd_party_$G$_power_mod }
		# 临时势力每年衰减 20%
		change_variable = { name = hd_party_$G$_power_mod multiply = 0.8 }
		if = {
			limit = {
				var:hd_party_$G$_power_mod > -5
				var:hd_party_$G$_power_mod < 5
			}
			remove_variable = hd_party_$G$_power_mod
		}
	}
	# 天朝循环·时代特色：紧张期乱象（该党势力 +40%）、党锢"一网打尽"（势力归零 10 年）
	if = {
		limit = { var:hd_dc_ten_boost_group ?= flag:$G$ }	# 只有外戚/宦官/武勋会被加成；用单一变量避免对世族/寒门报"读取但从未设置"
		change_variable = { name = hd_party_$G$_power multiply = 1.4 }
	}
	if = {
		limit = { has_variable = hd_dc_ten_purged_$G$ }
		set_variable = { name = hd_party_$G$_power value = 0 }
	}
	if = {
		limit = { var:hd_party_$G$_power < 0 }
		set_variable = { name = hd_party_$G$_power value = 0 }
	}
}

# Scope：君主。新领袖上任：解除要求效忠锁定并按新领袖性格免辩论重选一次；天子朝廷同步原版组领袖
hd_party_on_new_leader_effect = {
	if = {
		limit = { has_variable = hd_party_$G$_loyalty_lock }
		remove_variable = hd_party_$G$_loyalty_lock
		hd_party_pick_stance_effect = { G = $G$ }
	}
	if = {
		limit = { NOT = { exists = var:hd_party_$G$_stance } }
		hd_party_pick_stance_effect = { G = $G$ }
	}
	if = {
		limit = { has_title = title:h_china }
		situation:dynastic_cycle.situation_participant_group:$KEY$ = {
			set_variable = { name = movement_leader value = scope:hd_party_court.var:hd_party_$G$_leader }
		}
	}
}

# Scope：君主。$G$ 党按领袖性格加权随机选择立场；没有领袖时为中立
hd_party_pick_stance_effect = {
	if = {
		limit = { exists = var:hd_party_$G$_leader }
		save_scope_as = hd_party_court # callers already save this as a permanent scope; a same-name temporary one is rejected
		var:hd_party_$G$_leader = {
''')
for s in STANCES:
    E.append('\t\t\tsave_temporary_scope_value_as = { name = hd_party_w_%s value = hd_party_stance_weight_%s_value }\n' % (s, s))
E.append('\t\t}\n\t\trandom_list = {\n')
for s in STANCES:
    E.append('\t\t\t0 = {\n\t\t\t\tmodifier = { add = scope:hd_party_w_%s }\n\t\t\t\thd_party_set_stance_effect = { G = $G$ STANCE = %s }\n\t\t\t}\n' % (s, s))
E.append('''		}
	}
	else = {
		hd_party_set_stance_effect = { G = $G$ STANCE = zhongli }
	}
}

# Scope：君主。把 $G$ 党立场设为 $STANCE$，立即更新成员变量
hd_party_set_stance_effect = {
	set_variable = { name = hd_party_$G$_stance value = flag:$STANCE$ }
	every_in_list = {
		variable = hd_party_$G$_members
		limit = { is_alive = yes }
		set_variable = { name = hd_party_my_stance value = flag:$STANCE$ days = 400 }
		if = {
			limit = { var:hd_party_my_stance = flag:zunwang }
			add_character_modifier = { modifier = hd_party_stance_zunwang_modifier days = 400 }
		}
		else = {
			remove_character_modifier = hd_party_stance_zunwang_modifier
		}
	}
}

# Scope：君主。$G$ 党：占比、满意度、拥护/对抗、成员效果
hd_party_refresh_party_effect = {
	set_variable = {
		name = hd_party_$G$_share
		value = {
			value = var:hd_party_$G$_power
			multiply = 100
			divide = var:hd_party_total_power
		}
	}
	# 失宠衰减（年）
	if = {
		limit = { exists = var:hd_party_$G$_disgrace }
		hd_party_add_var_effect = { NAME = hd_party_$G$_disgrace VALUE = -1 }
		if = {
			limit = { var:hd_party_$G$_disgrace <= 0 }
			remove_variable = hd_party_$G$_disgrace
		}
	}
	set_variable = { name = hd_party_$G$_satisfaction value = hd_party_satisfaction_$G$_value }
	# 事件造成的满意度变化每年衰减 20%
	if = {
		limit = { exists = var:hd_party_$G$_sat_mod }
		change_variable = { name = hd_party_$G$_sat_mod multiply = 0.8 }
		if = {
			limit = {
				var:hd_party_$G$_sat_mod > -3
				var:hd_party_$G$_sat_mod < 3
			}
			remove_variable = hd_party_$G$_sat_mod
		}
	}
	set_variable = { name = hd_party_$G$_score value = hd_party_attitude_score_$G$_value }
	# 拥护/对抗（玩家领袖自行选择；失败锁定期间维持对抗）
	if = {
		limit = {
			NOT = { has_variable = hd_party_$G$_oppose_lock }
			NOT = { var:hd_party_$G$_leader ?= { is_ai = no } }
		}
		if = {
			limit = { var:hd_party_$G$_attitude ?= flag:support }
			if = {
				limit = { var:hd_party_$G$_score < 20 }
				hd_party_set_attitude_effect = { G = $G$ ATTITUDE = neutral }
			}
		}
		else_if = {
			limit = { var:hd_party_$G$_attitude ?= flag:oppose }
			if = {
				limit = { var:hd_party_$G$_score > -20 }
				hd_party_set_attitude_effect = { G = $G$ ATTITUDE = neutral }
			}
		}
		else = {
			if = {
				limit = { var:hd_party_$G$_score >= 50 }
				hd_party_set_attitude_effect = { G = $G$ ATTITUDE = support }
			}
			else_if = {
				limit = { var:hd_party_$G$_score <= -50 }
				hd_party_set_attitude_effect = { G = $G$ ATTITUDE = oppose }
			}
		}
	}
	if = {
		limit = { var:hd_party_$G$_attitude ?= flag:oppose }
		hd_party_add_var_effect = { NAME = hd_party_$G$_oppose_years VALUE = 1 }
	}
	else = {
		remove_variable = hd_party_$G$_oppose_years
	}
	hd_party_apply_attitude_modifier_effect = { G = $G$ }
	hd_party_apply_member_effects_effect = { G = $G$ }
}

# Scope：君主。设置 $G$ 党态度
hd_party_set_attitude_effect = {
	set_variable = { name = hd_party_$G$_attitude value = flag:$ATTITUDE$ }
	hd_party_apply_attitude_modifier_effect = { G = $G$ }
}

# Scope：君主。按 $G$ 党态度给君主拥护/对抗 modifier（势力衰微时不施加）
hd_party_apply_attitude_modifier_effect = {
	remove_character_modifier = hd_party_attitude_$G$_support_modifier
	remove_character_modifier = hd_party_attitude_$G$_oppose_modifier
	if = {
		limit = { NOT = { hd_party_is_weak_trigger = { G = $G$ } } }
		if = {
			limit = { var:hd_party_$G$_attitude ?= flag:support }
			add_character_modifier = hd_party_attitude_$G$_support_modifier
		}
		else_if = {
			limit = { var:hd_party_$G$_attitude ?= flag:oppose }
			add_character_modifier = hd_party_attitude_$G$_oppose_modifier
		}
	}
}

# Scope：君主。$G$ 党成员：政策 modifier 与好感、尊王 modifier、被青睐好感
hd_party_apply_member_effects_effect = {
	every_in_list = {
		variable = hd_party_$G$_members
		limit = { is_alive = yes }
		remove_character_modifier = hd_party_policy_ban_modifier
		remove_character_modifier = hd_party_policy_restrict_modifier
		remove_character_modifier = hd_party_policy_promote_modifier
		if = {
			limit = { scope:hd_party_court.var:hd_party_$G$_policy ?= flag:ban }
			add_character_modifier = { modifier = hd_party_policy_ban_modifier days = 400 }
			add_opinion = { target = scope:hd_party_court modifier = hd_party_policy_ban_opinion years = 1 }
		}
		else_if = {
			limit = { scope:hd_party_court.var:hd_party_$G$_policy ?= flag:restrict }
			add_character_modifier = { modifier = hd_party_policy_restrict_modifier days = 400 }
			add_opinion = { target = scope:hd_party_court modifier = hd_party_policy_restrict_opinion years = 1 }
		}
		else_if = {
			limit = { scope:hd_party_court.var:hd_party_$G$_policy ?= flag:promote }
			add_character_modifier = { modifier = hd_party_policy_promote_modifier days = 400 }
			add_opinion = { target = scope:hd_party_court modifier = hd_party_policy_promote_opinion years = 1 }
		}
		if = {
			limit = { scope:hd_party_court.var:hd_party_$G$_stance ?= flag:zunwang }
			add_character_modifier = { modifier = hd_party_stance_zunwang_modifier days = 400 }
		}
		else = {
			remove_character_modifier = hd_party_stance_zunwang_modifier
		}
		if = {
			limit = { scope:hd_party_court.var:hd_party_favored ?= flag:$G$ }
			add_opinion = { target = scope:hd_party_court modifier = hd_party_favored_opinion years = 1 }
		}
	}
}

# Scope：君主。政治运作的每月花费 modifier；资源透支时全部回到中立
hd_party_refresh_policy_cost_effect = {
''')
for g in G:
    E.append('''	remove_character_modifier = hd_party_policy_cost_%(g)s_inf_low_modifier
	remove_character_modifier = hd_party_policy_cost_%(g)s_inf_high_modifier
	remove_character_modifier = hd_party_policy_cost_%(g)s_pre_low_modifier
	remove_character_modifier = hd_party_policy_cost_%(g)s_pre_high_modifier
''' % {'g': g})
E.append('''	if = {
		limit = {
			OR = {
				AND = {
					government_has_flag = government_has_influence
					influence < 0
				}
				AND = {
					NOT = { government_has_flag = government_has_influence }
					prestige < 0
				}
			}
		}
''')
for g in G:
    E.append('\t\tremove_variable = hd_party_%s_policy\n' % g)
E.append('''		if = {
			limit = { is_ai = no }
			send_interface_toast = {
				type = event_toast_effect_bad
				title = hd_party_policy_unpaid_toast
			}
		}
	}
''')
for g in G:
    E.append('''	if = {
		limit = { var:hd_party_%(g)s_policy ?= flag:ban }
		if = {
			limit = { government_has_flag = government_has_influence }
			add_character_modifier = hd_party_policy_cost_%(g)s_inf_high_modifier
		}
		else = {
			add_character_modifier = hd_party_policy_cost_%(g)s_pre_high_modifier
		}
	}
	else_if = {
		limit = {
			OR = {
				var:hd_party_%(g)s_policy ?= flag:restrict
				var:hd_party_%(g)s_policy ?= flag:promote
			}
		}
		if = {
			limit = { government_has_flag = government_has_influence }
			add_character_modifier = hd_party_policy_cost_%(g)s_inf_low_modifier
		}
		else = {
			add_character_modifier = hd_party_policy_cost_%(g)s_pre_low_modifier
		}
	}
''' % {'g': g})
E.append('}\n\n')

# relations
E.append('# Scope：君主（scope:hd_party_court）。对立/合作朋党的领袖与前三名之间互加好感\nhd_party_refresh_relations_effect = {\n')
for a, b in PAIRS:
    E.append('''	if = {
		limit = { hd_party_hostile_trigger = { A = %(a)s B = %(b)s } }
		hd_party_pair_hostile_effect = { A = %(a)s B = %(b)s }	# 天朝循环·时代特色：按时代/乱象换档
		set_variable = { name = hd_party_rel_%(a)s_%(b)s value = flag:hostile }
		set_variable = { name = hd_party_rel_%(b)s_%(a)s value = flag:hostile }
	}
	else_if = {
		limit = { hd_party_coop_trigger = { A = %(a)s B = %(b)s } }
		hd_party_pair_coop_effect = { A = %(a)s B = %(b)s }	# 天朝循环·时代特色：按时代换档
		set_variable = { name = hd_party_rel_%(a)s_%(b)s value = flag:coop }
		set_variable = { name = hd_party_rel_%(b)s_%(a)s value = flag:coop }
	}
	else = {
		set_variable = { name = hd_party_rel_%(a)s_%(b)s value = flag:none }
		set_variable = { name = hd_party_rel_%(b)s_%(a)s value = flag:none }
	}
''' % {'a': a, 'b': b})
E.append('''}

# 天朝循环·时代特色：党际好感按时代换档（docs/天朝循环_时代特色重制计划.md §3.2/§3.3）
# 天子朝廷进取期：对立减半、合作加倍；紧张期"党争内耗"乱象：对立加倍。换档时先移除其他档位，避免叠加
# Scope：君主（scope:hd_party_court）
hd_party_pair_hostile_effect = {
	if = {
		limit = {
			has_title = title:h_china
			hd_dc_phase_is_trigger = { PHASE = stability_advancement }
		}
		hd_party_pair_remove_opinion_effect = { A = $A$ B = $B$ OPINION = hd_party_hostile_opinion }
		hd_party_pair_remove_opinion_effect = { A = $A$ B = $B$ OPINION = hd_party_hostile_double_opinion }
		hd_party_pair_opinion_effect = { A = $A$ B = $B$ OPINION = hd_party_hostile_half_opinion }
	}
	else_if = {
		limit = { has_character_modifier = hd_dc_kit_ten_chaos_partisan_modifier }
		hd_party_pair_remove_opinion_effect = { A = $A$ B = $B$ OPINION = hd_party_hostile_opinion }
		hd_party_pair_remove_opinion_effect = { A = $A$ B = $B$ OPINION = hd_party_hostile_half_opinion }
		hd_party_pair_opinion_effect = { A = $A$ B = $B$ OPINION = hd_party_hostile_double_opinion }
	}
	else = {
		hd_party_pair_remove_opinion_effect = { A = $A$ B = $B$ OPINION = hd_party_hostile_half_opinion }
		hd_party_pair_remove_opinion_effect = { A = $A$ B = $B$ OPINION = hd_party_hostile_double_opinion }
		hd_party_pair_opinion_effect = { A = $A$ B = $B$ OPINION = hd_party_hostile_opinion }
	}
}
hd_party_pair_coop_effect = {
	if = {
		limit = {
			has_title = title:h_china
			hd_dc_phase_is_trigger = { PHASE = stability_advancement }
		}
		hd_party_pair_remove_opinion_effect = { A = $A$ B = $B$ OPINION = hd_party_coop_opinion }
		hd_party_pair_opinion_effect = { A = $A$ B = $B$ OPINION = hd_party_coop_double_opinion }
	}
	else = {
		hd_party_pair_remove_opinion_effect = { A = $A$ B = $B$ OPINION = hd_party_coop_double_opinion }
		hd_party_pair_opinion_effect = { A = $A$ B = $B$ OPINION = hd_party_coop_opinion }
	}
}
# Scope：君主。$A$ 与 $B$ 两党的前三名互相移除好感 $OPINION$
hd_party_pair_remove_opinion_effect = {
	every_in_list = {
		variable = hd_party_$A$_top
		limit = { is_alive = yes }
		save_temporary_scope_as = hd_party_pa
		scope:hd_party_court = {
			every_in_list = {
				variable = hd_party_$B$_top
				limit = { is_alive = yes }
				remove_opinion = { target = scope:hd_party_pa modifier = $OPINION$ }
				scope:hd_party_pa = { remove_opinion = { target = prev modifier = $OPINION$ } }
			}
		}
	}
}

# Scope：君主。$A$ 与 $B$ 两党的前三名互加好感 $OPINION$
hd_party_pair_opinion_effect = {
	every_in_list = {
		variable = hd_party_$A$_top
		limit = { is_alive = yes }
		save_temporary_scope_as = hd_party_pa
		scope:hd_party_court = {
			every_in_list = {
				variable = hd_party_$B$_top
				limit = { is_alive = yes }
				add_opinion = { target = scope:hd_party_pa modifier = $OPINION$ years = 1 }
				scope:hd_party_pa = { add_opinion = { target = prev modifier = $OPINION$ years = 1 } }
			}
		}
	}
}

############################################################
# 青睐
############################################################
# Scope：君主。青睐 $G$ 党（$G$ = none 时取消青睐）。调用前已扣除花费
hd_party_set_favored_effect = {
	save_temporary_scope_value_as = { name = hd_party_new_fav value = flag:$G$ }
	# 原被青睐的朋党失宠
''')
for g in G:
    E.append('''	if = {
		limit = {
			var:hd_party_favored ?= flag:%(g)s
			NOT = { scope:hd_party_new_fav = flag:%(g)s }
		}
		set_variable = { name = hd_party_%(g)s_disgrace value = 10 }
		var:hd_party_%(g)s_leader ?= {
			add_opinion = { target = prev modifier = hd_party_disgraced_opinion }
		}
	}
''' % {'g': g})
E.append('''	remove_variable = hd_party_favored
	remove_variable = hd_party_favor_years
	if = {
		limit = { NOT = { scope:hd_party_new_fav = flag:none } }
		set_variable = { name = hd_party_favored value = flag:$G$ }
		set_variable = { name = hd_party_favor_years value = 0 }
	}
	set_variable = { name = hd_party_favor_cd days = hd_party_favor_cd_days }
	# 天子朝廷：同步原版"当权朋党"
	if = {
		limit = { has_title = title:h_china }
		situation:dynastic_cycle ?= {
			every_participant_group = {
				limit = { has_variable = movement_favored }
				remove_variable = movement_favored
			}
		}
''')
for g in G:
    E.append('\t\tif = { limit = { scope:hd_party_new_fav = flag:%s } %s = { make_movement_favored_effect = yes } }\n' % (g, grp(g)))
E.append('''	}
	hd_party_apply_favor_copy_effect = yes
	trigger_event = { id = hd_party.0001 days = 1 }
}

# Scope：君主。青睐事件链计数（每年）
hd_party_favor_chain_tick_effect = {
	if = {
		limit = { exists = var:hd_party_favor_years }
		hd_party_add_var_effect = { NAME = hd_party_favor_years VALUE = 1 }
		if = {
			limit = { var:hd_party_favor_years >= 5 }
			hd_party_add_var_effect = { NAME = hd_party_chain_tick VALUE = 1 }
		}
		if = {
			limit = {
				var:hd_party_favor_years >= 5
				OR = {
					var:hd_party_favor_years = 5
					var:hd_party_chain_tick >= 5
				}
			}
			set_variable = { name = hd_party_chain_tick value = 0 }
''')
for g in G:
    E.append('''			if = {
				limit = {
					var:hd_party_favored ?= flag:%(g)s
					NOT = { var:hd_party_%(g)s_chain_stage ?= 3 }
				}
				random = {
					chance = hd_party_chain_chance
					modifier = {
						add = 20
						has_variable = hd_party_%(g)s_chain_paused
					}
					remove_variable = hd_party_%(g)s_chain_paused
					if = {
						limit = { NOT = { exists = var:hd_party_%(g)s_chain_stage } }
						trigger_event = hd_party_chain.%(n)d1
					}
					else_if = {
						limit = { var:hd_party_%(g)s_chain_stage = 1 }
						trigger_event = hd_party_chain.%(n)d2
					}
					else = {
						trigger_event = hd_party_chain.%(n)d3
					}
				}
			}
''' % {'g': g, 'n': G.index(g) + 1})
E.append('''		}
	}
}

############################################################
# 政策 / 要求效忠 / 态度（玩家与 AI 共用）
############################################################
# Scope：君主。把 $G$ 党政策设为 $POLICY$（neutral = 清除）
hd_party_set_policy_effect = {
	save_scope_as = hd_party_court
	remove_variable = hd_party_$G$_policy
	save_temporary_scope_value_as = { name = hd_party_new_policy value = flag:$POLICY$ }
	if = {
		limit = { NOT = { scope:hd_party_new_policy = flag:neutral } }
		set_variable = { name = hd_party_$G$_policy value = flag:$POLICY$ }
		set_variable = { name = hd_party_$G$_policy_cd days = hd_party_policy_cd_days }
	}
	hd_party_refresh_policy_cost_effect = yes
	set_variable = { name = hd_party_$G$_satisfaction value = hd_party_satisfaction_$G$_value }
	hd_party_apply_member_effects_effect = { G = $G$ }
	# 天朝循环·时代特色：天子查禁/抑制朋党 → 诱因"打压朋党"（C2）
	if = {
		limit = {
			has_title = title:h_china
			OR = {
				scope:hd_party_new_policy = flag:ban
				scope:hd_party_new_policy = flag:restrict
			}
		}
		hd_dc_kit_fire_effect = { CATALYST = catalyst_hd_suppress_party ACTOR = scope:hd_party_court }
	}
}

# Scope：君主（scope:hd_party_court）。对 $G$ 党要求效忠的结算（花费已扣）
# 2026-10-09 U11：改为 random_list，选项提示同时显示成败两种结果及几率（原 random + if 在预览时只显示失败一支），结果以 toast 告知
hd_party_loyalty_resolve_effect = {
	set_variable = { name = hd_party_$G$_loyalty_cd days = hd_party_loyalty_cd_days }
	random_list = {
		0 = {
			modifier = { add = hd_party_loyalty_chance_$G$_value }
			desc = hd_party_loyalty_success_tt
			set_local_variable = hd_party_loyalty_ok
		}
		0 = {
			modifier = {
				add = {
					value = 100
					subtract = hd_party_loyalty_chance_$G$_value
				}
			}
			desc = hd_party_loyalty_fail_tt
		}
	}
	hidden_effect = {	# 实际结算（预览时不显示，以免只列出失败一支）
	if = {
		limit = { has_local_variable = hd_party_loyalty_ok }
		hd_party_set_stance_effect = { G = $G$ STANCE = zunwang }
		set_variable = { name = hd_party_$G$_loyalty_lock value = var:hd_party_$G$_leader }
		send_interface_toast = { type = event_toast_effect_good title = hd_party_loyalty_success_tt }
	}
	else = {
		hd_party_set_attitude_effect = { G = $G$ ATTITUDE = oppose }
		set_variable = { name = hd_party_$G$_oppose_lock days = hd_party_loyalty_fail_lock_days }
		send_interface_toast = { type = event_toast_effect_bad title = hd_party_loyalty_fail_tt }
	}
	remove_local_variable = hd_party_loyalty_ok	# AI 一次结算可能连续处理多党，用后即清
	}
}

############################################################
# AI
############################################################
# Scope：AI 君主（scope:hd_party_court）
hd_party_ai_ruler_effect = {
	# 青睐：无青睐或被青睐朋党对抗时，换成满意度最高且不衰微的朋党
	if = {
		limit = {
			NOT = { has_variable = hd_party_favor_cd }
			prestige >= hd_party_favor_prestige_cost
			OR = {
				NOT = { exists = var:hd_party_favored }
''')
for g in G:
    E.append('\t\t\t\tAND = { var:hd_party_favored ?= flag:%s var:hd_party_%s_attitude ?= flag:oppose }\n' % (g, g))
E.append('''			}
		}
		random = {
			chance = 50
			clear_saved_scope = hd_party_ai_pick
''')
# choose best satisfaction: use ordered over values via saved values, sequential compare
E.append('\t\t\tsave_temporary_scope_value_as = { name = hd_party_ai_best value = -1000 }\n')
for g in G:
    E.append('''			if = {
				limit = {
					NOT = { var:hd_party_favored ?= flag:%(g)s }
					NOT = { var:hd_party_%(g)s_attitude ?= flag:oppose }
					NOT = { hd_party_is_weak_trigger = { G = %(g)s } }
					exists = var:hd_party_%(g)s_satisfaction
					var:hd_party_%(g)s_satisfaction > scope:hd_party_ai_best
				}
				save_temporary_scope_value_as = { name = hd_party_ai_best value = var:hd_party_%(g)s_satisfaction }
				save_temporary_scope_value_as = { name = hd_party_ai_pick value = %(i)d }
			}
''' % {'g': g, 'i': G.index(g) + 1})
E.append('\t\t\tif = {\n\t\t\t\tlimit = { exists = scope:hd_party_ai_pick }\n\t\t\t\tadd_prestige = { value = hd_party_favor_prestige_cost multiply = -1 }\n')
for g in G:
    E.append('\t\t\t\tif = { limit = { scope:hd_party_ai_pick = %d } hd_party_set_favored_effect = { G = %s } }\n' % (G.index(g) + 1, g))
E.append('\t\t\t}\n\t\t}\n\t}\n')
for g in G:
    E.append('''	# %(cn)s：政策
	if = {
		limit = { NOT = { has_variable = hd_party_%(g)s_policy_cd } }
		if = {
			limit = {
				var:hd_party_%(g)s_policy ?= flag:restrict
				exists = var:hd_party_%(g)s_oppose_years
				var:hd_party_%(g)s_oppose_years >= 10
			}
			hd_party_set_policy_effect = { G = %(g)s POLICY = ban }
		}
		else_if = {
			limit = {
				NOT = { exists = var:hd_party_%(g)s_policy }
				var:hd_party_%(g)s_attitude ?= flag:oppose
				exists = var:hd_party_%(g)s_share
				var:hd_party_%(g)s_share >= 30
			}
			hd_party_set_policy_effect = { G = %(g)s POLICY = restrict }
		}
		else_if = {
			limit = {
				NOT = { exists = var:hd_party_%(g)s_policy }
				var:hd_party_favored ?= flag:%(g)s
			}
			hd_party_set_policy_effect = { G = %(g)s POLICY = promote }
		}
		else_if = {
			limit = {
				exists = var:hd_party_%(g)s_policy
				NOT = { var:hd_party_%(g)s_attitude ?= flag:oppose }
				NOT = { var:hd_party_favored ?= flag:%(g)s }
			}
			hd_party_set_policy_effect = { G = %(g)s POLICY = neutral }
		}
	}
	# %(cn)s：要求效忠
	if = {
		limit = {
			var:hd_party_%(g)s_attitude ?= flag:oppose
			NOT = { has_variable = hd_party_%(g)s_loyalty_cd }
			NOT = { var:hd_party_%(g)s_stance ?= flag:zunwang }
			exists = var:hd_party_%(g)s_leader
			hd_party_loyalty_chance_%(g)s_value >= 50
		}
		if = {
			limit = {
				government_has_flag = government_has_influence
				influence >= hd_party_loyalty_influence_cost
			}
			change_influence = { value = hd_party_loyalty_influence_cost multiply = -1 }
			hd_party_loyalty_resolve_effect = { G = %(g)s }
		}
		else_if = {
			limit = { legitimacy >= 100 }
			add_legitimacy = { value = hd_party_loyalty_legitimacy_cost multiply = -1 }
			hd_party_loyalty_resolve_effect = { G = %(g)s }
		}
		else_if = {
			limit = { prestige >= hd_party_loyalty_prestige_cost }
			add_prestige = { value = hd_party_loyalty_prestige_cost multiply = -1 }
			hd_party_loyalty_resolve_effect = { G = %(g)s }
		}
	}
''' % {'g': g, 'cn': CN[g]})
E.append('''}

# Scope：君主（scope:hd_party_court）。AI 领袖年度考虑发起立场辩论
hd_party_ai_leader_debate_effect = {
''')
for g in G:
    E.append('''	var:hd_party_%(g)s_leader ?= {
		if = {
			limit = {
				is_ai = yes
				hd_party_can_start_debate_trigger = yes
			}
			hd_party_ai_consider_debate_effect = { G = %(g)s }
		}
	}
''' % {'g': g})
E.append('''}

# Scope：AI 领袖（scope:hd_party_court）。另一立场的权重比当前立场高 30 以上时，25% 发起辩论
hd_party_ai_consider_debate_effect = {
''')
for s in STANCES:
    E.append('\tsave_temporary_scope_value_as = { name = hd_party_w_%s value = hd_party_stance_weight_%s_value }\n' % (s, s))
E.append('\tsave_temporary_scope_value_as = { name = hd_party_w_cur value = 0 }\n')
for s in STANCES:
    E.append('\tif = { limit = { scope:hd_party_court.var:hd_party_$G$_stance ?= flag:%s } save_temporary_scope_value_as = { name = hd_party_w_cur value = scope:hd_party_w_%s } }\n' % (s, s))
E.append('''	save_temporary_scope_value_as = { name = hd_party_w_thr value = { value = scope:hd_party_w_cur add = 30 } }
	if = {
		limit = {
			OR = {
''')
for s in STANCES:
    E.append('\t\t\t\tAND = { NOT = { scope:hd_party_court.var:hd_party_$G$_stance ?= flag:%s } scope:hd_party_w_%s > scope:hd_party_w_thr }\n' % (s, s))
E.append('''			}
		}
		random = {
			chance = 25
			set_variable = { name = hd_party_ai_debate_wish days = 60 }
			ai_attempt_to_host_activity = activity_hd_party_debate
		}
	}
}

''')
w(r'common\scripted_effects\hd_party_effects.txt', ''.join(E))

# =====================================================================================
# MODIFIERS
# =====================================================================================
M = ['# 天朝循环大修·朋党：modifier（由 docs/tools/gen_party_effects.py 生成，勿手改）\n\n']
ATT = {
 'hanmen': [('county_opinion_add', 5)],
 'shizu': [('domain_tax_mult', 0.1), ('character_capital_county_monthly_development_growth_add', 0.1),
           ('character_capital_county_monthly_control_add', 0.1), ('monthly_prestige_gain_mult', 0.1), ('legitimacy_gain_mult', 0.1)],
 'wuxun': [('levy_size', 0.15), ('levy_reinforcement_rate', 0.2), ('men_at_arms_limit', 1), ('men_at_arms_maintenance', -0.1)],
 'huanguan': [('monthly_influence_mult', 0.15), ('dread_baseline_add', 10), ('owned_hostile_scheme_success_chance_add', 10)],
 'waiqi': [('direct_vassal_opinion', 5), ('courtier_opinion', 5)],
}
def fnum(v):
    if isinstance(v, int): return str(v)
    return ('%.3f' % v).rstrip('0').rstrip('.')
for g in G:
    for a in ['support', 'oppose']:
        M.append('hd_party_attitude_%s_%s_modifier = {\n\ticon = %s\n' % (g, a, 'social_positive' if a == 'support' else 'social_negative'))
        for k, v in ATT[g]:
            if a == 'oppose':
                v = -v * 1.5
                if k == 'men_at_arms_limit': v = -2
            M.append('\t%s = %s\n' % (k, fnum(v)))
        M.append('}\n')
# policy (members)
POL = {'ban': (-0.5, -0.3, -0.3), 'restrict': (-0.2, -0.1, -0.1), 'promote': (0.2, 0.1, 0.1)}
for p, (inf, pre, leg) in POL.items():
    M.append('hd_party_policy_%s_modifier = {\n\ticon = %s\n\tmonthly_influence_mult = %s\n\tmonthly_prestige_gain_mult = %s\n\tlegitimacy_gain_mult = %s\n}\n' %
             (p, 'social_positive' if p == 'promote' else 'social_negative', fnum(inf), fnum(pre), fnum(leg)))
for g in G:
    M.append('hd_party_policy_cost_%s_inf_low_modifier = {\n\ticon = social_negative\n\tmonthly_influence = -1\n}\n' % g)
    M.append('hd_party_policy_cost_%s_inf_high_modifier = {\n\ticon = social_negative\n\tmonthly_influence = -3\n}\n' % g)
    M.append('hd_party_policy_cost_%s_pre_low_modifier = {\n\ticon = social_negative\n\tmonthly_prestige = -2\n}\n' % g)
    M.append('hd_party_policy_cost_%s_pre_high_modifier = {\n\ticon = social_negative\n\tmonthly_prestige = -5\n}\n' % g)
M.append('''hd_party_stance_zunwang_modifier = {
	icon = social_positive
	opinion_of_liege = 15
}
hd_party_debate_disgrace_modifier = {
	icon = social_negative
	monthly_prestige_gain_mult = -0.1
}
hd_party_dominant_modifier = {
	icon = social_negative
	legitimacy_gain_mult = -0.1
}
hd_party_chain_huanguan_power_modifier = {
	icon = social_positive
	monthly_influence_mult = 0.2
}
hd_party_chain_shizu_land_member_modifier = {
	icon = county_modifier_development_positive
	domicile_monthly_gold_mult = 0.2
}
hd_party_chain_shizu_land_ruler_modifier = {
	icon = county_modifier_opinion_negative
	county_opinion_add = -5
}
hd_party_chain_wuxun_border_member_modifier = {
	icon = martial_positive
	men_at_arms_cap = 1
}
hd_party_chain_wuxun_border_ruler_modifier = {
	icon = county_modifier_control_negative
	monthly_county_control_growth_factor = -0.1
}
hd_party_chain_wuxun_arrogant_modifier = {
	icon = martial_negative
	dread_baseline_add = -10
}
''')
# favor copies from situation file
sit = open(os.path.join(MOD, r'common\situation\situations\z_kuzhu_modified_dynastic_cycle.txt'), encoding='utf-8-sig').read().replace('\r\n', '\n')
def block_end(s, i):
    d = 0; j = i
    while j < len(s):
        c = s[j]
        if c == '#':
            k = s.find('\n', j); j = len(s) if k < 0 else k; continue
        if c == '{': d += 1
        elif c == '}':
            d -= 1
            if d == 0: return j + 1
        j += 1
for p in PHASES:
    m = re.search(r'\n\t\tsituation_dynastic_cycle_phase_%s = \{' % p, sit)
    pb = sit[m.start(): block_end(sit, sit.index('{', m.start()))]
    cm = re.search(r'dynastic_cycle_character_effects = \{', pb)
    ce = pb[cm.start(): block_end(pb, pb.index('{', cm.start()))]
    for g in G:
        gm = re.search(r'\n\t+%s = \{' % KEY[g], ce)
        body = ''
        if gm:
            gb = ce[gm.start(): block_end(ce, ce.index('{', gm.start()))]
            for sub in ['character_modifier', 'county_modifier']:
                sm = re.search(sub + r' = \{', gb)
                if sm:
                    sb = gb[sm.end(): block_end(gb, gb.index('{', sm.start())) - 1]
                    for line in sb.split('\n'):
                        # 天朝循环·时代特色：gen_era_outlets.py 给乱世各组注入的 ai_war_chance（注释 "# A1"）不属于组效果，
                        # 不复制给青睐君主：纯注入行跳过；与原值合并的行（"# A1：原 X +4"）还原为原值 X
                        a1 = re.search(r'ai_war_chance = \S+ # A1(?:：原 (\S+) \+\d+)?', line)
                        if a1:
                            if not a1.group(1):
                                continue
                            line = 'ai_war_chance = %s' % a1.group(1)
                        line = re.sub(r'#.*', '', line).strip()
                        if line:
                            body += '\t' + line + '\n'
        M.append('hd_party_favor_%s_%s_modifier = {\n\ticon = social_positive\n%s}\n' % (g, p, body))
w(r'common\modifiers\hd_party_modifiers.txt', ''.join(M))

# =====================================================================================
# OPINION MODIFIERS
# =====================================================================================
O = '''# 天朝循环大修·朋党：好感 modifier
hd_party_hostile_opinion = {
	opinion = -15
	stacking = no
}
hd_party_coop_opinion = {
	opinion = 10
	stacking = no
}
# 天朝循环·时代特色：进取期对立减半 / 合作加倍；党争内耗对立加倍
hd_party_hostile_half_opinion = {
	opinion = -8
	stacking = no
}
hd_party_hostile_double_opinion = {
	opinion = -30
	stacking = no
}
hd_party_coop_double_opinion = {
	opinion = 20
	stacking = no
}
hd_party_policy_ban_opinion = {
	opinion = -30
	stacking = no
}
hd_party_policy_restrict_opinion = {
	opinion = -10
	stacking = no
}
hd_party_policy_promote_opinion = {
	opinion = 10
	stacking = no
}
hd_party_favored_opinion = {
	opinion = 10
	stacking = no
}
hd_party_disgraced_opinion = {
	opinion = -30
	decaying = yes
	years = 10
	stacking = no
}
hd_party_debate_support_opinion = {
	opinion = 10
	years = 5
	stacking = no
}
hd_party_debate_disgrace_opinion = {
	opinion = -15
	years = 5
	stacking = no
}
hd_party_chain_refused_opinion = {
	opinion = -20
	decaying = yes
	years = 5
	stacking = no
}
'''
w(r'common\opinion_modifiers\hd_party_opinions.txt', O)
print('effects/modifiers ok')
