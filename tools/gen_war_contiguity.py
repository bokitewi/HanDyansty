# -*- coding: utf-8 -*-
"""生成 common/scripted_effects/zz_hd_war_contiguity_effects.txt（剧本史实战争连通目标筛选）。
用法：python gen_war_contiguity.py <mod 根目录>"""
import sys

N = 50  # start_war 最多带的目标头衔数

HEAD = r'''# 剧本史实战争「连通目标」筛选（boki 10-18：所有宣称头衔必须与本土相连，不准有飞地）。
# 本文件由 tools/gen_war_contiguity.py 生成，改动请改生成器。
#
# 用法：
#   hd_wct_add_input_effect = { TARGET = title:xxx }   # 可多次，加入原定目标（州/郡/县均可）
#   hd_wct_start_war_effect = { CB = xxx_cb ATTACKER = <角色> DEFENDER = <角色> }
#   结束后由调用方 hd_wct_clear_input_effect = yes 清空输入（218 封臣宣战不成要改由宗主再宣一次，所以不在这里清）。
#
# 规则（boki 10-18 拍板）：
#   1 候选县 = 原定目标法理下、由守方或其封臣持有的县。
#   2 从「与攻方最高领主国土接壤」的候选县出发，只经候选县向外连通，连得到的才算。
#   3 某个原定目标的候选县全部连得到 → 原头衔照用（州/郡名、战争名不变）；
#     否则拆开：整郡连得到的用该郡，其余只取连得到的县。
#   4 一个都连不到 → 改为守方所有与攻方接壤的郡，按 2、3 再筛一遍。
#   5 仍为空（两国根本不接壤）→ 沿用原定目标并写日志 HD_WCT NO_BORDER。
# 中间结果都放全局变量表（hd_wct_*），用完即清。

hd_wct_add_input_effect = {
	if = {
		limit = { NOT = { is_target_in_global_variable_list = { name = hd_wct_in target = $TARGET$ } } }
		add_to_global_variable_list = { name = hd_wct_in target = $TARGET$ }
	}
}

hd_wct_clear_input_effect = {
	clear_global_variable_list = hd_wct_in
}

# 由 hd_wct_in 算出 hd_wct_out（规则 1~3）
hd_wct_build_effect = {
	clear_global_variable_list = hd_wct_cand
	clear_global_variable_list = hd_wct_reach
	clear_global_variable_list = hd_wct_out
	# 1 候选县
	every_in_global_list = {
		variable = hd_wct_in
		every_in_de_jure_hierarchy = {
			limit = {
				tier = tier_county
				hd_wct_def_held_trigger = yes
				NOT = { is_target_in_global_variable_list = { name = hd_wct_cand target = this } }
			}
			add_to_global_variable_list = { name = hd_wct_cand target = this }
		}
	}
	# 2 起点：与攻方接壤的候选县
	every_in_global_list = {
		variable = hd_wct_cand
		limit = { hd_wct_borders_att_trigger = yes }
		add_to_global_variable_list = { name = hd_wct_reach target = this }
	}
	# 2 只经候选县向外连通
	while = {
		limit = {
			any_in_global_list = {
				variable = hd_wct_cand
				NOT = { is_target_in_global_variable_list = { name = hd_wct_reach target = this } }
				any_neighboring_county = { is_target_in_global_variable_list = { name = hd_wct_reach target = this } }
			}
		}
		every_in_global_list = {
			variable = hd_wct_cand
			limit = {
				NOT = { is_target_in_global_variable_list = { name = hd_wct_reach target = this } }
				any_neighboring_county = { is_target_in_global_variable_list = { name = hd_wct_reach target = this } }
			}
			add_to_global_variable_list = { name = hd_wct_reach target = this }
		}
	}
	# 3 定目标
	every_in_global_list = {
		variable = hd_wct_in
		if = {
			limit = {
				any_in_de_jure_hierarchy = {
					tier = tier_county
					is_target_in_global_variable_list = { name = hd_wct_reach target = this }
				}
				NOT = {
					any_in_de_jure_hierarchy = {
						tier = tier_county
						is_target_in_global_variable_list = { name = hd_wct_cand target = this }
						NOT = { is_target_in_global_variable_list = { name = hd_wct_reach target = this } }
					}
				}
			}
			hd_wct_add_out_effect = yes
		}
		else = {
			every_in_de_jure_hierarchy = {
				limit = { tier = tier_duchy }
				if = {
					limit = {
						any_in_de_jure_hierarchy = {
							tier = tier_county
							is_target_in_global_variable_list = { name = hd_wct_reach target = this }
						}
						NOT = {
							any_in_de_jure_hierarchy = {
								tier = tier_county
								is_target_in_global_variable_list = { name = hd_wct_cand target = this }
								NOT = { is_target_in_global_variable_list = { name = hd_wct_reach target = this } }
							}
						}
					}
					hd_wct_add_out_effect = yes
				}
				else = {
					every_in_de_jure_hierarchy = {
						limit = {
							tier = tier_county
							is_target_in_global_variable_list = { name = hd_wct_reach target = this }
						}
						hd_wct_add_out_effect = yes
					}
				}
			}
		}
	}
}

# Scope：头衔
hd_wct_add_out_effect = {
	if = {
		limit = { NOT = { is_target_in_global_variable_list = { name = hd_wct_out target = this } } }
		add_to_global_variable_list = { name = hd_wct_out target = this }
	}
}

hd_wct_start_war_effect = {
	$ATTACKER$ = {
		save_scope_as = hd_wct_me
		top_liege = { save_scope_as = hd_wct_att }
	}
	$DEFENDER$ = { save_scope_as = hd_wct_def }
	hd_wct_build_effect = yes
	# 4 一个都连不到：改为守方所有与攻方接壤的郡
	if = {
		limit = { NOT = { any_in_global_list = { variable = hd_wct_out always = yes } } }
		clear_global_variable_list = hd_wct_orig
		every_in_global_list = {
			variable = hd_wct_in
			add_to_global_variable_list = { name = hd_wct_orig target = this }
		}
		clear_global_variable_list = hd_wct_in
		scope:hd_wct_def = {
			every_sub_realm_county = {
				limit = { hd_wct_borders_att_trigger = yes }
				duchy ?= {
					if = {
						limit = { NOT = { is_target_in_global_variable_list = { name = hd_wct_in target = this } } }
						add_to_global_variable_list = { name = hd_wct_in target = this }
					}
				}
			}
		}
		hd_wct_build_effect = yes
		debug_log = "HD_WCT TARGET_NOT_CONTIGUOUS -> BORDER_DUCHIES"
		# 5 两国不接壤：沿用原定目标
		if = {
			limit = { NOT = { any_in_global_list = { variable = hd_wct_out always = yes } } }
			every_in_global_list = {
				variable = hd_wct_orig
				add_to_global_variable_list = { name = hd_wct_out target = this }
			}
			debug_log = "HD_WCT NO_BORDER -> ORIGINAL_TARGETS"
		}
		# 恢复输入表，供封臣宣战不成时宗主再宣一次
		clear_global_variable_list = hd_wct_in
		every_in_global_list = {
			variable = hd_wct_orig
			add_to_global_variable_list = { name = hd_wct_in target = this }
		}
		clear_global_variable_list = hd_wct_orig
	}
	hd_wct_assign_effect = yes
	scope:hd_wct_me = {
		hd_wct_declare_effect = { CB = $CB$ }
	}
	clear_global_variable_list = hd_wct_cand
	clear_global_variable_list = hd_wct_reach
	clear_global_variable_list = hd_wct_out
	clear_global_variable_list = hd_wct_used
}

'''

