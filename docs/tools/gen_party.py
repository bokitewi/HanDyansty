# -*- coding: utf-8 -*-
# 生成朋党系统核心脚本：values / triggers / effects / modifiers / opinion modifiers
import re, os
MOD = r"E:\documents\Paradox Interactive\Crusader Kings III\mod\HanDyansty"
G = ['huanguan', 'waiqi', 'wuxun', 'shizu', 'hanmen']
KEY = {'huanguan': 'undecided_movement', 'waiqi': 'pro_hegemon_movement', 'wuxun': 'expansion_movement',
       'shizu': 'conservative_movement', 'hanmen': 'advancement_movement'}
FLAG = {'huanguan': 'undecided', 'waiqi': 'pro_hegemon', 'wuxun': 'expansion', 'shizu': 'conservative', 'hanmen': 'advancement'}
CN = {'huanguan': '宦官', 'waiqi': '外戚', 'wuxun': '武勋', 'shizu': '世族', 'hanmen': '寒门'}
STANCES = ['zunwang', 'kaituo', 'jinqu', 'shoujiu', 'zhongli']
HOSTILE_PAIRS = [('jinqu', 'shoujiu'), ('kaituo', 'shoujiu')]
COOP_PAIRS = [('jinqu', 'kaituo'), ('zhongli', 'shoujiu')]

