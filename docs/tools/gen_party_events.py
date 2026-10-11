# -*- coding: utf-8 -*-
# 生成朋党系统事件：hd_party.*（结算、要求效忠、184 开局）与 hd_party_chain.*（青睐事件链）
import os
MOD = r"E:\documents\Paradox Interactive\Crusader Kings III\mod\HanDyansty"
G = ['huanguan', 'waiqi', 'wuxun', 'shizu', 'hanmen']
N = {g: i + 1 for i, g in enumerate(G)}

def w(path, text):
    p = os.path.join(MOD, path)
    open(p, 'w', encoding='utf-8-sig', newline='\r\n').write(text.replace('\r\n', '\n'))

E = ['''# 天朝循环大修·朋党：事件（由 docs/tools/gen_party_events.py 生成，勿手改）
namespace = hd_party

# 朝廷结算（隐藏，君主）
hd_party.0001 = {
	type = character_event
	hidden = yes
	trigger = {
		is_alive = yes
		hd_party_court_ruler_trigger = yes
	}
	immediate = {
		hd_party_court_refresh_effect = yes
	}
}

# 开局初始化（开局 3 天后，任一玩家身上触发）
hd_party.0002 = {
	type = character_event
	hidden = yes
	immediate = {
		hd_party_game_start_effect = yes
	}
}

# 要求效忠（玩家君主）：scope:hd_party_target_group = 参与者组
hd_party.0020 = {
	type = character_event
	title = hd_party.0020.t
	desc = hd_party.0020.desc
	theme = dynastic_cycle
	left_portrait = {
		character = root
		animation = dismissal
	}
	right_portrait = {
		character = scope:hd_party_target_leader
		animation = worry
	}
	immediate = {
		save_scope_as = hd_party_court
		hd_party_save_group_code_effect = { GROUP = scope:hd_party_target_group }
''']
for g in G:
    E.append('\t\tif = { limit = { scope:hd_party_g ?= flag:%s } var:hd_party_%s_leader ?= { save_scope_as = hd_party_target_leader } }\n' % (g, g))
E.append('''	}
	option = { # 影响力
		name = hd_party.0020.a
		trigger = {
			government_has_flag = government_has_influence
			influence >= hd_party_loyalty_influence_cost
		}
		change_influence = {
			value = hd_party_loyalty_influence_cost
			multiply = -1
		}
		hd_party_loyalty_by_code_effect = yes
	}
	option = { # 正统
		name = hd_party.0020.b
		trigger = {
			legitimacy >= hd_party_loyalty_legitimacy_cost
		}
		add_legitimacy = {
			value = hd_party_loyalty_legitimacy_cost
			multiply = -1
		}
		hd_party_loyalty_by_code_effect = yes
	}
	option = { # 威望（非行政政体以威望 300 代替影响力）
		name = hd_party.0020.c
		trigger = {
			NOT = { government_has_flag = government_has_influence }
			prestige >= hd_party_loyalty_prestige_alt_cost
		}
		add_prestige = {
			value = hd_party_loyalty_prestige_alt_cost
			multiply = -1
		}
		hd_party_loyalty_by_code_effect = yes
	}
	option = { # 威望 1000（仅限有影响力的政体；无影响力政体走 c 的威望 300）
		name = hd_party.0020.d
		trigger = {
			government_has_flag = government_has_influence
			prestige >= hd_party_loyalty_prestige_cost
		}
		add_prestige = {
			value = hd_party_loyalty_prestige_cost
			multiply = -1
		}
		hd_party_loyalty_by_code_effect = yes
	}
	option = { # 动用牵制
		name = hd_party.0020.e
		trigger = {
			exists = scope:hd_party_target_leader
			has_usable_hook = scope:hd_party_target_leader
		}
		if = {
			limit = { has_strong_usable_hook = scope:hd_party_target_leader }
			save_scope_value_as = { name = hd_party_hook_level value = 2 }
		}
		else = {
			save_scope_value_as = { name = hd_party_hook_level value = 1 }
		}
		use_hook = scope:hd_party_target_leader
		hd_party_loyalty_by_code_effect = yes
	}
	option = { # 作罢
		name = hd_party.0020.f
	}
}

############################################################
# 184 年史实开局（草案 9.3）
############################################################
# 黄巾起义后解除党锢：寒门政策回到中立（开局约 75 天后）
hd_party.0101 = {
	type = character_event
	title = hd_party.0101.t
	desc = hd_party.0101.desc
	theme = dynastic_cycle
	left_portrait = {
		character = root
		animation = worry
	}
	trigger = {
		has_title = title:h_china
		var:hd_party_hanmen_policy ?= flag:restrict
	}
	immediate = {
		save_scope_as = hd_party_court
	}
	option = {
		name = hd_party.0101.a
		custom_tooltip = hd_party.0101.a.tt
		hd_party_set_policy_effect = { G = hanmen POLICY = neutral }
	}
}

namespace = hd_party_chain
''')