TRIG = r'''# 剧本史实战争连通目标筛选用触发器（由 tools/gen_war_contiguity.py 生成；说明见 common/scripted_effects/zz_hd_war_contiguity_effects.txt）

# 守方（scope:hd_wct_def）或其封臣持有的县。Scope：县头衔
hd_wct_def_held_trigger = {
	holder ?= {
		OR = {
			this = scope:hd_wct_def
			target_is_liege_or_above = scope:hd_wct_def
		}
	}
}

# 与攻方最高领主（scope:hd_wct_att）国土接壤。Scope：县头衔
hd_wct_borders_att_trigger = {
	any_neighboring_county = {
		holder ?= { target_is_same_character_or_above = scope:hd_wct_att }
	}
}
'''

VAL = r'''# 剧本史实战争连通目标筛选用（由 tools/gen_war_contiguity.py 生成）
# 头衔等级，供排序：州、郡在前，主目标（战争名里的 TITLE）尽量取大头衔
hd_wct_tier_value = {
	value = 0
	if = { limit = { tier = tier_empire } add = 4 }
	else_if = { limit = { tier = tier_kingdom } add = 3 }
	else_if = { limit = { tier = tier_duchy } add = 2 }
	else_if = { limit = { tier = tier_county } add = 1 }
}
'''

def gen():
    out = [HEAD]
    # assign
    a = ['# 把 hd_wct_out 依次存为 scope:hd_wct_t1 ~ t%d（先清掉上一次留下的）' % N, 'hd_wct_assign_effect = {', '\tclear_global_variable_list = hd_wct_used']
    for k in range(1, N + 1):
        a.append('\tclear_saved_scope = hd_wct_t%d' % k)
    for k in range(1, N + 1):
        a += ['\tordered_in_global_list = {',
              '\t\tvariable = hd_wct_out',
              '\t\tlimit = { NOT = { is_target_in_global_variable_list = { name = hd_wct_used target = this } } }',
              '\t\torder_by = hd_wct_tier_value',
              '\t\tsave_scope_as = hd_wct_t%d' % k,
              '\t\tadd_to_global_variable_list = { name = hd_wct_used target = this }',
              '\t}']
    a += ['\tif = {',
          '\t\tlimit = { any_in_global_list = { variable = hd_wct_out NOT = { is_target_in_global_variable_list = { name = hd_wct_used target = this } } } }',
          '\t\tdebug_log = "HD_WCT TOO_MANY_TARGETS (>%d), REST DROPPED"' % N,
          '\t}', '}', '']
    out.append('\n'.join(a))
    # declare
    d = ['# Scope：宣战人。按目标个数选分支（原版 diarchy_events 同法）', 'hd_wct_declare_effect = {']
    for k in range(N, 0, -1):
        kw = 'if' if k == N else 'else_if'
        d.append('\t%s = {' % kw)
        d.append('\t\tlimit = { exists = scope:hd_wct_t%d }' % k)
        d.append('\t\tstart_war = {')
        d.append('\t\t\tcb = $CB$')
        d.append('\t\t\ttarget = scope:hd_wct_def')
        for j in range(1, k + 1):
            d.append('\t\t\ttarget_title = scope:hd_wct_t%d' % j)
        d.append('\t\t}')
        d.append('\t}')
    d += ['\telse = { debug_log = "HD_WCT NO_TARGET $CB$" }', '}', '']
    out.append('\n'.join(d))
    return '\n'.join(out)

if __name__ == '__main__':
    import os
    root = sys.argv[1]
    for rel, txt in (('common/scripted_effects/zz_hd_war_contiguity_effects.txt', gen()),
                     ('common/scripted_triggers/zz_hd_war_contiguity_triggers.txt', TRIG),
                     ('common/script_values/zz_hd_war_contiguity_values.txt', VAL)):
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8-sig', newline='\n') as f:
            f.write(txt)