def w(path, text):
    p = os.path.join(MOD, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w', encoding='utf-8-sig', newline='\r\n').write(text.replace('\r\n', '\n'))

def grp(g):
    return 'situation:dynastic_cycle.situation_participant_group:%s' % KEY[g]

# =====================================================================================
# TRIGGERS
# =====================================================================================
T = []
T.append('''# 天朝循环大修·朋党：通用判定（由 docs/tools/gen_party.py 生成，勿手改）
# Scope 约定：除注明外，均在"朝廷君主"（court ruler）角色 scope 下使用。
# 朋党数据统一存放在君主身上：var:hd_party_<组>_*（组 = huanguan/waiqi/wuxun/shizu/hanmen）

# Scope：君主。该朝廷已初始化朋党数据
hd_party_court_initialized_trigger = {
	has_variable = hd_party_court
}

# Scope：君主。$G$ 党势力衰微（占比低于阈值）
hd_party_is_weak_trigger = {
	exists = var:hd_party_$G$_share
	var:hd_party_$G$_share < hd_party_weak_share_value
}
''')
# hostile / coop triggers (A,B are group codes)
def stance_is(g, s): return 'var:hd_party_%s_stance ?= flag:%s' % (g, s)
T.append('''# Scope：君主。$A$ 党与 $B$ 党立场对立
# 对立：进取–守旧、开拓–守旧、尊王–对抗君主的朋党
hd_party_hostile_trigger = {
	OR = {
		AND = { var:hd_party_$A$_stance ?= flag:jinqu var:hd_party_$B$_stance ?= flag:shoujiu }
		AND = { var:hd_party_$A$_stance ?= flag:shoujiu var:hd_party_$B$_stance ?= flag:jinqu }
		AND = { var:hd_party_$A$_stance ?= flag:kaituo var:hd_party_$B$_stance ?= flag:shoujiu }
		AND = { var:hd_party_$A$_stance ?= flag:shoujiu var:hd_party_$B$_stance ?= flag:kaituo }
		AND = { var:hd_party_$A$_stance ?= flag:zunwang var:hd_party_$B$_attitude ?= flag:oppose }
		AND = { var:hd_party_$B$_stance ?= flag:zunwang var:hd_party_$A$_attitude ?= flag:oppose }
	}
}

# Scope：君主。$A$ 党与 $B$ 党立场合作
# 合作：进取–开拓、中立–守旧、尊王–拥护君主的朋党
hd_party_coop_trigger = {
	OR = {
		AND = { var:hd_party_$A$_stance ?= flag:jinqu var:hd_party_$B$_stance ?= flag:kaituo }
		AND = { var:hd_party_$A$_stance ?= flag:kaituo var:hd_party_$B$_stance ?= flag:jinqu }
		AND = { var:hd_party_$A$_stance ?= flag:zhongli var:hd_party_$B$_stance ?= flag:shoujiu }
		AND = { var:hd_party_$A$_stance ?= flag:shoujiu var:hd_party_$B$_stance ?= flag:zhongli }
		AND = { var:hd_party_$A$_stance ?= flag:zunwang var:hd_party_$B$_attitude ?= flag:support }
		AND = { var:hd_party_$B$_stance ?= flag:zunwang var:hd_party_$A$_attitude ?= flag:support }
	}
}

# Scope：君主。被青睐的朋党立场与 $G$ 党对立
hd_party_favored_hostile_to_trigger = {
	OR = {
''')
for x in G:
    T.append('\t\tAND = { var:hd_party_favored ?= flag:%s hd_party_hostile_trigger = { A = %s B = $G$ } }\n' % (x, x))
T.append('''	}
}

# Scope：君主。被青睐的朋党立场为 $STANCE$
hd_party_favored_stance_is_trigger = {
	OR = {
''')
for x in G:
    T.append('\t\tAND = { var:hd_party_favored ?= flag:%s var:hd_party_%s_stance ?= flag:$STANCE$ }\n' % (x, x))
T.append('''	}
}

# Scope：角色。本人是某朝廷朋党的成员，且所属朋党立场为 $STANCE$（成员变量每年刷新，400 天过期）
hd_party_member_stance_is_trigger = {
	var:hd_party_my_stance ?= flag:$STANCE$
}

# Scope：角色。本人所属朋党为 $G$
hd_party_member_group_is_trigger = {
	var:hd_party_my_group ?= flag:$G$
}

# Scope：角色。文官：持实职官位且不持武官军衔
hd_party_is_civil_official_trigger = {
	WJ_has_substantive_office_trigger = yes
	WJ_mt_military_person = no
	WJ_mr_has_rank = no
}

# Scope：角色。武官：持武官军衔或为军事人员
hd_party_is_military_official_trigger = {
	OR = {
		WJ_mt_military_person = yes
		WJ_mr_has_rank = yes
	}
}

# Scope：角色。是本朝廷 $G$ 党的领袖或前三名
hd_party_is_top_of_trigger = {
	exists = var:hd_party_my_court
	var:hd_party_my_group ?= flag:$G$
	var:hd_party_my_court = {
		is_target_in_variable_list = { name = hd_party_$G$_top target = prev }
	}
}

# Scope：角色。可以发起立场辩论（领袖或前三名，未被禁）
hd_party_can_start_debate_trigger = {
	is_adult = yes
	is_imprisoned = no
	NOT = { has_variable = hd_party_debate_cd }
	exists = var:hd_party_my_court
	OR = {
''')
for g in G:
    T.append('''		AND = {
			var:hd_party_my_group ?= flag:%(g)s
			var:hd_party_my_court = {
				is_target_in_variable_list = { name = hd_party_%(g)s_top target = prev }
				NOT = { has_variable = hd_party_%(g)s_debate_lock }
				NOT = { has_variable = hd_party_%(g)s_loyalty_lock }
				NOT = { has_variable = hd_party_%(g)s_debating }
				NOT = { hd_party_is_weak_trigger = { G = %(g)s } }
			}
		}
''' % {'g': g})
T.append('''	}
}

# Scope：角色。玩家担任朋党领袖
hd_party_is_player_leader_trigger = {
	is_ai = no
	exists = var:hd_party_my_court
	OR = {
''')
for g in G:
    T.append('\t\tAND = { var:hd_party_my_group ?= flag:%s var:hd_party_my_court.var:hd_party_%s_leader ?= this }\n' % (g, g))
T.append('''	}
}

# Scope：角色。可以使用"投身乱世"（斗争期，外戚/武勋/寒门/世族的无地成年人）
hd_party_can_join_chaos_trigger = {
	hd_cycle_phase_is_struggle_trigger = yes
	is_landed = no
	is_adult = yes
	is_imprisoned = no
	OR = {
		hd_party_member_group_is_trigger = { G = waiqi }
		hd_party_member_group_is_trigger = { G = wuxun }
		hd_party_member_group_is_trigger = { G = hanmen }
		hd_party_member_group_is_trigger = { G = shizu }
	}
}

# Scope：角色。是 $COURT$ 朝廷中被"查禁"的朋党成员
hd_party_banned_member_of_trigger = {
	var:hd_party_my_court ?= $COURT$
	OR = {
		AND = { var:hd_party_my_group ?= flag:huanguan var:hd_party_my_court.var:hd_party_huanguan_policy ?= flag:ban }
		AND = { var:hd_party_my_group ?= flag:waiqi var:hd_party_my_court.var:hd_party_waiqi_policy ?= flag:ban }
		AND = { var:hd_party_my_group ?= flag:wuxun var:hd_party_my_court.var:hd_party_wuxun_policy ?= flag:ban }
		AND = { var:hd_party_my_group ?= flag:shizu var:hd_party_my_court.var:hd_party_shizu_policy ?= flag:ban }
		AND = { var:hd_party_my_group ?= flag:hanmen var:hd_party_my_court.var:hd_party_hanmen_policy ?= flag:ban }
	}
}

# Scope：角色。是 $COURT$ 朝廷中尊王立场的朋党成员
hd_party_zunwang_member_of_trigger = {
	var:hd_party_my_court ?= $COURT$
	var:hd_party_my_stance ?= flag:zunwang
}

# Scope：角色。所在朝廷君主身上有 $MODIFIER$（用于拥护/对抗的钩子；独立统治者看自己）
hd_party_court_has_modifier_trigger = {
	OR = {
		has_character_modifier = $MODIFIER$
		var:hd_party_my_court ?= { has_character_modifier = $MODIFIER$ }
		top_liege ?= { has_character_modifier = $MODIFIER$ }
	}
}

# Scope：角色。本人所属朋党正被所在朝廷青睐
hd_party_member_favored_trigger = {
	OR = {
		AND = { var:hd_party_my_group ?= flag:huanguan var:hd_party_my_court.var:hd_party_favored ?= flag:huanguan }
		AND = { var:hd_party_my_group ?= flag:waiqi var:hd_party_my_court.var:hd_party_favored ?= flag:waiqi }
		AND = { var:hd_party_my_group ?= flag:wuxun var:hd_party_my_court.var:hd_party_favored ?= flag:wuxun }
		AND = { var:hd_party_my_group ?= flag:shizu var:hd_party_my_court.var:hd_party_favored ?= flag:shizu }
		AND = { var:hd_party_my_group ?= flag:hanmen var:hd_party_my_court.var:hd_party_favored ?= flag:hanmen }
	}
}

# Scope：角色。本人所属朋党在所在朝廷的政策为 $POLICY$
hd_party_member_policy_is_trigger = {
	OR = {
		AND = { var:hd_party_my_group ?= flag:huanguan var:hd_party_my_court.var:hd_party_huanguan_policy ?= flag:$POLICY$ }
		AND = { var:hd_party_my_group ?= flag:waiqi var:hd_party_my_court.var:hd_party_waiqi_policy ?= flag:$POLICY$ }
		AND = { var:hd_party_my_group ?= flag:wuxun var:hd_party_my_court.var:hd_party_wuxun_policy ?= flag:$POLICY$ }
		AND = { var:hd_party_my_group ?= flag:shizu var:hd_party_my_court.var:hd_party_shizu_policy ?= flag:$POLICY$ }
		AND = { var:hd_party_my_group ?= flag:hanmen var:hd_party_my_court.var:hd_party_hanmen_policy ?= flag:$POLICY$ }
	}
}

# Scope：角色。是 $COURT$ 朝廷任一朋党的领袖
hd_party_is_any_leader_of_court_trigger = {
	OR = {
		$COURT$.var:hd_party_huanguan_leader ?= this
		$COURT$.var:hd_party_waiqi_leader ?= this
		$COURT$.var:hd_party_wuxun_leader ?= this
		$COURT$.var:hd_party_shizu_leader ?= this
		$COURT$.var:hd_party_hanmen_leader ?= this
	}
}

# Scope：任意。天子朝廷中两个参与者组（$FIRST$、$SECOND$）的朋党立场对立（供 PAR 党争危机使用）
hd_party_groups_hostile_trigger = {
	exists = title:h_china.holder
	OR = {
		AND = { $FIRST$ = { participant_group_type = undecided_movement } $SECOND$ = { participant_group_type = pro_hegemon_movement } title:h_china.holder = { hd_party_hostile_trigger = { A = huanguan B = waiqi } } }
		AND = { $FIRST$ = { participant_group_type = undecided_movement } $SECOND$ = { participant_group_type = expansion_movement } title:h_china.holder = { hd_party_hostile_trigger = { A = huanguan B = wuxun } } }
		AND = { $FIRST$ = { participant_group_type = undecided_movement } $SECOND$ = { participant_group_type = conservative_movement } title:h_china.holder = { hd_party_hostile_trigger = { A = huanguan B = shizu } } }
		AND = { $FIRST$ = { participant_group_type = undecided_movement } $SECOND$ = { participant_group_type = advancement_movement } title:h_china.holder = { hd_party_hostile_trigger = { A = huanguan B = hanmen } } }
		AND = { $FIRST$ = { participant_group_type = pro_hegemon_movement } $SECOND$ = { participant_group_type = undecided_movement } title:h_china.holder = { hd_party_hostile_trigger = { A = waiqi B = huanguan } } }
		AND = { $FIRST$ = { participant_group_type = pro_hegemon_movement } $SECOND$ = { participant_group_type = expansion_movement } title:h_china.holder = { hd_party_hostile_trigger = { A = waiqi B = wuxun } } }
		AND = { $FIRST$ = { participant_group_type = pro_hegemon_movement } $SECOND$ = { participant_group_type = conservative_movement } title:h_china.holder = { hd_party_hostile_trigger = { A = waiqi B = shizu } } }
		AND = { $FIRST$ = { participant_group_type = pro_hegemon_movement } $SECOND$ = { participant_group_type = advancement_movement } title:h_china.holder = { hd_party_hostile_trigger = { A = waiqi B = hanmen } } }
		AND = { $FIRST$ = { participant_group_type = expansion_movement } $SECOND$ = { participant_group_type = undecided_movement } title:h_china.holder = { hd_party_hostile_trigger = { A = wuxun B = huanguan } } }
		AND = { $FIRST$ = { participant_group_type = expansion_movement } $SECOND$ = { participant_group_type = pro_hegemon_movement } title:h_china.holder = { hd_party_hostile_trigger = { A = wuxun B = waiqi } } }
		AND = { $FIRST$ = { participant_group_type = expansion_movement } $SECOND$ = { participant_group_type = conservative_movement } title:h_china.holder = { hd_party_hostile_trigger = { A = wuxun B = shizu } } }
		AND = { $FIRST$ = { participant_group_type = expansion_movement } $SECOND$ = { participant_group_type = advancement_movement } title:h_china.holder = { hd_party_hostile_trigger = { A = wuxun B = hanmen } } }
		AND = { $FIRST$ = { participant_group_type = conservative_movement } $SECOND$ = { participant_group_type = undecided_movement } title:h_china.holder = { hd_party_hostile_trigger = { A = shizu B = huanguan } } }
		AND = { $FIRST$ = { participant_group_type = conservative_movement } $SECOND$ = { participant_group_type = pro_hegemon_movement } title:h_china.holder = { hd_party_hostile_trigger = { A = shizu B = waiqi } } }
		AND = { $FIRST$ = { participant_group_type = conservative_movement } $SECOND$ = { participant_group_type = expansion_movement } title:h_china.holder = { hd_party_hostile_trigger = { A = shizu B = wuxun } } }
		AND = { $FIRST$ = { participant_group_type = conservative_movement } $SECOND$ = { participant_group_type = advancement_movement } title:h_china.holder = { hd_party_hostile_trigger = { A = shizu B = hanmen } } }
		AND = { $FIRST$ = { participant_group_type = advancement_movement } $SECOND$ = { participant_group_type = undecided_movement } title:h_china.holder = { hd_party_hostile_trigger = { A = hanmen B = huanguan } } }
		AND = { $FIRST$ = { participant_group_type = advancement_movement } $SECOND$ = { participant_group_type = pro_hegemon_movement } title:h_china.holder = { hd_party_hostile_trigger = { A = hanmen B = waiqi } } }
		AND = { $FIRST$ = { participant_group_type = advancement_movement } $SECOND$ = { participant_group_type = expansion_movement } title:h_china.holder = { hd_party_hostile_trigger = { A = hanmen B = wuxun } } }
		AND = { $FIRST$ = { participant_group_type = advancement_movement } $SECOND$ = { participant_group_type = conservative_movement } title:h_china.holder = { hd_party_hostile_trigger = { A = hanmen B = shizu } } }
	}
}

# Scope：无地角色。有政治分量、应作为局势手动参与者
# 持世族头衔 / 宫廷职位 / 议政 / 辅政 / WJ 官职 / 武官军衔
hd_party_manual_participant_valid_trigger = {
	is_alive = yes
	is_adult = yes
	OR = {
		is_councillor = yes
		has_any_court_position = yes
		is_diarch = yes
		any_held_title = { is_noble_family_title = yes }
		WJ_has_official_position_trigger = yes
		WJ_mr_has_rank = yes
	}
}

# Scope：角色。斗争期，本身份可免除"成为冒险者"的文化/信仰门槛
hd_party_adventurer_identity_trigger = {
	hd_cycle_phase_is_struggle_trigger = yes
	OR = {
		var:movement_member ?= flag:pro_hegemon
		var:movement_member ?= flag:expansion
		var:movement_member ?= flag:advancement
		var:movement_member ?= flag:conservative
	}
}
''')
w(r'common\scripted_triggers\hd_party_triggers.txt', ''.join(T))

# =====================================================================================
# VALUES
# =====================================================================================
V = []
V.append('''# 天朝循环大修·朋党：数值（由 docs/tools/gen_party.py 生成，勿手改）
# 常量
hd_party_weak_share_value = 10
hd_party_attitude_enter_value = 50
hd_party_attitude_exit_value = 20
hd_party_favor_prestige_cost = 500
hd_party_favor_cd_days = 3650
hd_party_policy_cd_days = 1825
hd_party_loyalty_cd_days = 1825
hd_party_loyalty_fail_lock_days = 1825
hd_party_loyalty_influence_cost = 300
hd_party_loyalty_legitimacy_cost = 50
hd_party_loyalty_prestige_cost = 1000
hd_party_loyalty_prestige_alt_cost = 300
hd_party_debate_cd_days = 3650
hd_party_debate_lock_days = 3650
hd_party_debate_prestige_cost = 200
hd_party_debate_gold_cost = 50
hd_party_debate_success_threshold = 30
hd_party_convert_prestige_cost = 500
hd_party_convert_legitimacy_cost = 30
hd_party_convert_cd_days = 3650
hd_party_attitude_player_cd_days = 1095
hd_party_chain_chance = 30
hd_party_favored_power_bonus = 350

# Scope：君主。本朝廷五党势力合计
hd_party_total_power_value = {
	value = 0
''')
for g in G:
    V.append('\tif = { limit = { exists = var:hd_party_%s_power } add = var:hd_party_%s_power }\n' % (g, g))
V.append('\tmin = 1\n}\n\n')

SPEC = {
 'hanmen': '''	if = {
		limit = { any_in_list = { variable = hd_party_hanmen_members count >= 3 WJ_has_substantive_office_trigger = yes } }
		add = { value = 15 desc = hd_party_sat_hanmen_office_many }
	}
	else_if = {
		limit = { NOT = { any_in_list = { variable = hd_party_hanmen_members WJ_has_substantive_office_trigger = yes } } }
		add = { value = -15 desc = hd_party_sat_hanmen_office_none }
	}
	if = {
		limit = { has_variable = hd_party_recent_exam }
		add = { value = 15 desc = hd_party_sat_hanmen_exam }
	}
	if = {
		limit = { has_variable = hd_party_famine_flag }
		add = { value = -15 desc = hd_party_sat_hanmen_famine }
	}
''',
 'shizu': '''	if = {
		limit = { any_in_list = { variable = hd_party_shizu_members count >= 3 WJ_has_substantive_office_trigger = yes } }
		add = { value = 15 desc = hd_party_sat_shizu_office_many }
	}
	if = {
		limit = { has_variable = hd_party_recent_revoke_shizu }
		add = { value = -30 desc = hd_party_sat_shizu_revoke }
	}
	if = {
		limit = { hd_party_favored_stance_is_trigger = { STANCE = shoujiu } }
		add = { value = 15 desc = hd_party_sat_shizu_shoujiu }
	}
''',
 'wuxun': '''	if = {
		limit = { has_variable = hd_party_recent_offense_win }
		add = { value = 20 desc = hd_party_sat_wuxun_victory }
	}
	if = {
		limit = {
			is_at_war = no
			NOT = { has_variable = hd_party_recent_war }
		}
		add = { value = -15 desc = hd_party_sat_wuxun_peace }
	}
	if = {
		limit = { any_in_list = { variable = hd_party_wuxun_members count >= 3 WJ_mr_has_rank = yes } }
		add = { value = 15 desc = hd_party_sat_wuxun_ranks }
	}
	if = {
		limit = { hd_party_favored_stance_is_trigger = { STANCE = kaituo } }
		add = { value = 15 desc = hd_party_sat_wuxun_kaituo }
	}
''',
 'huanguan': '''	if = {
		limit = { any_in_list = { variable = hd_party_huanguan_members has_court_position = chief_eunuch_court_position } }
		add = { value = 20 desc = hd_party_sat_huanguan_chief }
	}
	if = {
		limit = { is_adult = no }
		add = { value = 15 desc = hd_party_sat_minor_ruler }
	}
	if = {
		limit = { any_in_list = { variable = hd_party_huanguan_members is_diarch_of_target = prev } }
		add = { value = 25 desc = hd_party_sat_regent }
	}
	if = {
		limit = {
			exists = var:hd_party_huanguan_leader
			opinion = { target = var:hd_party_huanguan_leader value >= 50 }
		}
		add = { value = 10 desc = hd_party_sat_huanguan_favor }
	}
''',
 'waiqi': '''	if = {
		limit = { any_in_list = { variable = hd_party_waiqi_members highest_held_title_tier >= tier_kingdom } }
		add = { value = 20 desc = hd_party_sat_waiqi_kingdom }
	}
	if = {
		limit = {
			any_in_list = {
				variable = hd_party_waiqi_members
				OR = {
					is_councillor_of = prev
					tgp_is_any_minister = yes
				}
			}
		}
		add = { value = 15 desc = hd_party_sat_waiqi_council }
	}
	if = {
		limit = {
			exists = primary_spouse
			primary_heir ?= { mother ?= prev.primary_spouse }
		}
		add = { value = 15 desc = hd_party_sat_waiqi_heir }
	}
	if = {
		limit = { is_adult = no }
		add = { value = 15 desc = hd_party_sat_minor_ruler }
	}
	if = {
		limit = { any_in_list = { variable = hd_party_waiqi_members is_diarch_of_target = prev } }
		add = { value = 20 desc = hd_party_sat_regent }
	}
''',
}
for g in G:
    V.append('''# Scope：君主。%(cn)s党满意度（-100 ~ 100）
hd_party_satisfaction_%(g)s_value = {
	value = 0
	if = {
		limit = { var:hd_party_favored ?= flag:%(g)s }
		add = { value = 30 desc = hd_party_sat_favored }
	}
	if = {
		limit = { hd_party_favored_hostile_to_trigger = { G = %(g)s } }
		add = { value = -15 desc = hd_party_sat_favored_hostile }
	}
	if = {
		limit = { var:hd_party_%(g)s_policy ?= flag:promote }
		add = { value = 25 desc = hd_party_sat_policy_promote }
	}
	else_if = {
		limit = { var:hd_party_%(g)s_policy ?= flag:restrict }
		add = { value = -25 desc = hd_party_sat_policy_restrict }
	}
	else_if = {
		limit = { var:hd_party_%(g)s_policy ?= flag:ban }
		add = { value = -50 desc = hd_party_sat_policy_ban }
	}
	if = {
		limit = { exists = var:hd_party_%(g)s_disgrace }
		add = {
			value = var:hd_party_%(g)s_disgrace
			multiply = -4
			desc = hd_party_sat_disgrace
		}
	}
%(spec)s	if = {
		limit = { exists = var:hd_party_%(g)s_sat_mod }
		add = { value = var:hd_party_%(g)s_sat_mod desc = hd_party_sat_events }
	}
	min = -100
	max = 100
}

# Scope：君主（需 scope:hd_party_court = 君主）。%(cn)s党拥护分
hd_party_attitude_score_%(g)s_value = {
	value = -25
	if = {
		limit = { exists = var:hd_party_%(g)s_satisfaction }
		add = var:hd_party_%(g)s_satisfaction
	}
	if = {
		limit = { exists = var:hd_party_%(g)s_leader }
		add = {
			value = "var:hd_party_%(g)s_leader.opinion(scope:hd_party_court)"
			multiply = 0.5
		}
		if = {
			limit = { var:hd_party_%(g)s_leader = { has_dread_level_towards = { target = scope:hd_party_court level >= 1 } } }
			add = 20
		}
		if = {
			limit = { var:hd_party_%(g)s_leader = { is_obedient_to = scope:hd_party_court } }
			add = 30
		}
		if = {
			limit = { var:hd_party_%(g)s_leader = { has_trait = loyal } }
			add = 20
		}
		if = {
			limit = { var:hd_party_%(g)s_leader = { has_trait = disloyal } }
			add = -20
		}
		if = {
			limit = { var:hd_party_%(g)s_leader = { has_trait = deceitful } }
			add = -20
		}
	}
	add = {
		value = legitimacy_level
		multiply = 10
	}
}

# Scope：君主（需 scope:hd_party_court）。对%(cn)s党要求效忠的成功率（%%）
hd_party_loyalty_chance_%(g)s_value = {
	value = 30
	add = {
		value = legitimacy_level
		multiply = 10
	}
	if = {
		limit = { exists = var:hd_party_%(g)s_leader }
		if = {
			limit = { var:hd_party_%(g)s_leader = { has_dread_level_towards = { target = scope:hd_party_court level >= 1 } } }
			add = 20
		}
		if = {
			limit = { var:hd_party_%(g)s_leader = { is_obedient_to = scope:hd_party_court } }
			add = 20
		}
		add = {
			value = "var:hd_party_%(g)s_leader.opinion(scope:hd_party_court)"
			multiply = 0.2
		}
	}
	if = {
		limit = { exists = var:hd_party_%(g)s_satisfaction }
		add = {
			value = var:hd_party_%(g)s_satisfaction
			multiply = 0.3
		}
	}
	if = {
		limit = { exists = var:hd_party_%(g)s_share }
		add = {
			value = var:hd_party_%(g)s_share
			multiply = -0.5
		}
	}
	if = {
		limit = { scope:hd_party_hook_level ?= 2 }
		add = 60
	}
	else_if = {
		limit = { scope:hd_party_hook_level ?= 1 }
		add = 40
	}
	min = 5
	max = 95
}

''' % {'g': g, 'cn': CN[g], 'spec': SPEC[g]})

# stance weights (scope: leader character; scope:hd_party_court = ruler)
STW = {
 'kaituo': [('brave', 30), ('wrathful', 10), ('ambitious', 30), ('zealous', 10), ('callous', 15)],
 'shoujiu': [('gregarious', 10), ('zealous', 30), ('temperate', 15), ('stubborn', 10)],
 'zhongli': [('craven', 30), ('content', 30), ('lazy', 20)],
 'zunwang': [('temperate', 10), ('content', 10), ('zealous', 10), ('loyal', 50), ('chaste', 10), ('craven', 10)],
 'jinqu': [('cynical', 30), ('just', 20), ('diligent', 20)],
}
STANCE_VS = {
 'kaituo': ['belligerent', 'glory_hound', 'minority'],
 'shoujiu': ['barons_and_minor_landholders', 'zealot', 'courtly'],
 'zhongli': ['barons_and_minor_landholders', 'parochial', 'minority'],
 'zunwang': ['zealot', 'courtly'],
 'jinqu': ['zealot', 'glory_hound'],
}
for s in STANCES:
    lines = ['# Scope：领袖角色（需 scope:hd_party_court）。立场"%s"的选择权重' % s, 'hd_party_stance_weight_%s_value = {' % s, '\tvalue = 5']
    for tr, wt in STW[s]:
        lines.append('\tif = { limit = { has_trait = %s } add = %d }' % (tr, wt))
    for vs in STANCE_VS[s]:
        lines.append('\tif = { limit = { has_vassal_stance = %s } add = 30 }' % vs)
    if s == 'zunwang':
        lines.append('\tif = {\n\t\tlimit = { exists = scope:hd_party_court }\n\t\tadd = {\n\t\t\tvalue = "opinion(scope:hd_party_court)"\n\t\t\tmultiply = 0.3\n\t\t}\n\t}\n\telse_if = {\n\t\tlimit = { exists = liege }\n\t\tadd = {\n\t\t\tvalue = "opinion(liege)"\n\t\t\tmultiply = 0.3\n\t\t}\n\t}')
    if s == 'zunwang':
        # 天朝循环·时代特色：天子朝廷进取期，尊王立场权重 ×2（§3.2）
        lines.append('\t# 天朝循环·时代特色：天子朝廷进取期尊王权重 ×2\n\tif = {\n\t\tlimit = {\n\t\t\thd_dc_phase_is_trigger = { PHASE = stability_advancement }\n\t\t\tscope:hd_party_court ?= { has_title = title:h_china }\n\t\t}\n\t\tmultiply = 2\n\t}')
    lines.append('\tmin = 1\n}\n')
    V.append('\n'.join(lines) + '\n')

V.append('''# Scope：辩论活动。拥护方 / 反对方势力合计
hd_party_debate_support_power_value = {
	value = 0
	every_guest_subset = {
		name = hd_debate_support
		limit = { exists = var:movement_power }
		add = var:movement_power
	}
}
hd_party_debate_oppose_power_value = {
	value = 0
	every_guest_subset = {
		name = hd_debate_oppose
		limit = { exists = var:movement_power }
		add = var:movement_power
	}
	# 拂袖而去：反对方势力修正减半
	if = {
		limit = { has_variable = hd_debate_oppose_left }
		multiply = 0.5
	}
}
# Scope：辩论活动。势力修正 = (拥护方 − 反对方) ÷ 双方合计 × 30
hd_party_debate_power_mod_value = {
	value = hd_party_debate_support_power_value
	subtract = hd_party_debate_oppose_power_value
	multiply = 30
	divide = {
		value = hd_party_debate_support_power_value
		add = hd_party_debate_oppose_power_value
		min = 1
	}
}

# Scope：角色。辩论侧栏排序（个人朋党力量）
hd_party_debate_sort_value = {
	value = 0
	if = {
		limit = { exists = var:movement_power }
		add = var:movement_power
	}
}

# Scope：发起"投身乱世"的角色。事件兵数量 = 300 + 军事 × 25，上限 800
hd_party_join_chaos_troops_value = {
	value = martial
	multiply = 25
	add = 300
	max = 800
}
''')
w(r'common\script_values\hd_party_values.txt', ''.join(V))
print('values/triggers ok')