# ---------------------------------------------------------- chain events
# 2026-10-09 文本重写（U11）：满意度/势力变量变化在界面上不可见，各选项加一句叙事提示（hd_party_tt_*，见 gen_party_loc.py）
def resent(x):
    return '\t\tcustom_tooltip = hd_party_tt_%s_resent\n' % x
COMMON_ACCEPT = '''		custom_tooltip = hd_party_tt_%(g)s_pleased
		hd_party_add_var_effect = { NAME = hd_party_%(g)s_sat_mod VALUE = 15 }
		hd_party_add_var_effect = { NAME = hd_party_%(g)s_power_mod VALUE = %(pw)d }
		set_variable = { name = hd_party_%(g)s_chain_stage value = %(s)d }
'''
COMMON_COMP = '''		custom_tooltip = hd_party_tt_%(g)s_soothed
		hd_party_add_var_effect = { NAME = hd_party_%(g)s_sat_mod VALUE = 5 }
		set_variable = { name = hd_party_%(g)s_chain_stage value = %(s)d }
'''
COMMON_REFUSE = '''		custom_tooltip = hd_party_tt_%(g)s_resent
		hd_party_add_var_effect = { NAME = hd_party_%(g)s_sat_mod VALUE = -15 }
		set_variable = hd_party_%(g)s_chain_paused
		var:hd_party_%(g)s_leader ?= { add_opinion = { target = root modifier = hd_party_chain_refused_opinion } }
'''
def others(g, val, skip=()):
    return ''.join('\t\thd_party_add_var_effect = { NAME = hd_party_%s_sat_mod VALUE = %d }\n' % (x, val) for x in G if x != g and x not in skip)
STAGE3_ACCEPT = '''		custom_tooltip = hd_party_tt_%(g)s_dominant
		custom_tooltip = hd_party_tt_others_resent
		hd_party_add_var_effect = { NAME = hd_party_%(g)s_power_mod VALUE = 150 }
		set_variable = { name = hd_party_%(g)s_chain_stage value = 3 }
		add_character_modifier = { modifier = hd_party_dominant_modifier years = 10 }
'''
STAGE3_REFUSE = '''		custom_tooltip = hd_party_tt_%(g)s_resent
		hd_party_add_var_effect = { NAME = hd_party_%(g)s_sat_mod VALUE = -25 }
		set_variable = hd_party_%(g)s_chain_paused
		hd_party_refresh_party_effect = { G = %(g)s }
'''
# helpers
GIVE_COUNTY = '''		trigger = {	# 2026-10-09 C2：无县可赐时改付 200 金，须有足额金钱
			trigger_if = {
				limit = {
					NOT = {
						AND = {
							domain_size >= 3
							any_held_title = {
								tier = tier_county
								NOT = { this = root.capital_county }
							}
						}
					}
				}
				gold >= 200
			}
		}
		random_held_title = {
			limit = {
				tier = tier_county
				NOT = { this = root.capital_county }
			}
			save_scope_as = hd_party_gift_county
		}
		if = {
			limit = {
				exists = scope:hd_party_gift_county
				exists = scope:hd_party_chain_leader
				domain_size >= 3
			}
			create_title_and_vassal_change = {
				type = granted
				save_scope_as = hd_party_change
				add_claim_on_loss = no
			}
			scope:hd_party_gift_county = {
				change_title_holder = {
					holder = scope:hd_party_chain_leader
					change = scope:hd_party_change
				}
			}
			resolve_title_and_vassal_change = scope:hd_party_change
		}
		else_if = {
			limit = { exists = scope:hd_party_chain_leader }
			pay_short_term_gold = { target = scope:hd_party_chain_leader gold = 200 }
		}
'''
def rank(trait):
    return '''		scope:hd_party_chain_leader ?= {
			if = {
				limit = { WJ_mr_has_rank = no }
				add_trait = %s
			}
			else = {
				add_prestige = 300
			}
		}
''' % trait
def temp_office(g, n):
    return '''		ordered_in_list = {
			variable = hd_party_%s_members
			limit = {
				is_alive = yes
				is_landed = no
				is_adult = yes
				WJ_has_official_position_trigger = no
			}
			order_by = prestige
			max = %d
			check_range_bounds = no
			add_character_modifier = { modifier = WJ_temp_official_modifier years = 3 }
		}
''' % (g, n)
COMP_GOLD = '''		trigger = { gold >= 100 }	# 2026-10-09 C2：付 100 金须有足额金钱
		scope:hd_party_chain_leader ?= { save_scope_as = hd_party_chain_target }
		if = {
			limit = { exists = scope:hd_party_chain_target }
			pay_short_term_gold = { target = scope:hd_party_chain_target gold = 100 }
		}
'''
COMP_PRESTIGE = '''		add_prestige = -100
		scope:hd_party_chain_leader ?= { add_prestige = 150 }
'''
SPEC = {
 ('waiqi', 1): (GIVE_COUNTY, COMP_GOLD),
 ('waiqi', 2): (rank('WJ_mr_jiangjun_qian') + resent('wuxun') + '\t\thd_party_add_var_effect = { NAME = hd_party_wuxun_sat_mod VALUE = -10 }\n', COMP_PRESTIGE),
 ('waiqi', 3): ('\t\tdesignate_diarch = scope:hd_party_chain_leader\n' + others('waiqi', -15), None),
 ('huanguan', 1): ('''		if = {
			limit = {
				exists = scope:hd_party_chain_leader
				can_employ_court_position_type = chief_eunuch_court_position
			}
			appoint_court_position = {
				recipient = scope:hd_party_chain_leader
				court_position = chief_eunuch_court_position
			}
		}
''', COMP_GOLD),
 ('huanguan', 2): (rank('WJ_mr_xiaowei_huben') + resent('wuxun') + '\t\thd_party_add_var_effect = { NAME = hd_party_wuxun_sat_mod VALUE = -15 }\n', COMP_PRESTIGE),
 ('huanguan', 3): ('\t\tadd_character_modifier = { modifier = hd_party_chain_huanguan_power_modifier years = 10 }\n'
                   '\t\thd_party_add_var_effect = { NAME = hd_party_hanmen_sat_mod VALUE = -20 }\n\t\thd_party_add_var_effect = { NAME = hd_party_waiqi_sat_mod VALUE = -20 }\n'
                   + others('huanguan', -15, ('hanmen', 'waiqi')), None),
 ('hanmen', 1): ('\t\ttrigger = { gold >= 100 }\n\t\tremove_short_term_gold = 100\n' + temp_office('hanmen', 2), temp_office('hanmen', 1)),  # 2026-10-09 C2：51.a 付 100 金须有足额金钱
 ('hanmen', 2): ('\t\tadd_prestige = 200\n' + resent('huanguan') + '\t\thd_party_add_var_effect = { NAME = hd_party_huanguan_sat_mod VALUE = -15 }\n', COMP_PRESTIGE),
 ('hanmen', 3): ('''		scope:hd_party_chain_leader ?= {
			add_character_modifier = { modifier = WJ_temp_official_modifier years = 5 }
		}
		hd_party_add_var_effect = { NAME = hd_party_shizu_sat_mod VALUE = -20 }
''' + others('hanmen', -15, ('shizu',)), None),
 ('shizu', 1): (temp_office('shizu', 2) + resent('hanmen') + '\t\thd_party_add_var_effect = { NAME = hd_party_hanmen_sat_mod VALUE = -10 }\n', temp_office('shizu', 1)),
 ('shizu', 2): ('''		every_in_list = {
			variable = hd_party_shizu_members
			limit = { is_alive = yes }
			add_character_modifier = { modifier = hd_party_chain_shizu_land_member_modifier years = 10 }
		}
		add_character_modifier = { modifier = hd_party_chain_shizu_land_ruler_modifier years = 10 }
''', ''),  # 2026-10-09 U11："略加约束"不再付给世族领袖 100 金（文案为约束，非赏赐）
 ('shizu', 3): ('\t\thd_party_add_var_effect = { NAME = hd_party_hanmen_sat_mod VALUE = -30 }\n' + others('shizu', -15, ('hanmen',)), None),
 ('wuxun', 1): (rank('WJ_mr_jiangjun_qian'), COMP_GOLD),
 ('wuxun', 2): ('''		every_in_list = {
			variable = hd_party_wuxun_members
			limit = { is_alive = yes }
			add_character_modifier = { modifier = hd_party_chain_wuxun_border_member_modifier years = 10 }
		}
		add_character_modifier = { modifier = hd_party_chain_wuxun_border_ruler_modifier years = 10 }
''', COMP_GOLD),  # 2026-10-09 U11："赐以钱粮"改为付金（原为威望转移）
 ('wuxun', 3): ('\t\tadd_character_modifier = { modifier = hd_party_chain_wuxun_arrogant_modifier years = 10 }\n'
                '\t\thd_party_add_var_effect = { NAME = hd_party_huanguan_sat_mod VALUE = -15 }\n\t\thd_party_add_var_effect = { NAME = hd_party_hanmen_sat_mod VALUE = -15 }\n'
                + others('wuxun', -15, ('huanguan', 'hanmen')), None),
}
for g in G:
    for s in (1, 2, 3):
        eid = 'hd_party_chain.%d%d' % (N[g], s)
        acc, comp = SPEC[(g, s)]
        d = {'g': g, 's': s, 'pw': 50 if s == 1 else 100}
        E.append('''%(eid)s = {
	type = character_event
	title = %(eid)s.t
	desc = %(eid)s.desc
	theme = dynastic_cycle
	left_portrait = {
		character = root
		animation = thinking
	}
	right_portrait = {
		character = scope:hd_party_chain_leader
		animation = personality_bold
	}
	trigger = {
		var:hd_party_favored ?= flag:%(g)s
		exists = var:hd_party_%(g)s_leader
	}
	immediate = {
		save_scope_as = hd_party_court
		var:hd_party_%(g)s_leader = { save_scope_as = hd_party_chain_leader }
	}
''' % {'eid': eid, 'g': g})
        if s < 3:
            E.append('\toption = {\n\t\tname = %s.a\n' % eid + acc + COMMON_ACCEPT % d + '\t}\n')
            E.append('\toption = {\n\t\tname = %s.b\n' % eid + comp + COMMON_COMP % d + '\t}\n')
            E.append('\toption = {\n\t\tname = %s.c\n' % eid + COMMON_REFUSE % d + '\t}\n}\n\n')
        else:
            E.append('\toption = {\n\t\tname = %s.a\n' % eid + acc + STAGE3_ACCEPT % d + '\t}\n')
            E.append('\toption = {\n\t\tname = %s.c\n' % eid + STAGE3_REFUSE % d + '\t}\n}\n\n')
w(r'events\hd_party_events.txt', ''.join(E))
print('events ok')
